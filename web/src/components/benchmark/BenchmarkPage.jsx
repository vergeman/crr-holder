import React, { useEffect, useRef, useState } from "react";
import inputs from "./measurement_inputs.json";
import { httpProvider } from "../../data/provider";
import { createProvider, downloadDatabase } from "../../data/wasmProvider";
import { createSuite } from "./suite";
import { runBenchmark } from "./runner";

const suite = createSuite(inputs);

export function BenchmarkPage() {
  const [provider, setProvider] = useState("http");
  const [timeoutSeconds, setTimeoutSeconds] = useState(10);
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
      setProgress("Database preloaded; shaping can now be enabled");
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
        httpProvider,
        createProvider: (backend) => createProvider(backend, preloaded),
        preloadedDownload:
          provider === "wasm" ? preloaded?.download : undefined,
        networkLabel,
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
            timeoutSeconds < 1 || passes < 1 || !Number.isInteger(passes)
          }
        >
          Run benchmark
        </button>
      </fieldset>
      <button disabled={!running} onClick={() => controller.current.abort()}>
        Stop
      </button>
      <p role="status">{progress}</p>
      <p>{runs.length} retained runs</p>
    </main>
  );
}
