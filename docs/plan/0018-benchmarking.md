# 0018 - Provider Benchmarking

Type: feat
Branch: feat/0018-benchmarking

## Goal

Compare HTTP, WASM and VFS at `/benchmark.html`, with timings, download totals
and JSON export.

## Approach

- Development-only page; provider switching without navigation or map loading.
- Query the actual `DB_FILE`: HTTP on the server, WASM from a full download,
  VFS through database range requests.
- Share fixed request parameters from
  `web/src/components/benchmark/measurement_inputs.json`.
- Capture HTTP references; run a first pass, one warm-up and three measured
  passes by default. Compare responses outside timed calls.
- Configurable API latency, default 50 ms; normal app requests are unaffected.
- Automatically preload WASM once, with progress and Stop; reuse the buffer.
- Default timeout: 10 seconds. Query timeouts release workers and continue to
  the next service; initialization timeouts end the run.
- Gzip JSON and full database downloads; leave HEAD/range responses uncompressed.
- Retain startup, first-pass and warm timings, median/p95, failures and download
  totals. Export JSON; keep results in memory. Support narrow screens.

## Benchmark suite

- 22 calls/pass: metadata 2, summary 4, sources 8, sinks 4, contracts 4.
- Filters: market, account, point and combined; metadata uses market/account only.
- Source pagination: offsets 0 and 20, limit 20.
- Sink and contract drill-downs use the shared request parameters.

## Implementation

- Group benchmark components under `web/src/components/benchmark/`; keep the
  page entry focused on state and run coordination.
- Reuse HTTP services; create isolated WASM/VFS providers with explicit
  initialization, timing access and worker disposal.
- Preload WASM outside the operation timeout and without added latency. Apply
  configurable latency in Vite only to benchmark HTTP and VFS requests.
- After a query timeout, skip that service's remaining variants and passes.
  Initialize a fresh worker for the next service; classify its first call
  separately from warm samples. Skip services with failed HTTP references.
- Measure client calls and worker service/SQL/normalization timings. Exclude
  first calls and warm-up from warm statistics.
- Count compressed response-body bytes, including warm-up and completed VFS
  ranges; exclude reference requests, headers and page assets. Count one WASM
  preload per comparison. Interrupted responses may omit partial bytes.
- Retain raw byte counts and decoded database size; display MB and seconds.
- Add no dependencies, persistence, router or reusable benchmark framework.

## Commit groups

1. Basic page.
2. Provider selection, services, lifecycle and timings.
3. Controls, suite, comparisons, timeout recovery and tests.
4. Results, retained runs and export.
5. Actual runs and documentation.

Fold follow-ups into their related commits; keep formatting changes separate
and consolidate plan updates in the final docs commit.

## Acceptance

- [x] All three providers run without navigation or map loading.
- [x] Five services and filters covered; parity failures visible.
- [x] Startup, first-pass and warm results retained and exported.
- [x] Stop/timeout releases workers; controls and results work on narrow screens.

## Microbenchmark results

Ran HTTP, WASM and VFS sequentially at 50, 100 and 150 ms added API latency,
with gzip, 22 workloads, one first pass, one warm-up and three measured passes.
HTTP and WASM matched all responses. VFS timed out on all five services at every
latency, completing no workloads.

| API latency | HTTP warm mean/call | WASM warm mean/call | VFS downloaded |
| --- | --- | --- | --- |
| 50 ms | 169.3 ms | 123.1 ms | 6.350 MB |
| 100 ms | 191.2 ms | 101.8 ms | 3.061 MB |
| 150 ms | 250.8 ms | 105.3 ms | 2.192 MB |

- HTTP: 0.665 MB over 110 calls/run, averaging 6.045 KB/call.
- WASM: 85.107 MB compressed, 398.688 MB decoded; download 16.478 s,
  initialization 0.648–0.914 s, zero query-download bytes.
- Projected time crossover: ~380/~195/~125 calls at 50/100/150 ms.
  Projected data crossover: ~14,100 calls. These sequential microbenchmark
  estimates are not app-session thresholds.
