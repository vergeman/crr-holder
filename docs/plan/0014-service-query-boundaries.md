# 0014 - Service Query Boundaries

Type: refactor
Branch: refactor/0014-service-query-boundaries

Depends on: [0013 - Query Performance](0013-query-performance.md)

## Goal

* Organize services by frontend feature and drill-down level.

* Separate service coordination, SQL operations, and response transformations
  through named function wrappers without changing query strategies.

## Context

* The optimized 0013 queries are the behavioral and performance baseline.

* Review began with source holdings, then covered sink holdings, contract
  details, metadata, and summary. SQL remains embedded in Python for this plan.

## Approach

* Group summary coordination, metrics, and rankings under `api/services/summary/`:
  `summary.py`, `top_account_holders.py`, and `top_settlement_points.py`.
  Export `get_summary` through the package's `__init__.py`.

* Split holdings into `api/services/crr_holdings/`: `source_holdings.py`,
  `sink_holdings.py`, and `contract_holdings.py`. Export the existing service
  entry points through `__init__.py`; update route, test, and measurement imports.
  Keep the shared delivery-month query in the package's `helpers.py`.

* Wrap SQL construction and execution in `_query_*` functions with explicit
  inputs and returned-column documentation. Keep public service functions as
  coordinators; use pure helpers for substantial response transformations.
  Prefix module-local helpers with `_`; keep cross-module functions public.

* Apply the query wrappers to holdings, metadata, and summary. Document usage
  and existing optimizations in `api/services/helpers.py`.

* Document service endpoints and their frontend consumers: metadata bootstrap
  and dropdowns; Portfolio Summary, Discover, and map totals; source initial
  load, sink expansion, and the contract-details modal.

## Commit groups

* Summary package and query wrappers: `9212a98`.

* CRR holdings package, query wrappers, response helpers, and imports: `1f9e21e`.

* Metadata query wrappers and bootstrap documentation: `5bfb8d4`.

* Shared-helper usage and optimization documentation: `31e0f85`.

* Finalize this plan and record deferred SQL extraction in 0015. Keep
  formatting-only changes separate.

## Scope control

* Preserve endpoint contracts, filters, calculations, ordering, pagination,
  optimized SQL strategies, and timing annotations.

* SQL extraction and cross-runtime parameter handling belong to
  [0015 - Shared Service SQL](0015-shared-service-sql.md). Add no ORM, browser
  implementation, schema changes, dependencies, or generic query framework here.

* Treat acceptance and verification as closed lists. Ask before adding unplanned
  files, stored data, dependencies, or substantial checks; resolve routine
  implementation choices within the agreed scope.

## Verification

* Use existing response fixtures and API tests to verify unchanged outputs,
  including rankings, filters, month cells, pagination, and contract grouping.
  Require exact decoded-JSON comparisons against optimized 0013 fixtures;
  do not regenerate baselines.

* Reuse running Compose services. Required commands:
  `docker compose exec -T api python -m unittest discover -s tests -v`
  and `git diff --check`.

* The separately requested performance comparison uses the existing 0013
  measurement runner and captures; add no new benchmark framework.

## Acceptance

* [x] Summary and CRR holdings are organized into feature packages with updated
  imports and documented frontend entry points.

* [x] Holdings, metadata, and summary use named SQL-operation wrappers and clear
  response assembly, retaining existing optimized query strategies.

* [x] Shared helpers document usage, optional filters, and summary-query
  optimizations.

* [x] Existing API tests, exact response comparisons, and diff checks pass.

## Validation results

* API regression suite: 20 tests passed, including exact response fixtures.

* Requested measurements: 22/22 responses matched optimized 0013 captures;
  no material performance regression established.

* `git diff --check`: passed.
