# Summary query optimization experiments

The initial `/api/summary` request took about nine seconds. We considered
query changes and build-time aggregates; first we measured the existing queries.

## 1. Identify the expensive work

Added `EXPLAIN QUERY PLAN` and timing around the totals query, including fetching
its result. Added timings around geography and both ranking helpers, then
separated SQL/fetch time from Python result building in geography and point
rankings.

Initial measured stages (milliseconds):

| Stage | Unfiltered | HB_NORTH | LZ_NORTH |
| --- | ---: | ---: | ---: |
| Totals | 2,677 | 1,426 | 1,487 |
| Geography | 2,940 | 2,011 | 1,968 |
| Account rankings | 493 | 412 | 391 |
| Point rankings | 2,944 | 1,915 | 1,817 |
| Combined | 9,055 | 5,764 | 5,664 |

A subsequent run isolated geography SQL at 2,705 ms versus 0.99 ms for Python,
and point-ranking SQL at 2,722 ms versus 0.04 ms for Python. SQL dominated.
Both queries read holdings separately for source and sink contributions.

## 2. Reuse geography's filtered holdings

Changed geography to `WITH holdings AS MATERIALIZED (...)`. This stores the
filtered input temporarily for the statement, allowing both endpoint branches
to reuse it. It does not persist an aggregate between requests.

| Geography SQL, ms | Before | Materialized |
| --- | ---: | ---: |
| Unfiltered | 2,705 | 2,084 |
| HB_NORTH | 1,820 | 1,005 |
| LZ_NORTH | 1,875 | 1,001 |

The plan changed from two base-table reads to one read and two `SCAN holdings`
operations. The initial read still narrowed only by `report_id`.

## 3. Make the point filter selective

The filter must include `source = point OR sink = point`. Instead of relying on
the optimizer to combine indexes for that expression, split it into:

- Source matches.
- `UNION ALL` sink matches, excluding rows whose source also matches.

This preserves self-path counting without duplicate holdings. Existing indexes
now narrowed by `(report_id, source)` and `(report_id, sink)`.

Geography SQL fell to **60 ms for HB_NORTH** and **31 ms for LZ_NORTH**.
Unfiltered geography remained around 2,071 ms.

## 4. Apply the filter rewrite to totals and rankings

Shared the source/sink selection across geography, totals, and both rankings.
Kept the existing materialization choices to isolate the filter change.

| Measured stage, ms | HB_NORTH | LZ_NORTH |
| --- | ---: | ---: |
| Totals | 376 | 332 |
| Geography | 58 | 19 |
| Account rankings | 38 | 13 |
| Point rankings | 83 | 33 |
| Combined | 555 | 396 |

Fixture comparisons matched the original OR-filter results, including both
endpoint directions, self-paths, account/report filters, and an absent point.
The totals plan still showed broad base-index reads in its unique-points subquery.

## 5. Materialize totals' holdings explicitly

Changed totals to `WITH holdings AS MATERIALIZED (...)` too. Its subqueries now
read the temporary holdings result instead of revisiting the base table.

| Measured stage, ms | Unfiltered | HB_NORTH | LZ_NORTH | XLUREP account |
| --- | ---: | ---: | ---: | ---: |
| Totals | 2,766 | 76 | 31 | 3 |
| Geography | 2,084 | 59 | 21 | 3 |
| Account rankings | 476 | 43 | 15 | 1 |
| Point rankings | 2,828 | 81 | 27 | 3 |
| Combined | 8,153 | 258 | 94 | 10 |

Filtered requests improved substantially. Unfiltered totals did not improve
(2,606 ms in the preceding run), so full-report materialization has not shown
a benefit for that query.

These are individual development runs, not benchmark medians. Combined times
sum the measured stages and exclude response serialization and network time;
other requests were sometimes executing concurrently. Returned row counts
are not counts of rows scanned. Python syntax and whitespace checks passed.

## Next experiment: a smaller summary input

Two build-time options remain:

- Precompute each report's complete unfiltered summary; keep live aggregation
  for filtered requests.
- Aggregate monthly holdings to
  **report × account × source × sink × hedge type**, summing MWh across months.

Explore the second option next: one smaller table could feed all current summary
queries while preserving account and inclusive source/sink filters. Monthly
matrices would keep using monthly holdings; contract details would keep using
original holdings. A future summary month filter would require monthly data.

First compare row counts at the two grains, then compare timings and equivalent
results for the overview, point filters, and large-account filters. The size
reduction and speedup are recorded below.

## 6. Build and query the month-free aggregate

Built `crr_summary_holdings` at the proposed grain, storing one summed `mwh`
measure. Summary totals, geography, and rankings now use it through
`summary_holdings_query`; monthly matrices and contract details are unchanged.
The dataset builder populates it and validates path totals against monthly data.
Source and sink indexes preserve the split point lookups; the primary-key index
supports account filtering.

The existing database was extended in place for this experiment:

- Monthly input: **799,368 rows**.
- Summary aggregate: **246,197 rows**, about 69% fewer.
- Aggregate and index build: **3.87 seconds** locally.

Single-run local comparisons of complete `get_summary` calls (milliseconds):

| Filters | Monthly input | Summary input |
| --- | ---: | ---: |
| Report only | 13,883 | 5,373 |
| HB_NORTH | 849 | 240 |
| LZ_NORTH | 659 | 212 |
| XEDIS2 (largest monthly row count) | 503 | 55 |
| XEDIS2 + HB_NORTH | 183 | 41 |

These local runs use a different runtime from the earlier Docker logs and
different cache states; compare within this table, not against earlier timings.
All five responses matched the previous results, allowing the existing
floating-point tolerance. The build fixture and 11 geography, ranking, source,
and sink tests passed. Full API test discovery was blocked locally by missing
`fastapi` for the contract test module.

Docker stage totals fell from 8,153 to 3,470 ms for the overview, 258 to 75 ms
for HB_NORTH, 94 to 46 ms for LZ_NORTH, and 10 to 2 ms for XLUREP.
These are single runs, excluding serialization and network time.

The unfiltered overview still
aggregates every summary row; consider sharing geography/ranking aggregation
or precomputing that overview if its measured latency remains too high.

## 7. Scan the summary table for report-only requests

Added `NOT INDEXED` only when neither account nor settlement point is selected.
The local plan now shows `SCAN crr_summary_holdings`; point filters still use
the source and sink indexes. A single local comparison of complete summary
calls fell from **5,106 ms to 2,287 ms** for the overview. All five comparison
responses matched within tolerance, and filtered timings stayed similar.
The Docker run reduced measured overview stages from **3,470 to 1,510 ms**:

| Stage, ms | Index access | Table scan |
| --- | ---: | ---: |
| Totals | 1,197 | 611 |
| Geography | 951 | 436 |
| Account rankings | 69 | 133 |
| Point rankings | 1,253 | 331 |

Account rankings regressed individually, but the combined time improved.
Filtered stage totals remained small: 67 ms for HB_NORTH, 42 ms for LZ_NORTH,
and 2 ms for XLUREP. These are single-run stage sums, excluding serialization
and network time. Next, test sharing geography and point-ranking aggregation.

This forced scan is an
experiment and may be less suitable when a report selects a small part of a
database containing many reports.

## 8. Persist optimizer statistics

Ran `ANALYZE` on the existing database and added it to the end of the dataset
build, after validation. Statistics persist in the published SQLite file.
Without a hint, the basic report-only selection changed from a `summary_sink`
index search to a table scan. Statistics show all 246,197 summary rows belong
to one report. Full unhinted geography and point-ranking plans also chose
table scans; totals retained some base-index reads in subqueries locally.

The code still contains `NOT INDEXED`. Next, remove it and repeat the Docker
profiling to compare planner-selected access with the forced scan.

## 9. Remove the forced scan after ANALYZE

Removed `NOT INDEXED` from the summary query builder. With persisted statistics,
the basic report-only selection chooses a table scan; point and account filters
still choose their corresponding indexes.

A single local complete-summary run took 2,208 ms unfiltered, 72 ms for HB_NORTH,
41 ms for LZ_NORTH, 48 ms for XEDIS2, and 44 ms for XEDIS2 + HB_NORTH.
The overview is similar to the earlier forced-scan local run (2,287 ms);
statistics and cache states differ, so this is not an isolated timing comparison.
All five responses matched the forced-scan results within tolerance, and the
11 geography, ranking, source, and sink tests passed. Whitespace checks passed.
Docker plans confirmed table scans for the overview and index lookups for
point/account filters. Measured stage sums remained comparable:

| Filters, ms | Forced scan | ANALYZE without override |
| --- | ---: | ---: |
| Report only | 1,510 | 1,546 |
| HB_NORTH | 67 | 67 |
| LZ_NORTH | 43 | 39 |
| XLUREP | 2 | 2 |

These are single runs, excluding serialization and network time. Keep the
override removed and retain build-time statistics. Next, test sharing geography
and point-ranking aggregation to reduce repeated full-report work.

## 10. Share geography and point-ranking aggregation

Replaced separate geography and point-ranking queries with `get_point_summary`.
One SQL aggregation calculates source, sink, and ranking MWh per point. Source
contributions always enter the ranking; sink contributions enter only for
non-self paths. This preserves self-path semantics without subtracting large
floating-point totals. Python builds the map response and sorts the same point
rows by descending ranking MWh, then identifier, taking the first 100.

Single local complete-summary comparisons (milliseconds):

| Filters | Separate queries | Shared aggregation |
| --- | ---: | ---: |
| Report only | 1,906 | 1,372 |
| HB_NORTH | 60 | 51 |
| LZ_NORTH | 35 | 32 |
| XEDIS2 | 42 | 33 |
| XEDIS2 + HB_NORTH | 33 | 26 |

All five responses matched within tolerance, including ranking order.
The 11 geography, ranking, source, and sink tests and whitespace checks passed.
These are single local runs with differing cache states. Next, repeat in Docker;
the combined helper logs `point summary SQL` and Python result-building times.

Docker stage sums fell from 1,546 to 1,193 ms for the overview, 67 to 46 ms for
HB_NORTH, and 39 to 27 ms for LZ_NORTH. XLUREP stayed around 2 ms. Geography
and point rankings together fell from 801 to 497 ms in these individual runs.

## 11. Reuse the participating-point count

Removed the totals query's points CTE and count subquery. Geography already
returns every participating point, including zero-exposure points and those
without coordinates, so `settlementPointCount` now uses its result length.

A single local complete-summary comparison fell from 1,384 to 1,264 ms for the
overview, 47 to 39 ms for HB_NORTH, and 28 to 23 ms for LZ_NORTH. All five
comparison responses matched within tolerance. The 11 geography, ranking,
source, and sink tests and whitespace checks passed. Next, repeat in Docker
and compare the totals query time; cache states differ between these local runs.

Docker totals-query time fell from 621 to 408 ms; the point-union subquery is
absent from the plan. Measured summary stage sums:

| Filters, ms | Before count reuse | After count reuse |
| --- | ---: | ---: |
| Report only | 1,193 | 1,008 |
| HB_NORTH | 46 | 47 |
| LZ_NORTH | 27 | 31 |
| XLUREP | 2 | 2 |

These are single runs excluding serialization and network time. Small filtered
differences do not establish a regression. The overview's remaining major
stages are shared point aggregation (529 ms) and totals/distinct paths (408 ms).
Next, assess further shared work or a precomputed unfiltered overview.

## 12. Profile source and sink holdings

Added query plans, SQL/fetch timings, returned row counts, and Python cell setup
and fill timings to both matrix requests. Monthly cell queries now fetch all
rows before filling cells so SQL work is measured separately. Query predicates
and response contents are unchanged; the original-contract endpoint is unchanged.

Single local SQL timings (milliseconds), using the first source on each page
for the corresponding sink expansion:

| Query | Unfiltered | HB_NORTH | XEDIS2 |
| --- | ---: | ---: | ---: |
| Source timeline | 201 | 208 | 205 |
| Source bounds | 411 | 33 | 50 |
| Source rankings | 902 | 46 | 26 |
| Source monthly cells | 118 | 40 | 12 |
| Sink timeline | 213 | 205 | 200 |
| Sink rankings | 9 | 8 | 1 |
| Sink monthly cells | 11 | 10 | 2 |

Python cell setup/fill took under 5 ms combined per request in these runs.
Seven source/sink tests and whitespace checks passed. These are local single
runs; next, inspect Docker timings. Source ranking and the shared report
timeline are the initial candidates for investigation, without changing them yet.

Docker sink expansions showed the timeline dominating: 127–131 ms versus
5–8 ms for rankings and 7–9 ms for monthly cells across HB_NORTH, HB_HOUSTON,
and HB_WEST. Python setup/fill remained around 3–5 ms combined.

## 13. Index report delivery months

Added `monthly_report_month` on `(report_id, delivery_month)` to the build and
existing database. Split the timeline seed into separate MIN and MAX scalar
subqueries so each can find an endpoint without scanning all report entries.
Analyzed the new index in the existing database; normal builds analyze all
indexes at completion.

The local plan uses the new covering index for both bounds. Timeline SQL took
0.51 ms for the same 42 months, versus around 200 ms in the original local
profile. An absent report still returns no months. Seven source/sink tests
and whitespace checks passed. Next, repeat the sink expansions in Docker.

Docker timeline time fell from about 130 ms to 0.37–0.40 ms. Measured sink
expansion stages fell from 149 to 33 ms for HB_NORTH and 147 to 26 ms for
HB_HOUSTON in individual runs, excluding serialization and network time.

## 14. Profile individual contracts

Added query plans and separate SQL/fetch and Python grouping/sorting timings
to the contract endpoint, reusing the holdings profiling helper. It now fetches
rows before grouping so SQL work is excluded from the Python timer.

Local queries for August 2026 OBL contracts took 5.11 ms SQL + 0.95 ms Python
for HB_NORTH → LZ_NORTH (440 rows), and 4.32 ms SQL + 1.15 ms Python for
HB_HOUSTON → LZ_HOUSTON (404 rows). Both responses exactly matched the prior
implementation. The plan uses `holdings_path_dates` through report, source,
sink, and the start-date range. Whitespace checks passed. Contract fixture
tests still require the unavailable local FastAPI dependency. Next, capture
the same requests in Docker; no query optimization was made in this step.

Docker contract timings confirmed small costs: August OBL HB_NORTH → LZ_NORTH
returned 440 rows in 7.44 ms SQL + 1.61 ms Python; September Houston → Houston
returned 54 OPT rows in 1.30 + 0.25 ms and 410 OBL rows in 5.37 + 0.56 ms.
Sink expansions remained around 25–30 ms across measured stages. These are
individual runs excluding serialization and network time. Leave these queries
unchanged and profile top-level source pagination next.

## 15. Profile top-level source pagination in Docker

Called `get_source_holdings` directly in the existing API container against its
read-only database. Each case used report 1 and a page size of 20; no query
changes were made. These sequential single runs exclude HTTP, serialization,
and rendering. Function totals include query-plan logging overhead.

| Stage, ms | First page | Second page | HB_NORTH | XEDIS2 |
| --- | ---: | ---: | ---: | ---: |
| Timeline | 0.21 | 0.19 | 0.27 | 0.28 |
| Portfolio bounds | 235 | 252 | 28 | 43 |
| Source rankings | 642 | 611 | 40 | 17 |
| Monthly cells | 87 | 62 | 37 | 9 |
| Complete function | 966 | 926 | 106 | 70 |

Both unfiltered pages recompute report-wide bounds and rankings. Ranking uses
`monthly_source` by report, then sorts aggregated source totals before applying
LIMIT/OFFSET. Bounds scan the monthly table, checking nonzero MWh. Monthly cells
use selective source lookups. Point-filtered plans now show `MULTI-INDEX OR`
using both source and sink indexes, so the earlier OR-filter problem is not
present in these plans. Account filters use account-prefix indexes.

Next: test ranking sources from the existing month-free summary aggregate,
while retaining monthly data for cells and nonzero-exposure date bounds.
Ranking order can change slightly from floating-point regrouping and should
be checked. The nonzero monthly bounds cannot be recovered from that aggregate
because it discards month and may combine offsetting exposures.

## 16. Rank sources from the summary aggregate

Changed only top-level source rankings to use `summary_holdings_query` and sum
its MWh by source and hedge type. Date bounds and monthly cells retain their
monthly input. Fixtures that modify monthly holdings now rebuild the aggregate
before querying, matching the dataset build lifecycle.

Single-run comparisons in the existing API container (milliseconds):

| Case | Ranking before | Ranking after | Function before | Function after |
| --- | ---: | ---: | ---: | ---: |
| First page | 642 | 116 | 966 | 449 |
| Second page | 611 | 117 | 926 | 421 |
| HB_NORTH | 40 | 7 | 106 | 78 |
| XEDIS2 | 17 | 2 | 70 | 55 |

Four full page responses matched the monthly implementation within floating-point
tolerance, including source order and pagination. Seven source/sink tests and
whitespace checks passed. These are sequential single runs, not medians, and
exclude HTTP/serialization. Unfiltered bounds now dominate at about 242–247 ms.
Next, investigate endpoint lookups for nonzero monthly exposure bounds using
the existing report/month index before adding more stored aggregates.
