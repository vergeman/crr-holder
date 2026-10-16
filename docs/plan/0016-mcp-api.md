# 0016 - MCP API

Type: experiment
Branch: experiment/0016-mcp-api

## Goal

* Expose the five existing read-only query services as decorator-based MCP tools.

* Serve MCP alongside the HTTP API in the existing FastAPI process.

* Log tool usage, elapsed time, CPU time, and process memory without storing a
  second copy of service data.

## Context

* `api/routes.py` opens a read-only database connection and delegates to Python
  services. `api/models.py` defines the existing response contracts.

* MCP tools reuse the existing Python services directly, without an internal
  HTTP round trip or a second implementation of query orchestration.

* `api/timing.py` already provides optional service timing through `@timed` and
  `ENABLED_TIMED`. MCP usage logging measures the tool invocation separately.

## Approach

### 1. MCP tools and FastAPI integration

* Add the official Python `mcp` SDK to `api/requirements.txt`, pinned to a verified
  stable release compatible with Python 3.12 and the existing FastAPI stack.
  Current documentation uses `MCPServer` and `@mcp.tool()`; use the API of the
  pinned release consistently. The package currently publishes 2.3.0 on
  [PyPI](https://pypi.org/project/mcp/).

* Add `api/mcp_server.py` for one server and five thin tool adapters. Avoid naming
  the module `mcp.py`, which would shadow the dependency. Each adapter opens the
  existing `open_database()` context, calls its service, and returns the existing
  Pydantic response model. Keep SQL and response assembly inside the services.

  | MCP tool | Existing service | Response model |
  | --- | --- | --- |
  | `get_metadata` | `services.metadata.get_metadata` | `Metadata` |
  | `get_summary` | `services.summary.get_summary` | `Summary` |
  | `get_source_holdings` | `services.crr_holdings.get_source_holdings` | `SourceHoldings` |
  | `get_sink_holdings` | `services.crr_holdings.get_sink_holdings` | `SinkHoldings` |
  | `get_contract_holdings` | `services.crr_holdings.get_contract_holdings` | `ContractHoldings` |

* Register tools with decorators, concise descriptions, typed parameters, and
  read-only annotations. Reuse response models for structured output; do not
  compose a separate prose version of the returned data.

* Match existing route parameters, defaults, optional-filter behavior, source
  pagination, hedge types, and delivery-month constraints. Move delivery-month
  validation and constrained input type aliases into `api/models.py` only where
  needed by both adapters. Use plain defaults with Pydantic annotations; do not
  pass FastAPI `Query` default objects to services or MCP tools. Keep HTTP paths,
  operation IDs, and response contracts unchanged.

* Use the SDK's worker-thread support for synchronous tools. Confirm the pinned
  implementation offloads them; if necessary, use an async adapter that awaits
  a worker-thread call. Create, use, and close each SQLite connection in that
  same thread. Do not run blocking SQLite work on the ASGI event loop.

* Update `api/main.py` to serve stateless Streamable HTTP at `/mcp/` on port 8000,
  alongside `/api/*`. Set the MCP application's inner path to `/` and mount it
  under `/mcp`. Start its session manager in FastAPI's lifespan and shut it down
  with the application. Do not start another server or container.

* Use MCP tool errors for failed invocations and SDK validation errors for
  invalid inputs. Preserve empty successful responses and source `nextOffset`.
  Add no arbitrary SQL execution tool or automatic retry logic.

### 2. Usage and resource logging

* Keep `@timed` unchanged and add a separate MCP decorator. Service timing is
  shared by HTTP and MCP callers; MCP usage records include connection setup,
  model conversion, invocation status, and resource samples. Keep those
  responsibilities and their logging controls separate.

* Add `api/mcp_usage.py` with one synchronous `@logged_tool` decorator preserving
  the wrapped signature. Place it inside `@mcp.tool()` so registration sees the
  typed signature and execution is measured in the service's worker thread.

* Emit one INFO completion record per dispatched tool invocation through the
  existing `uvicorn.error` logger. Record `tool`, normalized `parameters`,
  `status` (`success` or `error`), `elapsed_ms`, `cpu_ms`, `rss_before_bytes`, and
  `rss_after_bytes`. On failure also record the exception class as `error_type`.
  Do not log response contents, SQL, credentials, or exception messages.

* Include the subsequently requested `input_payload_bytes` and
  `output_payload_bytes`: compact UTF-8 JSON sizes of normalized arguments and
  the response model. Failed calls have null output size. These exclude
  MCP/HTTP framing and compression and do not measure network bandwidth.

* Use `perf_counter()` for elapsed time and `thread_time()` for execution-thread
  CPU time. Sample process RSS with `psutil`; add one pinned compatible dependency
  for current resident memory. Finish measurements and log in `finally`, then
  preserve the return value or propagate the original exception.

* Document that CPU milliseconds measure the invocation thread, while RSS is
  shared process memory at two instants. These are not per-customer memory,
  peak memory, or isolated CPU attribution across worker threads. Schema failures
  rejected before dispatch are outside these invocation logs. Log counts measure
  dispatched calls, not billable operations or unique user questions.

* Enable these MCP usage logs by default. Leave `@timed` and its environment
  toggle unchanged; enabling it adds the existing service-level timings.
  Store no usage table, account identity, billing ledger, or log output files.

### 3. Tests and connection documentation

* Add `api/tests/test_mcp.py` using the existing unittest runner, SDK client, and
  fixture data. Exercise the mounted ASGI application with its lifespan using
  the pinned SDK's supported HTTP test transport, or a temporary local Uvicorn
  server if required for streaming. Use existing dependencies and standard-library
  helpers. Reuse response fixtures without regenerating baselines.

* Check discovery and structured output for the five tools against existing
  services, including source pagination. Check shared input constraints and
  tool-error behavior so MCP does not silently bypass route validation.

* Check usage records on a successful and failed dispatched call. Assert field
  presence and valid units, without CPU, memory, or latency thresholds. Ensure
  validation errors do not invoke services. Check HTTP routes and OpenAPI remain
  accessible when the MCP app is mounted.

* Update `README.md` with `http://localhost:8000/mcp/`, a remote Streamable HTTP
  client configuration, tool names, a metadata-to-contract drill-down example,
  and log field meanings. Describe local development access only; hosted
  authentication, public deployment, and billing are separate work.

## Commit groups

1. `feat(api): expose holdings services through MCP` — dependency, tools,
   shared input constraints, FastAPI mount/lifespan, and protocol tests.

2. `feat(api): log MCP usage and resource measurements` — logging decorator,
   psutil dependency, and focused logging checks.

3. `docs: document MCP access and verification` — connection instructions and
   verified plan results. Keep any formatting-only changes separate.

## Scope control

* Use the smallest implementation that satisfies this plan. Treat acceptance
  criteria and verification as closed lists.

* Limit implementation to the API adapters, shared validation, application
  startup, dependencies, focused tests, and connection documentation. Keep
  service SQL, database schema, HTTP response shapes, and frontend unchanged.

* Add no MCP resources or prompts, caching, generic transport framework,
  pricing enforcement, authentication system, metrics
  dashboard, background sampler, or persistent usage storage.

* Before adding unplanned stored data, files, dependencies, or substantial
  verification steps, explain why, explicitly prompt the user for a scope
  decision, and wait for their reply. Existing authorization covers the work
  specified here. Resolve routine implementation choices directly.

## Verification

* Protocol integration checks confirm discoverable tools execute existing
  services and return their structured responses. Validation and logging checks
  confirm the new interface enforces its contract and produces usable records.

* Inspect Compose configuration and `docker compose ps` before using development
  services. Reuse running services. Install the planned API dependencies in the
  existing development service as needed; rebuild or recreate only if required.

* Run once after implementation:

  ```sh
  docker compose exec -T api python -m unittest discover -s tests -v
  docker compose exec -T api python -m pip check
  git diff --check
  ```

* Perform one SDK-client smoke check against `http://localhost:8000/mcp/`:
  initialize, list tools, and call metadata. Document the exact command with the
  implementation. No market-wide benchmark or client compatibility matrix.

## Acceptance

* [x] `/mcp/` initializes and lists exactly the five read-only tools alongside
  working HTTP routes in the same FastAPI application.

* [x] Tools reuse existing services and response models, preserve input
  constraints and pagination, and introduce no duplicate SQL or response assembly.

* [x] SQLite connections stay within worker threads; application lifespan owns
  MCP startup and shutdown.

* [x] Dispatched tool calls emit the specified usage, timing, CPU, and RSS fields
  on success or failure, with measurement limits documented.

* [x] Required API tests, dependency checks, and the mounted HTTP smoke check
  pass without regenerating response fixtures.

* [x] Connection instructions and the finite verification results are recorded.

## Verified results

* API unittest discovery: passed, 21 tests; response fixtures unchanged.
* `docker compose exec -T api python -m pip check`: passed.
* `git diff --check`: passed.
* Mounted HTTP SDK smoke check: passed; initialized `/mcp/`, discovered exactly
  five tools, and returned metadata for report 1. Exact command is recorded in
  [README.md](../../README.md).
* Reused the running API service with Python 3.12, FastAPI 0.143.0, and
  Starlette 1.8.0; installed `mcp==2.3.0` and `psutil==7.2.2` without recreating
  containers. SDK source confirms synchronous dispatch uses
  `anyio.to_thread.run_sync`; protocol fixtures execute SQLite within workers.
* Tests use the SDK's `streamable_http_client` with its supported `httpx2`
  client injection and ASGI transport, entering the mounted application's
  lifespan explicitly.

## References

* [Official SDK tools and decorators](https://py.sdk.modelcontextprotocol.io/servers/tools/)

* [Official SDK structured output](https://py.sdk.modelcontextprotocol.io/servers/structured-output/)

* [Official SDK mounting and lifespan](https://py.sdk.modelcontextprotocol.io/run/asgi/)

* [FastMCP alternative: FastAPI generation and mounting](https://gofastmcp.com/integrations/fastapi)
  supports converting an existing API, but this plan uses explicit tool adapters
  for descriptions and logging while keeping service logic shared.
