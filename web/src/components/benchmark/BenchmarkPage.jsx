import React, { useEffect, useRef, useState } from "react";
import inputs from "./measurement_inputs.json";
import { createHttpProvider } from "../../data/provider";
import { createProvider, downloadDatabase } from "../../data/wasmProvider";
import { createSuite } from "./suite";
import { runBenchmark } from "./runner";
import { BenchmarkResults } from "./BenchmarkResults";
import "./benchmark.css";

const suite = createSuite(inputs);

export function BenchmarkPage() {
  const [provider, setProvider] = useState("http");
  const [timeoutSeconds, setTimeoutSeconds] = useState(10);
  const [latencyMs, setLatencyMs] = useState(50);
  const [passes, setPasses] = useState(3);
  const [runs, setRuns] = useState([]);
  const [preloaded, setPreloaded] = useState(null);
  const [progress, setProgress] = useState("");
  const [running, setRunning] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const controller = useRef();

  useEffect(() => () => controller.current?.abort(), []);

  async function startBenchmark() {
    controller.current = new AbortController();
    setRunning(true);
    try {
      let database = preloaded;
      if (provider === "wasm" && !database) {
        setDownloading(true);
        setProgress("Downloading WASM database before benchmarking");
        database = await downloadDatabase(controller.current.signal);
        setPreloaded(database);
        setDownloading(false);
      }
      controller.current.signal.throwIfAborted();

      const run = await runBenchmark({
        backend: provider,
        suite,
        httpProvider: createHttpProvider(latencyMs, true),
        createProvider: (backend) =>
          createProvider(backend, database, latencyMs, true),
        preloadedDownload:
          provider === "wasm" && database
            ? {
                ...database.download,
                estimated100MbpsMs:
                  (database.download.bytes * 8) / 100000 + latencyMs,
              }
            : undefined,
        latencyMs,
        timeoutMs: timeoutSeconds * 1000,
        passes,
        signal: controller.current.signal,
        onProgress: setProgress,
      });
      setRuns((previous) => [...previous, run]);
      setProgress(run.status);
    } catch (error) {
      setProgress(
        controller.current.signal.aborted
          ? "Stopped"
          : `Download failed: ${error.message}`
      );
    } finally {
      setDownloading(false);
      setRunning(false);
    }
  }

  return (
    <main>
      <h1>Provider benchmarks</h1>
      <p>
        Compare HTTP, WASM, and VFS service calls. {suite.length} workloads per
        pass.
      </p>
      <fieldset disabled={running}>
        <label>
          Provider
          <select
            value={provider}
            onChange={(event) => setProvider(event.target.value)}
          >
            <option value="http">HTTP</option>
            <option value="wasm">WASM</option>
            <option value="vfs">VFS</option>
          </select>
        </label>
        <label>
          Timeout (seconds)
          <input
            type="number"
            min="1"
            value={timeoutSeconds}
            onChange={(event) => setTimeoutSeconds(Number(event.target.value))}
          />
        </label>
        <label>
          Measured passes
          <input
            type="number"
            min="1"
            value={passes}
            onChange={(event) => setPasses(Number(event.target.value))}
          />
        </label>
        <label>
          API latency (ms)
          <input
            type="number"
            min="0"
            step="1"
            value={latencyMs}
            onChange={(event) => setLatencyMs(Number(event.target.value))}
          />
        </label>
        <button
          onClick={startBenchmark}
          disabled={
            timeoutSeconds < 1 ||
            passes < 1 ||
            !Number.isInteger(passes) ||
            latencyMs < 0 ||
            !Number.isSafeInteger(latencyMs)
          }
        >
          Run benchmark
        </button>
      </fieldset>
      <p>
        API latency is set above and applied in Vite’s proxy before each
        benchmark request. JSON responses and full database downloads use gzip;
        VFS range requests are uncompressed. Warm results measure repeated
        queries after the first pass and one warm-up pass. VFS cannot finish
        some endpoints within the timeout; those timeouts are expected.
      </p>
      <button disabled={!running} onClick={() => controller.current.abort()}>
        Stop
      </button>
      <p role="status">{progress}</p>
      {downloading && <progress aria-label="Downloading WASM database" />}
      <BenchmarkResults runs={runs} preloaded={preloaded?.download} />
    </main>
  );
}
