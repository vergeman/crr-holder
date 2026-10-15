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
