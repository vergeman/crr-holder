# 0017 - Transcrypt Browser Services

Type: feat
Branch: feat/0017-transcrypt-browser-services
Base: master
Status: implemented

Depends on: [0014 - Service Query Boundaries](0014-service-query-boundaries.md)

## Goal

Generate all five browser query services from Python, preserving inline SQL,
query orchestration, and response assembly. Reuse 0015's WASM, HTTP range VFS,
and provider selector to compare browser execution with the API.

## Context

- Start from `master`; exclude 0015's SQL extraction and MCP changes.
- Reuse transport commit `430f15c` from `experiment/0015-shared-service-sql`.
- The Transcrypt 3.9.4 source-holdings pilot passed fixture and real-data checks.
  Restoring master's SQL changed bounds timing independently of compilation.
- VFS's initial market-wide metadata scan did not complete. Document this
  limitation without repeating that scan.

## Implementation

1. **Generate services.** Keep `api/services/` authoritative, including master's
   SQL strategies. Add `api/browser/build.py`, `entry.py`, `stubs/`, and
   `requirements.txt` pinning `Transcrypt==3.9.4`. Compile staged modules in a
   temporary directory, excluding FastAPI/Pydantic routes. Stub only server
   timing and `sqlite3.Connection`; make necessary compatibility changes in
   shared Python.

2. **Export artifacts.** Add `scripts/generate-browser-services.sh` to compile in
   the existing API container and stream output to ignored
   `web/src/generated/transcrypt/`, separate from Orval. Fail on compiler errors.
   Require explicit generation before frontend development/build and after
   Python changes; add no watcher, compiler endpoint, or shared volume.

3. **Reuse browser transport.** Apply and adapt `430f15c` before committing.
   Retain database GET/HEAD/ranges, pinned SQLite runtimes, cancellation, Vite
   configuration, provider selector, and all five per-method overrides. Remove
   SQL-file routes and worker SQL fetching from `api/wasm.py` and the worker.

4. **Connect generated code.** Add `web/src/data/sqliteAdapter.js` supporting
   `execute`, iterable rows, `fetchone`, `fetchall`, and named/positional/omitted
   parameters for both engines. Replace handwritten worker services with
   generated calls. Keep runtime/database setup, dispatch, timing, and result
   normalization/transfer in JavaScript. Retain one read-only database/worker
   per provider session, with WASM as the default.

## Commit groups

1. `feat(browser): generate query services with Transcrypt` — compiler,
   generator, entry point, stubs, and Python compatibility changes.
2. `feat(web): run generated services through WASM and HTTP VFS` — adapted
   transport, adapter, worker, selector, and transport tests.
3. `test(browser): verify generated service parity` — fixtures, real-data
   comparisons, interactions, and fixed-sample measurements.
4. `docs: document generated browser services` — setup, generation, results,
   and limitations.

Keep generated modules and raw captures out of Git. Keep formatting-only changes
in separate commits immediately after the related refactor.

## Verification

- Run API tests against unchanged response baselines.
- Add `web/tests/check-browser-services.py` using existing Chromium/CDP and the
  available Python WebSocket client. Compare all five generated services with
  fixtures and HTTP responses using existing measurement workloads. Cover source
  pagination, contract grouping, empty/omitted filters, and cancellation.
- Check source expansion, contract details, and HTTP/WASM switching on desktop
  and narrow screens. Browser queries must not fall back to holdings API calls.
- Retain HEAD/range tests; run one indexed real-data VFS query through generated
  code, bypassing the initial metadata scan.
- Measure download, runtime/database initialization, and warmed worker round
  trips separately. Compare with API service timings using existing inputs and
  fixed sampling; distinguish SQL effects from compiler overhead. Keep captures
  in `/tmp`.

Inspect Compose configuration and `docker compose ps`; reuse running services.
The browser checker uses a configurable existing CDP session and includes timing.
Add no browser framework or downloads; repeat checks only for failures or relevant
changes.

```sh
bash scripts/generate-browser-services.sh
docker compose exec -T api python -m unittest discover -s tests -v
python3 web/tests/check-browser-services.py
docker compose exec -T -e ENABLED_TIMED=1 api python tests/measure_services.py --label 0017-transcrypt
docker compose exec -T web npx vite build
docker compose exec -T web npx --no-install prettier --trailing-comma es5 --check \
  src/data/sqlite.worker.js src/data/sqliteAdapter.js src/data/wasmProvider.js \
  src/data/provider.js src/components/portfolio/DataProviderSelect.jsx
git diff --check
```

## Scope

Acceptance and verification are closed lists. Preserve HTTP paths/models, dataset
preparation, schema, SQL strategies, React hooks, and feature layout. Exclude SQL
extraction, handwritten JavaScript services, persistent browser caching, MCP,
authentication/billing, and alternate Python runtimes. Ask before adding unplanned
files, dependencies, stored data, or substantial verification.

## Acceptance

- [x] Repeatable generation of all five services, including inline SQL and
  response assembly, without handwritten browser equivalents.
- [x] API and browser parity against unchanged baselines, including ordering,
  pagination, filters, and contract grouping.
- [x] WASM and VFS use generated services through one shared SQLite adapter.
- [x] Provider overrides, desktop/narrow drill-downs, and HTTP/WASM switching pass.
- [x] Range transport and an indexed generated VFS query pass; document the
  unresolved metadata-scan limitation.
- [x] Document generation, setup/query measurements, and material compatibility
  or performance limitations.

## Results

- API tests: 23 passed. Browser fixtures: 38 passed; real-data workloads: 22 passed.
- Desktop/narrow drill-downs, switching, overrides, and cancellation: passed.
- Generation, production build, Prettier, and whitespace checks: passed. The build
  retains the existing large-chunk warning.

Local medians in milliseconds, using one warm-up and three samples:

| Service / filter | API service | WASM worker round trip |
| --- | ---: | ---: |
| Metadata / market | 1127.8 | 697.5 |
| Metadata / account | 427.2 | 429.4 |
| Summary / market | 1606.8 | 1307.1 |
| Summary / account | 0.2 | 2.0 |
| Sources, page 1 / market | 649.9 | 280.0 |
| Sources, page 1 / account | 0.7 | 4.6 |
| Sinks / market | 22.0 | 58.3 |
| Sinks / account | 0.6 | 1.4 |
| Contracts / market | 11.2 | 36.1 |
| Contracts / account | 8.0 | 5.3 |

The 398,688,256-byte download took 4.72 s; SQLite initialization took 52.6 ms and
opening/deserialization 310.0 ms. These exclude browser module loading and are
not total page-load measurements.

Median Python orchestration/assembly ranged from 0.1–28.1 ms across workloads.
The combined-filter source query spent 26.5 ms in the SQL adapter and 0.5 ms in
orchestration (27.4 ms round trip). SQL timing includes binding, row conversion,
and finalization. SQL strategies remain unchanged from master; 0015's faster
NULL-guard variant was not adopted. Different SQLite versions, processes, and
cache states mean these API/WASM timings do not isolate compiler overhead or
establish a universal speed advantage. API timings exclude HTTP transport.

The indexed generated VFS contract query matched the API in 6.22 s. The initial
market-wide metadata scan remains unresolved and was not repeated.
Raw captures remain in `/tmp/0017-browser-services/` and API-container
`/tmp/0013-query-performance/0017-transcrypt/`.
