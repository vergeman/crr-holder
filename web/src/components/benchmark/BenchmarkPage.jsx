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
  const [networkLabel, setNetworkLabel] = useState("Unshaped");
  const [progress, setProgress] = useState("");
  const [running, setRunning] = useState(false);
  const controller = useRef();

  useEffect(() => () => controller.current?.abort(), []);

  async function preloadDatabase() {
    controller.current = new AbortController();
    setRunning(true);
    setProgress("Preloading WASM database without shaping");
    try {
      setPreloaded(await downloadDatabase(controller.current.signal));
      setProgress("Database preloaded; ready to benchmark");
    } catch (error) {
      setProgress(error.message);
    } finally {
      setRunning(false);
    }
  }

  async function startBenchmark() {
    controller.current = new AbortController();
    setRunning(true);
    try {
      const run = await runBenchmark({
        backend: provider,
        suite,
        httpProvider: createHttpProvider(latencyMs),
        createProvider: (backend) =>
          createProvider(backend, preloaded, latencyMs),
        preloadedDownload:
          provider === "wasm" && preloaded
            ? {
                ...preloaded.download,
                estimated100MbpsMs:
                  (preloaded.download.bytes * 8) / 100000 + latencyMs,
              }
            : undefined,
        networkLabel,
        latencyMs,
        timeoutMs: timeoutSeconds * 1000,
        passes,
        signal: controller.current.signal,
        onProgress: setProgress,
      });
      setRuns((previous) => [...previous, run]);
      setProgress(run.status);
    } finally {
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
        <label>
          Network profile
          <input
            value={networkLabel}
            onChange={(event) => setNetworkLabel(event.target.value)}
          />
        </label>
        <button onClick={preloadDatabase}>Preload WASM database</button>
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
        API latency applies only to benchmark requests during a run. Normal app
        requests and WASM preload have no added delay.
      </p>
      <button disabled={!running} onClick={() => controller.current.abort()}>
        Stop
      </button>
      <p role="status">{progress}</p>
      <BenchmarkResults runs={runs} preloaded={preloaded?.download} />
    </main>
  );
}
