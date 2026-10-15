# 0012 - Service Timing

Type: feat
Branch: feat/0012-service-timing

## Goal

* Add a reusable `@timed` decorator for synchronous service functions.

* Log the function name, arguments, and elapsed milliseconds when
  `ENABLED_TIMED=1`; disable timing by default.

## Context

* The database performance experiment found SQL dominated service time;
  one duration covering SQL, fetching, and Python is sufficient here.

* Routes open database connections before calling services. Decorating services
  excludes connection setup, cleanup, and FastAPI processing.

* Keep instrumentation to imports and annotations, without changing queries or
  how results are consumed.

## Tasks and commit groups

Implement in order as four commits.

### 1. Environment toggle

Commit: `feat: add service timing environment toggle`

* Add `ENABLED_TIMED: "${ENABLED_TIMED:-0}"` to the API environment in
  `docker-compose.yml`. Changing the setting requires recreating the API
  container; no image rebuild is needed for this setting.

### 2. Timing decorator and tests

Commit: `feat: add timing decorator with tests`

* Add `api/timing.py` exposing `timed`. Use only the standard library:
  `functools.wraps`, `inspect.signature`, `logging`, `os`, and
  `time.perf_counter`.

* Read `ENABLED_TIMED` once at module import. Enable only for the value `1`;
  when disabled, return the original function without a timing wrapper.

* Capture the signature when decorating. On enabled calls, bind positional and
  keyword arguments to their names and include default values. Log all arguments
  uniformly; derive argument names automatically as signatures change.

* Capture arguments before starting the timer. Time the function invocation and
  emit one INFO log in `finally`, retaining its return value or exception.
  Use the existing `uvicorn.error` logger so output appears in API container
  logs without additional logging configuration.

* Log `function_name parameters={...} elapsed_ms=...`, using argument repr and
  milliseconds with two decimal places. Do not log results or SQL.

* Use this log message format (Uvicorn adds its usual INFO prefix):

  ```text
  get_source_holdings parameters={'db': <sqlite3.Connection object at 0x...>, 'report_id': 1, 'account_holder': None, 'settlement_point': 'HB_NORTH', 'limit': 20, 'offset': 0} elapsed_ms=255.40
  ```

  The first field is the decorated function's name. `parameters` is a Python
  dictionary representation of its named arguments in signature order, including
  defaults. Values reflect inputs to the call, before the
  service resolves or modifies them. `elapsed_ms` is elapsed wall-clock time
  covering the service's SQL, fetching, and Python processing, excluding argument
  capture and log emission. Emit the same format if the function raises, then
  propagate the exception; do not add a separate status or exception field.

* Add one integration test in `api/tests/test_timing.py` using an existing
  fixture database and a real service call. With timing enabled, check that
  the service returns its expected response and logs its name, arguments,
  and elapsed milliseconds. This test exercises the service
  annotation added in commit 3. Add no decorator unit tests, exception cases,
  argument permutations, or clock mocks; do not assert timing thresholds.

### 3. Service annotations

Commit: `feat: enable timing annotations on service entry points`

* Import and apply `@timed` to `get_metadata` in `api/services/metadata.py`,
  `get_summary` in `api/services/summary.py`, and `get_source_holdings`,
  `get_sink_holdings`, and `get_contract_holdings` in
  `api/services/holdings.py`.

### 4. Verification

Commit: `docs: record service timing verification`

* Run the commands in Verification below. Update acceptance checkboxes from
  verified results and record terse check/outcome bullets in this plan.

* Fold any fixes into the appropriate implementation commit above; keep this
  fourth commit limited to the plan's verification record.

## Scope control

* Limit changes to the new timing module and test, the three service modules,
  the API environment setting in Compose, and this plan's verification record.

* Support ordinary synchronous functions only. Add no connection wrappers,
  generator or async support, profiling hooks, per-query timing, response
  headers, dependencies, or output files.

* Use the smallest implementation that satisfies the acceptance criteria.
  Treat acceptance criteria and verification as closed lists.

* Before adding unplanned stored data, files, dependencies, or substantial
  verification steps, explain why, explicitly prompt the user for a scope
  decision, and wait for their reply. Existing authorization covers work
  specified in this plan. Resolve routine implementation choices directly.

## Acceptance

* [x] The five service entry points use `@timed`; routes, database connection
  handling, SQL, and response assembly are unchanged.

* [x] With `ENABLED_TIMED=1`, each decorated invocation logs its function name,
  all named arguments, and combined service duration in milliseconds.
  Both positional and keyword calls are captured without maintained field lists.

* [x] With `ENABLED_TIMED=0` or unset, decoration returns the original function
  and emits no timing logs.

* [x] Enabled decoration preserves function metadata, return values, and
  exceptions, and logs elapsed time when the function raises.

* [x] Compose passes the toggle to the API service and defaults it to `0`.

## Verification

* Run the single timing integration test as part of the existing API suite to
  check real service output and timing logs. Validate Compose configuration.
  Review the disabled path directly; add no separate toggle test matrix.

* Inspect `docker-compose.yml` and run `docker compose ps` before using services.
  Reuse the running API service. Run the suite once with timing enabled:

  ```sh
  docker compose exec -T -e ENABLED_TIMED=1 api python -m unittest discover -s tests -v
  docker compose config --quiet
  git diff --check
  ```

* No performance benchmark or container recreation is required for verification;
  the test command supplies the toggle to a fresh Python process.

## Verification results

* API suite with `ENABLED_TIMED=1`: passed all 19 tests, including the timing
  integration test, using the running API container.
* `docker compose config --quiet`: passed; existing obsolete `version` warning.
* `git diff --check`: passed.
* Direct review: disabled decoration returns the original function; enabled
  decoration captures named inputs and defaults before timing, preserves metadata
  and return values, and logs in `finally` while propagating exceptions.
* Service diff review: only timing imports and annotations changed; routes,
  connection handling, SQL, and response assembly are unchanged.
