# Shared service SQL experiment

All three `_query*` wrappers in `source_holdings.py` now load complete statements. Python loads UTF-8 text through `load_sql`; browser consumers can load
the same files as text. The source-holdings WASM experiment is described in
`web/src/README.md`; earlier measurements below predate that browser adapter.

## Source-month contract

The statement returns `(source, delivery_month, hedge_type, mwh)` in that column
order. `mwh` is the sum of the three MWh columns. Grouping and row order match
the original query; there is no explicit ORDER BY.

Bound parameters:

* `report_id`: resolved integer report ID.
* `account_holder`: string or NULL; NULL and the empty string omit the filter.
* `settlement_point`: string or NULL; NULL and the empty string omit the filter.
* `sources`: JSON text encoding an array of source strings; an empty array
  returns no rows. Python uses `json.dumps(sources)`; JavaScript uses
  `JSON.stringify(sources)`.

Execute the complete statement unchanged with named bound parameters. Normalize
absent or empty account and point filters to NULL before binding. No SQL text
expansion is required. SQLite must support `json_each`.

## Measured strategy

Measurements use the existing database and measurement inputs, with both source
pages for market, account, point, and combined filters. Raw captures remain in
`/tmp`, outside Git. Isolated query medians use five samples after an initial
execution; the existing service runner uses its unchanged warm-up and three
samples. Timings below are milliseconds.

The focused repeat confirmed these first-page query results:

| Filter | Original predicates/list | JSON list only | Nullable filters + JSON |
| --- | ---: | ---: | ---: |
| Account | 0.275 | 0.230 | 8.129 |
| Point | 37.313 | 38.119 | 37.269 |
| Combined | 0.126 | 24.725 | 2.574 |

Nullable account predicates replace the composite account/source index lookup
with `monthly_source`. JSON lists alone change combined filtering from the
composite account/source lookup to MULTI-INDEX OR, including `monthly_sink`.
The user accepted these timing differences for this experiment. Use the complete
statement with nullable filters and JSON source binding so both runtimes can
execute it without SQL text expansion. Other queries remain outside this trial.

Python SQLite 3.46.1 successfully executed `json_each('[1]')`; tested JSON lists
were JSON arrays of source strings bound as text. JSON and nullable candidates
returned exactly the original rows. Target WASM feature verification remains
open until a build is selected; no browser performance claim is made.

## Bounds and ranking contracts

All files below are under `crr_holdings/`. Parameters use the same resolved
`report_id` and empty-to-NULL account/point conventions as source-month cells.

| Statement | Bound parameters | Returned columns |
| --- | --- | --- |
| `source_portfolio_bounds.sql` | report_id, account_holder, settlement_point | first_month, last_month (positional; either may be NULL) |
| `source_portfolio_bounds_point.sql` | report_id, settlement_point (required) | first_month, last_month (positional; either may be NULL) |
| `ranked_sources.sql` | report_id, account_holder, limit, offset | source, total_opt_mwh, total_obl_mwh |
| `ranked_sources_point.sql` | report_id, account_holder, settlement_point (required), limit, offset | source, total_opt_mwh, total_obl_mwh |

Bounds select MIN/MAX only for a nonempty point without an account; otherwise
they search the month timeline from each end for nonzero inventory. Ranking
selects the point variant whenever a point is present, preserving source/sink
UNION ALL and excluding self paths from its sink branch. Both rankings order
by combined totals descending, then source ascending, before pagination.

All statements execute unchanged with bound values; none requires templating.
The wrappers may bind extra unused account/point values. Nullable account
predicates change account-index lookups to report/source-index lookups; this
is recorded as an accepted strategy, not an assertion of identical query plans.
The direct point-only bounds predicate retains the indexed source/sink OR plan.

## Query conversion inventory

All five query services now load complete statements. Sink totals, sink monthly
cells, and contract segments were the final queries extracted; their contracts
and validation are recorded below.

## Current validation

All 20 API tests pass, including exact response fixtures. All eight measured
source responses match `0015-before` exactly. `git diff --check` passes.

Service medians from `0015-null-json`, compared with `0015-before` (ms):

| Source workload | Before | NULL filters + JSON |
| --- | ---: | ---: |
| Market, first page | 212.74 | 208.61 |
| Market, second page | 188.05 | 197.27 |
| Account, first page | 0.63 | 8.29 |
| Account, second page | 0.15 | 0.14 |
| Point, first page | 77.35 | 65.74 |
| Point, second page | 69.67 | 57.01 |
| Combined, first page | 4.28 | 6.41 |
| Combined, second page | 4.94 | 3.97 |

## Remaining source-wrapper validation

All 20 API tests pass after extracting bounds and rankings. All 22 measured
service responses in `0015-sources-complete` match `0015-before` exactly.
`EXPLAIN QUERY PLAN` confirms that point-only bounds retain MULTI-INDEX OR and
point rankings retain indexed source/sink UNION ALL. Nullable account filters
lose account-index lookups in both bounds and ranking.

Source-service medians (ms), comparing the accepted source-month implementation
with the remaining wrappers extracted:

| Workload | `0015-null-json` | `0015-sources-complete` |
| --- | ---: | ---: |
| Market, first page | 208.61 | 207.01 |
| Market, second page | 197.27 | 178.51 |
| Account, first page | 8.29 | 170.63 |
| Account, second page | 0.14 | 161.89 |
| Point, first page | 65.74 | 71.71 |
| Point, second page | 57.01 | 64.87 |
| Combined, first page | 6.41 | 95.85 |
| Combined, second page | 3.97 | 91.80 |

The preceding `0015-sources-all` run also measured account requests at
156–172 ms and combined requests at 100–101 ms, confirming the larger cost
of nullable account predicates in the remaining queries. These costs remain
visible for review; browser execution and timing remain unverified.

## Settlement-point totals experiment

`summary/settlement_point_totals.sql` and
`summary/settlement_point_totals_point.sql` extract only
`_query_settlement_point_totals`. At this stage the other summary queries
remained in Python; they are now extracted as described below.

Both statements bind `report_id` and `account_holder` (empty/absent account
becomes NULL). Select the point variant for a nonempty `settlement_point` and
bind that value. It retains indexed source/sink UNION ALL and excludes self
paths from the sink branch. No SQL text expansion is required.

Returned columns, in order: `point`, `longitude`, `latitude`, `source_mwh`,
`sink_mwh`, `total_mwh`. Rows sort by point. Missing coordinates remain NULL.
Materialized holdings feed both endpoint roles; self paths contribute to both
geographic roles and once to ranking totals. Python still assembles geography
and selects the top 100 points from these rows.

These statements require SQLite's `AS MATERIALIZED` syntax (SQLite 3.35.0+),
which the existing Python query already used. WASM build verification remains
open until a build is selected.

All four workload query outputs match exactly. Market and point query plans
are unchanged. Nullable account filtering changes the account-only lookup to
a scan of `crr_summary_holdings`; combined filtering uses `summary_source`
instead of the composite account/source index. Endpoint role expansion,
materialization, grouping, coordinate joins, and ordering retain their plans.

Summary-service medians (ms):

| Workload | `0015-points-before` | `0015-points-after` | `0015-points-complete` repeat |
| --- | ---: | ---: | ---: |
| Market | 936.62 | 887.46 | 851.28 |
| Account | 0.15 | 25.75 | 25.79 |
| Point | 25.43 | 26.03 | 26.50 |
| Combined | 11.36 | 14.27 | 14.33 |

The repeat confirms the account-only cost. These are full summary-service
medians; only settlement-point totals changed. All 20 API tests pass, all 22
measured responses match the original baseline, and all four summary responses
also match the immediate baseline exactly. `git diff --check` passes.


## Full source-holdings WASM trial

`resolve_report.sql` returns the latest `(report_id,)` with no parameters.
`crr_holdings/delivery_months.sql` binds `report_id` and returns `(month,)` rows
in ascending order, including gaps between report endpoints. Both Python helpers
and the source-holdings browser worker execute these files unchanged.

The browser trial selects `@sqlite.org/sqlite-wasm` 3.53.4-build2 and imports the
API-served database read-only. Successful complete source responses verify
`json_each`, nullable predicates, recursive month generation, bound values, and
all source statement variants in that build. The summary and metadata browser
checks are recorded below.

Browser verification on the real API-served database passed: both pages for
market/account/point/combined filters, latest-report selection, empty filters,
empty results, and request cancellation. Complete browser responses equal the
HTTP responses exactly. The holdings panel rendered at 1440px and 390px widths.
All 20 API tests, the Vite build, Prettier checks, and `git diff --check` pass.
The build retains its large-chunk warning.


## Summary and metadata WASM extraction

All metadata and summary wrappers now load complete statements. The browser
provider in `web/src/data/wasmProvider.js` shares one database and worker with
source holdings. Its `getMetadata`, `getSummary`, and `getSourceHoldings` methods
use the same arguments and response shapes as the HTTP provider. No new runtime
dependency or dataset copy is added.

The API serves metadata files through `/api/metadata-sql/{statement}` and summary
files through `/api/summary-sql/{statement}`. The worker loads them once with the
source statements. Sinks and contracts remain on HTTP. Per-method HTTP switches
are documented in `web/src/README.md`.

Additional statement contracts:

| File | Parameters | Returned columns, in order |
| --- | --- | --- |
| `metadata/reports.sql` | none | report_id, publication_date |
| `metadata/report_account_holders.sql` | report_id | account_holder, legal_name |
| `metadata/settlement_point_choices.sql` | report_id, account_holder | settlement_point |
| `summary/portfolio_metrics.sql` | report_id, account_holder | total_mwh, holder_count, directed_path_count, opt_mwh, obl_mwh (positional) |
| `summary/portfolio_metrics_point.sql` | report_id, account_holder, settlement_point | same metrics |
| `summary/top_account_holders.sql` | report_id, account_holder | account_holder, legal_name, total_mwh |
| `summary/top_account_holders_point.sql` | report_id, account_holder, settlement_point | same account columns |

Empty or absent account values bind as NULL. A nonempty point selects the point
variant and binds `settlement_point`. Explicit report IDs are preserved; omitted
IDs use the shared latest-report statement. Report holder choices remain
independent of account filters. Point choices use a deduplicating endpoint
UNION. Summary point queries preserve indexed source/sink UNION ALL with self
paths counted once. Counts, null handling, ordering, and ranking limits retain
the existing response contract. JavaScript uses numeric MWh sorting and direct
identifier comparisons to match Python's top-point tie ordering.

`EXPLAIN QUERY PLAN` comparisons show that nullable account predicates remove
account-index constraints from metadata point choices, summary metrics, and
account rankings. Market point choices also change covering indexes. All 18
captured query results match exactly; point variants retain endpoint indexes.

API service medians in milliseconds:

| Workload | `0015-summary-meta-before` | `0015-summary-meta-after` | `0015-summary-meta-complete` repeat |
| --- | ---: | ---: | ---: |
| Metadata, market | 939.27 | 1259.05 | 1042.10 |
| Metadata, account | 415.22 | 853.67 | 557.16 |
| Summary, market | 1127.62 | 1115.00 | 1035.44 |
| Summary, account | 33.39 | 116.05 | 98.79 |
| Summary, point | 32.41 | 29.86 | 31.37 |
| Summary, combined | 15.66 | 15.28 | 19.33 |

Account filtering remains slower with nullable predicates. Raw captures stay
outside Git; response baselines were not regenerated. All 22 final measured
service responses match the original baseline, and metadata/summary also match
the immediate baseline.

Browser validation passes on the real API-served database: complete metadata
and summary equality for market, account, point, combined, latest-report,
empty-result, and empty-filter requests; source pagination and cancellation
also pass. The initial load downloads one database and makes no metadata,
summary, or source-holdings API calls. The existing committed fixtures also
match all 13 metadata/summary responses, including previous reports, ties,
self paths, missing coordinates, and zero exposure. This verifies summary's
`AS MATERIALIZED` statements in the selected WASM build.

The page renders summary, map markers, and source rows at desktop and narrow
widths. All 20 API tests, the Vite build, Prettier checks, and
`git diff --check` pass. The build retains its large-chunk warning.
Desktop and narrow UI interactions also pass: account selection, filtered point
choices, combined selection, map/summary updates, clearing filters, and source
pagination.

## Direct-account variant speed trial

For a nonempty account, Python and the WASM worker now select complete
`*_account.sql` statements. These statements replace only the nullable account
predicate with `account_holder = :account_holder`; parameter names and returned
columns match their original counterparts. Statements for requests without an
account are unchanged. JSON source-list binding and point-filter handling are
unchanged, isolating the account predicate's effect.

Account variants cover metadata's settlement-point choices; summary metrics,
account rankings, and settlement-point totals (including their point variants);
and source bounds, rankings (including point), and month cells. Point-only
bounds have no account variant because that strategy is selected only without
an account. `selectStatement` in the worker selects loaded SQL text by name;
Python selects the corresponding file before calling `load_sql`. Neither
runtime expands SQL text.

Query plans regain `monthly_account` for account bounds and composite account
indexes for metadata point choices, source rankings/cells, summary metrics,
and summary rankings/totals. Combined variants retain separate source/sink
lookups. Captured metadata/summary query rows and all 22 measured API responses
match the immediate baseline exactly.

API medians (ms), using the existing runner and inputs:

| Workload | `0015-account-variants-before` | `0015-account-variants-after` |
| --- | ---: | ---: |
| Metadata, account | 605.04 | 418.35 |
| Summary, account | 105.30 | 0.15 |
| Sources, account first page | 269.37 | 1.13 |
| Sources, account second page | 271.19 | 0.17 |
| Summary, combined | 15.45 | 13.33 |
| Sources, combined first page | 148.53 | 5.01 |
| Sources, combined second page | 114.49 | 4.57 |

Browser medians (ms), three samples after warm-up on the same real database,
excluding download/import and including the worker request and response:

| Workload | Nullable account predicate | Direct account predicate |
| --- | ---: | ---: |
| Metadata, account | 2089.00 | 617.40 |
| Summary, account | 127.80 | 2.20 |
| Sources, account first page | 201.80 | 3.00 |
| Metadata, combined | 1949.10 | 454.80 |
| Summary, combined | 8.70 | 8.00 |
| Sources, combined first page | 88.40 | 5.10 |

Account summary and source queries improve substantially. Metadata improves,
but remains the largest part of an account selection. These are local test
measurements; raw captures remain outside Git and response baselines were not
regenerated.

Verification passes: all 20 API tests, eight complete browser/API response
comparisons for account and combined selections (including both source pages),
desktop/narrow filter interactions and pagination, Vite build, Prettier, and
`git diff --check`. The build retains its existing large-chunk warning.

## HTTP range VFS provider

The optional `vfsProvider` in `web/src/data/wasmProvider.js` uses the same worker
query selection and response assembly as `wasmProvider`. The header's Data
provider selector switches all three methods and reloads the page. It writes
`provider=wasm`, `provider=vfs`, or `provider=http` and clears per-method
overrides. Direct URLs and per-method overrides remain available.

`/api/database` now handles HEAD as well as GET. Starlette's existing
FileResponse supplies Accept-Ranges, Content-Length, byte-range 206 responses,
and 416 responses for unsatisfiable ranges. The VFS opens it read-only and
requests pages rather than first downloading the complete file. Same-origin
requests use the existing Vite proxy.

Pinned `sqlite-wasm-http` 1.2.0 supplies the HTTP VFS and bundled SQLite 3.44.2.
Its synchronous HTTP backend runs inside the worker, using the library's
standard in-memory cache. Full-download WASM continues using SQLite 3.53.4.
The database's existing 4096-byte pages and schema are unchanged.

The first indexed account-summary test made one HEAD and 22 successful range
GETs totaling 115,712 database bytes, compared with the 398,688,256-byte full
file. Cold setup plus this query took about 2.5 seconds in that run. This is a
single local observation, not a median or a general speed claim.

A cold real-market metadata request issued thousands of small range reads and
did not complete during the multi-minute trial; that scan was canceled. VFS
avoids the upfront complete download but does not resolve the report-wide
account-holder scan. Full real-market VFS behavior remains a performance
limitation of this experiment; the default remains full-download WASM.

The three database transport tests verify HEAD, exact partial bytes, and
unsatisfiable ranges. All 23 API tests pass. Thirteen existing metadata/summary
fixture responses match through the VFS runtime using simulated range responses,
including previous reports, null coordinates, ties, self paths, and zero
exposure. The fixture-backed page renders with all three methods on VFS at
desktop and narrow widths. These fixture checks do not substitute for the
separate real-endpoint checks.


## Sink and contract conversion completion

The remaining Python wrappers now load complete statements from `crr_holdings/`.
The same source-SQL transport serves them to the worker. Each statement has a
`*_account.sql` variant with a direct account predicate; absent or empty optional
filters bind as NULL. Both runtimes select the same variant without SQL text
expansion. The unused Python predicate builder has been removed.

| Statement | Parameters | Returned columns, in order |
| --- | --- | --- |
| `ranked_sinks.sql` | report_id, account_holder, settlement_point, source | sink, total_opt_mwh, total_obl_mwh |
| `sink_month_cells.sql` | report_id, account_holder, settlement_point, source | sink, delivery_month, hedge_type, mwh |
| `contract_segments.sql` | report_id, account_holder, settlement_point, source, sink, month, hedge_type | account_holder, legal_name, time_of_use, crr_id, segment_id, crr_type, start_date, end_date, mw, hours, month_mwh |

Sink rankings retain descending combined MWh and ascending identifier ties.
Monthly cells retain the report timeline with zero-filled gaps. Contract queries
retain inclusive delivery-month bounds and order segments by descending monthly
MWh, then contract and segment identifiers. Browser assembly retains holder
ranking, fixed time-of-use order, and zero-MW contracts. The grand total uses
compensated summation to match Python 3.12's `sum()` over holder totals.

All five methods now follow the selected provider. `sinks` and `contracts` URL
parameters support independent overrides, and changing the header selector
clears all five overrides. VFS uses the same new worker methods, but its
real-market performance trial remains stopped.

Validation:

* API fixtures: 23 tests passed; committed response baselines unchanged.
* Real-database service comparison: all eight sink/contract responses unchanged.
* WASM/HTTP comparison: all 14 sink/contract responses matched exactly;
  cancellation checks passed.
* Browser fixtures: all 13 committed sink/contract responses matched exactly.
* Desktop and narrow interactions: sink expansion, contract details, disclosures,
  closing, and clearing filters passed without holdings HTTP calls.
* HTTP/WASM provider switching and clearing method overrides: passed.
* Vite build, Prettier, and whitespace checks: passed; existing large-chunk
  warning remains.

The existing service runner captured before/after sink and contract timings under
`0015-drilldowns-before` and `0015-drilldowns-after` in the API container's `/tmp`.
These response-validation runs overlapped browser work and are not an isolated
performance benchmark. No new WASM/API benchmark or real-market VFS timing claim
is made here.
