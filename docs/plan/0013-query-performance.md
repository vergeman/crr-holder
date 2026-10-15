# 0013 - Query Performance

Type: perf
Branch: perf/0013-query-performance

Depends on: [0012 - Service Timing](0012-service-timing.md)

## Goal

* Apply the successful `experiment/db-performance:db/README.md` findings, tracking
  response equivalence and service timings after each optimization.

* Establish the optimized baseline for
  [0014 - Service Query Boundaries](0014-service-query-boundaries.md).

## Tasks and commit groups

Implement the nine tasks in order on `perf/0013-query-performance`, with at least
nine commits: the baseline first, then one commit per discrete improvement.
Include each task's verification results in its commit. Keep formatting-only
changes separate and immediately after the related implementation. Do not push.

After each task, finish verification, commit the result, and stop. Report the
commit, brief results, and any material differences; prompt the user to review
and wait for their reply before beginning the next task. Do not start 0014
automatically after task 9.

Use the referenced experiment commits as implementation guides, adapting their
changes to current modules. Do not cherry-pick profiling or unrelated changes.

### 1. Capture responses and timings before changes

Commit: `test: capture service response and timing baselines`

* Capture all five services' responses from existing fixture scenarios as JSON
  under `api/tests/fixtures/service_responses/`. Add
  `api/tests/test_service_responses.py` to compare complete outputs; keep inputs
  and fixture setup in code. Reuse existing coverage for filters, pagination,
  timeline gaps, empty portfolios, self paths, and nonempty contract details.
  Never regenerate expected responses automatically during tests.

* Add a small `api/tests/measure_services.py` runner using existing `@timed`
  service entry points against the real read-only database. Enable timing before
  imports and configure the existing logger; leave `api/timing.py` unchanged.
  Load fixed report and request inputs from
  `api/tests/fixtures/measurement_inputs.json` for all five services, covering unfiltered,
  account, point, combined filters, and source pagination where applicable.

* Capture complete real-data responses and timing logs under `/tmp`. Use the same
  database inputs, one warm-up, and three measured calls per workload. Record
  baseline medians here; after each optimization rerun only affected workloads
  and record their medians against the baseline and preceding step. Include the
  request inputs once so comparisons can be reproduced. Timings cover service
  execution, excluding HTTP and connection setup; add no timing assertions.

### 2. Build the summary aggregate

Commit: `perf(db): build summary holdings aggregate`
Reference: `5928a37` (dataset and fixture changes).

* Add `crr_summary_holdings` at report/account/source/sink/hedge-type grain with
  summed `mwh`, its composite primary key, and source/sink indexes. Populate it
  after monthly holdings via `db/crr/sql/summary_holdings.sql`; validate totals
  against monthly data and materialize it once during fixture setup.

### 3. Use aggregate holdings for summary queries

Commit: `perf(api): query summary holdings with selective filters`
References: `48bb950` (split point filters), `5928a37` (aggregate selection).

* Add `summary_holdings_query()` in `api/services/helpers.py`. Select the new
  aggregate with bound report/account filters; split point matches into disjoint
  source and sink branches with `UNION ALL`, preserving self-path semantics.
  Use it for summary totals, geography, and holder/point rankings.

### 4. Reuse filtered holdings within queries

Commit: `perf(api): materialize reused filtered holdings`
Reference: `48bb950` (materialized totals and geography CTEs).

* Mark totals and geography holdings CTEs `AS MATERIALIZED` to reuse their
  filtered inputs.

### 5. Publish optimizer statistics

Commit: `perf(db): publish optimizer statistics`
References: `4c02819`, `6d7b7f3`.

* Run `ANALYZE` after dataset validation and before publication. Let SQLite choose
  access paths; do not carry over the experiment's superseded `NOT INDEXED` hint.
  Recheck the combined-filter regression identified in task 3.

### 6. Share point aggregation

Commit: `perf(api): share point aggregation and count`
References: `fd438e1`, `ef1aeef`.

* Introduce `get_settlement_point_summary()` for geography and point rankings. Preserve
  separate source/sink exposure, count self paths once in rankings, and retain
  zero-exposure points and missing coordinates. Derive settlement-point count
  from the complete geography list and remove its separate totals calculation.

### 7. Seek report timeline endpoints

Commit: `perf(db): index report timeline endpoint lookups`
Reference: `5f97a08`.

* Add `monthly_report_month(report_id, delivery_month)`. Seed `delivery_months()`
  with separate scalar MIN/MAX lookups, keeping continuous month expansion.
  Include the index in build-time statistics.

### 8. Rank sources from summary holdings

Commit: `perf(api): rank sources from summary holdings`
Reference: `3fe259a`.

* Use `summary_holdings_query()` for source ranking. Keep pagination, monthly
  cells, and nonzero date bounds on their existing semantics and data sources.

### 9. Seek nonzero portfolio bounds

Commit: `perf(api): seek nonzero portfolio date bounds`
Reference: `1b5b70f`.

* Use ordered earliest/latest nonzero-month lookups with `LIMIT 1` for report-only
  and account-filtered requests, including account-plus-point filters. Retain
  combined MIN/MAX for point-only requests, as established by the experiment.

* Finish this task by comparing final outputs with the original baselines before
  explicitly updating committed fixtures to the optimized responses. Record any
  permitted numeric differences; require exact fixture comparisons afterward. Complete 0013 before
  starting the structural refactor.

## Scope control

* Limit changes to the existing dataset build/SQL/tests and affected API
  services/tests, plus the files named above. Keep endpoint contracts, matrix
  cells, contract queries, and OFFSET pagination. Port successful changes into
  current modules; do not merge experimental profiling or unrelated changes.

* Allow only the specified aggregate, indexes, fixtures, and measurement runner.
  Add no dependencies, query framework, browser provider, or SQL extraction.

* Treat tasks and verification as closed lists. Explain and ask before adding
  unplanned files, stored data, dependencies, or substantial verification.
  Resolve routine implementation choices within scope without confirmation.

## Verification

* Compare fixture and real-data responses after each optimization. Require exact
  structure, identifiers, counts, ordering, pagination, and nulls. Allow only
  MWh differences within `1e-6 + 1e-10 * abs(expected)` during optimization;
  investigate ranking changes rather than sorting them away.

* Inspect Compose configuration and `docker compose ps`; reuse running services.
  Run after baseline capture and each optimization:
  `docker compose exec -T -e ENABLED_TIMED=1 api python -m unittest discover -s tests -v`.

* Measure affected workloads with
  `docker compose exec -T -e ENABLED_TIMED=1 api python tests/measure_services.py`;
  let the runner accept service names to select workloads.
  Use `--label task-N` for later captures to preserve the original baseline. Keep raw captures in
  `/tmp/0013-query-performance/` and concise results in this plan. Investigate measured regressions
  before proceeding; experiment timings are reference observations, not targets.

* For build changes, run
  `python3 -m unittest discover -s db/crr/tests -v` with the dataset dependencies
  installed and build using the documented `db/crr/README.md` Docker commands.
  Rebuild only when required by a build change, before dependent measurements.

* Run `git diff --check` after each task. Do not run `EXPLAIN` or add query-plan
  logging; that investigation is already documented in the experiment branch.
  Add no broader performance suite.

## Acceptance

* [x] Original response fixtures and real-data response/timing baselines captured.

* [ ] All eight successful optimization groups implemented with response checks
  and affected service timings recorded after each group.

* [ ] At least nine task commits exist, beginning with the baseline, with a user
  review stop after each task.

* [ ] Dataset validation, API tests, and diff checks pass.

* [ ] Final optimized fixtures pass exact comparisons and are ready for 0014.

## Results

### Task 1 — baseline

* API suite: 20 tests passed. Complete-response fixtures cover all five services.
* Diff check: passed. Application services and timing library unchanged.
* Captures: `/tmp/0013-query-performance/baseline/` on the host and API
  container holds responses and timing logs. Fixed request inputs are committed
  in `api/tests/fixtures/measurement_inputs.json`.
* Inputs: report `1`, account `XNRGLD`, point/source `HB_NORTH`, sink `LZ_NORTH`,
  month `2027-06-01`, hedge `OBL`. Source pages use limit 20, offsets 0 and 20.
* Medians below are milliseconds, after one warm-up and three measured calls.
  Source entries show offset 0 / offset 20. Later runs use `--label task-N`.

| Service | Unfiltered | Account | Settlement Point | Combined |
| --- | ---: | ---: | ---: | ---: |
| metadata | 873.60 | 348.54 | — | — |
| summary | 9792.94 | 0.79 | 6072.56 | 0.54 |
| sources | 2158.83 / 2193.36 | 138.01 / 124.61 | 1967.38 / 1728.54 | 133.13 / 163.13 |
| sinks | 2423.01 | 158.61 | 2438.49 | 132.86 |
| contracts | 9.99 | 4.44 | 9.50 | 3.93 |

### Task 2 — summary aggregate

* Dataset test: passed. API suite: 20 tests passed, including exact fixtures.
* Documented Docker build and dataset rebuild: passed; all four validation
  error counts are zero. Monthly rows: 799,368; summary rows: 246,197.
* Service queries still use monthly holdings; aggregate adoption is task 3.
* Real-data responses: all 22 match the original baseline exactly.
* Raw responses/logs: `/tmp/0013-query-performance/task-2/`.
* Medians below are ms, with percentage change from baseline (also the preceding
  step). Source entries show offset 0 / offset 20.

| Service | Unfiltered | Account | Settlement Point | Combined |
| --- | ---: | ---: | ---: | ---: |
| metadata | 744.20 (-15%) | 324.66 (-7%) | — | — |
| summary | 10740.05 (+10%) | 0.97 (+23%) | 6555.79 (+8%) | 0.60 (+11%) |
| sources | 2072.52 (-4%) / 2413.15 (+10%) | 184.71 (+34%) / 185.34 (+49%) | 2471.31 (+26%) / 2575.89 (+49%) | 199.25 (+50%) / 195.66 (+20%) |
| sinks | 2577.12 (+6%) | 141.97 (-10%) | 2452.69 (+1%) | 138.86 (+5%) |
| contracts | 10.51 (+5%) | 5.21 (+17%) | 10.40 (+9%) | 4.43 (+13%) |

* Source timing recheck (`task-2-recheck/`): unfiltered 2432.80 / 2347.14 ms;
  account 140.25 / 132.98 ms; settlement point 1830.70 / 1820.45 ms;
  combined 141.93 / 141.43 ms. The larger filtered increases did not persist;
  timings vary between runs, and this preparatory task claims no speedup.
* Diff check: passed.


### Task 3 — aggregate summary queries

* API suite: 20 tests passed, including exact committed response fixtures.
* Four affected real-data responses match baseline and task 2 within MWh
  tolerance; structure, identifiers, counts, ordering, and nulls are unchanged.
  Maximum absolute MWh difference: `1.1920928955078125e-7`.
* Fixtures accept final scenario data before building the aggregate once;
  no refresh calls or expected-response changes were needed.
* Medians (ms), with original baseline and preceding task for comparison:

| Summary filter | Baseline | Task 2 | Task 3 |
| --- | ---: | ---: | ---: |
| Unfiltered | 9792.94 | 10740.05 | 3746.41 |
| Account | 0.79 | 0.97 | 0.19 |
| Settlement Point | 6072.56 | 6555.79 | 131.73 |
| Combined | 0.54 | 0.60 | 22.88 |

* Combined-filter regression reproduced at 30.71 ms median. Diagnostic selection
  timings were 4.714 ms with the default access choice versus 0.058 ms through
  the account primary key (same one returned row). This indicates an access-path
  issue before build statistics; recheck in task 5. No index hint was added.
* Captures: `/tmp/0013-query-performance/task-3/`. Diff check: passed.

### Task 4 — materialized filtered holdings

* Totals and geography reuse filtered holdings through `AS MATERIALIZED` CTEs.
* API suite: 20 tests passed, including exact committed response fixtures.
* Four real-data responses match task 3 exactly and baseline within MWh
  tolerance; maximum absolute baseline difference: `1.1920928955078125e-7`.
* Medians (ms), with original baseline and preceding task for comparison:

| Summary filter | Baseline | Task 3 | Task 4 |
| --- | ---: | ---: | ---: |
| Unfiltered | 9792.94 | 3746.41 | 3550.76 |
| Account | 0.79 | 0.19 | 0.19 |
| Settlement Point | 6072.56 | 131.73 | 37.44 |
| Combined | 0.54 | 22.88 | 20.61 |

* No new measured regressions; the combined-filter regression remains for the
  task 5 statistics recheck.
* Captures: `/tmp/0013-query-performance/task-4/` on host and API container.
  Diff check: passed.

### Task 5 — published optimizer statistics

* Dataset test, Docker rebuild, validation, and 20 API tests: passed.
* All 22 responses match preceding captures; baseline MWh differences are
  within tolerance (maximum `1.1920928955078125e-7`).
* Medians in ms; source entries show offset 0 / offset 20.

| Service | Unfiltered | Account | Settlement Point | Combined |
| --- | ---: | ---: | ---: | ---: |
| metadata | 710.64 | 308.78 | — | — |
| summary | 1658.49 | 0.36 | 46.75 | 23.71 |
| sources | 1312.00 / 1408.19 | 179.64 / 280.92 | 435.86 / 323.79 | 187.77 / 175.30 |
| sinks | 175.38 | 153.02 | 192.73 | 138.01 |
| contracts | 11.89 | 4.51 | 9.95 | 5.81 |

* Recheck: timing increases did not persist; all 16 responses match.
  Combined summary: 20.80 ms; statistics did not resolve its access-choice issue.
* Captures: `/tmp/0013-query-performance/task-5/` and `task-5-recheck/` on host
  and API container. Diff check: passed.

### Task 6 — shared point aggregation

* API suite: 20 tests passed. Diff check: passed.
* Four responses match task 5; baseline MWh differences remain within tolerance
  (maximum `1.1920928955078125e-7`).
* Medians in ms:

| Summary filter | Baseline | Task 5 | Task 6 |
| --- | ---: | ---: | ---: |
| Unfiltered | 9792.94 | 1658.49 | 946.33 |
| Account | 0.79 | 0.36 | 0.20 |
| Settlement Point | 6072.56 | 46.75 | 25.02 |
| Combined | 0.54 | 23.71 | 11.21 |

* Captures: `/tmp/0013-query-performance/task-6/` on host and API container.

### Task 7 — indexed timeline endpoints

* Dataset test, Docker rebuild, validation, and 20 API tests: passed.
* All 12 affected responses match baseline and task 5 exactly.
* Timings improved across all measured source and sink workloads.
* Medians in ms; source entries show offset 0 / offset 20.

| Service / filter | Baseline | Task 5 | Task 7 |
| --- | ---: | ---: | ---: |
| sources / Unfiltered | 2158.83 / 2193.36 | 1312.00 / 1408.19 | 1032.45 / 995.16 |
| sources / Account | 138.01 / 124.61 | 179.64 / 280.92 | 0.56 / 0.25 |
| sources / Settlement Point | 1967.38 / 1728.54 | 435.86 / 323.79 | 110.76 / 107.35 |
| sources / Combined | 133.13 / 163.13 | 187.77 / 175.30 | 22.75 / 21.80 |
| sinks / Unfiltered | 2423.01 | 175.38 | 17.03 |
| sinks / Account | 158.61 | 153.02 | 0.26 |
| sinks / Settlement Point | 2438.49 | 192.73 | 17.53 |
| sinks / Combined | 132.86 | 138.01 | 0.25 |

* Captures: `/tmp/0013-query-performance/task-7/` on host and API container.
  Diff check: passed.

### Task 8 — aggregate source rankings

* API suite: 20 tests passed. Diff check: passed.
* Eight responses match baseline and task 7 within MWh tolerance
  (maximum difference `1.4901161193847656e-8`); ordering and pagination unchanged.
* Medians in ms; entries show offset 0 / offset 20.

| Source filter | Baseline | Task 7 | Task 8 |
| --- | ---: | ---: | ---: |
| Unfiltered | 2158.83 / 2193.36 | 1032.45 / 995.16 | 488.19 / 485.96 |
| Account | 138.01 / 124.61 | 0.56 / 0.25 | 0.53 / 0.27 |
| Settlement Point | 1967.38 / 1728.54 | 110.76 / 107.35 | 88.60 / 86.10 |
| Combined | 133.13 / 163.13 | 22.75 / 21.80 | 28.01 / 30.08 |

* Combined-filter recheck: 24.71 / 25.59 ms.
* Captures: `/tmp/0013-query-performance/task-8/` and `task-8-recheck/` on host
  and API container.
