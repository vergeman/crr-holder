# 0015 - Experimental Shared Service SQL

Type: experiment
Branch: experiment/0015-shared-service-sql
Status: all five query methods converted; VFS performance trial remains stopped

Depends on: [0014 - Service Query Boundaries](0014-service-query-boundaries.md)

## Goal

Evaluate shared SQL and browser SQLite execution against the existing Python
services, including full-download WASM and HTTP range VFS providers.

## Implemented scope

* Extract complete source-holdings, sink-holdings, contract-details, metadata,
  summary, report-resolution, and delivery-month statements into `api/sql/`,
  with a cached Python loader.
* Bind source lists as JSON through `json_each(:sources)`. Trial nullable optional
  account predicates and retain direct-account statement variants where the
  nullable form prevents efficient indexed lookups.
* Serve the existing database and shared SQL through the API. Support HEAD and
  byte-range requests for the VFS experiment.
* Add browser query orchestration and response assembly for metadata, summary,
  source holdings, sink expansion, and contract details, sharing a worker
  within each browser provider.
* Compare full-download WASM, HTTP VFS, and HTTP API using a header selector and
  URL parameters. All five methods use the selected provider.

## Findings and stopping point

* Full-download WASM works, with the cost of downloading the complete database
  before the first query.
* Sharing SQL still requires JavaScript copies of Python query orchestration,
  parameter preparation, and response assembly. This maintenance cost limits
  the appeal of expanding browser execution.
* Direct-account variants improve indexed account queries. The report-wide
  account-holder metadata scan remains expensive.
* Indexed VFS queries work, but the initial real-market metadata scan generated
  thousands of small HTTP range requests and did not finish during the trial.
  Further VFS browser testing was canceled at the user's request.
* Browser expansion resumed at the user's request to finish the conversion.
  Keep this branch experimental. Full-download WASM remains its current default;
  the selector retains HTTP and VFS comparisons. MCP is outside this experiment.

Statement contracts, measurements, and detailed validation results are recorded
in [the shared SQL notes](../../api/sql/README.md). Provider setup is documented
in [the frontend notes](../../web/src/README.md).

## Commit groups

1. Metadata extraction, including the shared SQL loader and report resolution.
2. Summary extraction, including metrics, account rankings, and point totals.
3. Source-holdings extraction, including the shared delivery-month timeline.
4. Sink-holdings extraction, including rankings and monthly cells.
5. Contract-details extraction, including original segment queries.
6. Database and SQL endpoints, browser WASM/VFS providers, provider selector,
   dependencies, and database transport tests.
7. Experiment plan, SQL contracts and measurements, and provider documentation.

Keep formatting-only changes separate. Do not regenerate response baselines or
commit raw timing captures.

## Verification

Existing API fixtures check unchanged responses. Query-plan and timing
comparisons assess JSON binding and optional filters. Browser checks compare
responses and interactions, while transport tests verify database range access.
VFS fixture checks with simulated range responses do not establish real-market
scan performance.

Required commands used for the implementation:

```sh
docker compose exec -T api python -m unittest discover -s tests -v
docker compose exec -T web npx vite build
git diff --check
```

Existing service measurements used:

```sh
docker compose exec -T -e ENABLED_TIMED=1 api python tests/measure_services.py --label 0015-<stage>
```

## Results

* API tests: 23 passed; response baselines retained.
* Browser response comparisons and desktop/narrow interactions: passed for
  completed checks documented in the SQL notes.
* Production build and Prettier: passed; existing large-chunk warning remains.
* Real-market initial VFS metadata load: incomplete; testing canceled.
* Completed conversion: all eight real-database sink/contract service responses
  unchanged; 14 WASM/HTTP comparisons and 13 committed browser fixtures passed.
* Completed conversion: desktop/narrow drill-downs and HTTP/WASM provider
  switching passed. No further real-market VFS trial was performed.
