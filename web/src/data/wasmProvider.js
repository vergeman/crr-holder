export async function downloadDatabase(signal, latencyMs = 0) {
  const started = performance.now();
  const path =
    latencyMs > 0 ? `/api/_benchmark/${latencyMs}/database` : "/api/database";
  const url = new URL(path, window.location.origin).href;
  let recordTransfer;
  const transferred = new Promise((resolve) => {
    recordTransfer = resolve;
  });
  const observer = new PerformanceObserver((list) => {
    const entry = list
      .getEntries()
      .find((entry) => entry.name === url && entry.startTime >= started);
    if (entry) recordTransfer(entry.encodedBodySize);
  });
  // Streaming gzip has no Content-Length; the browser records encoded body bytes.
  observer.observe({ type: "resource" });

  try {
    const response = await fetch(url, { cache: "no-store", signal });
    if (!response.ok)
      throw new Error(`Database download failed: ${response.status}`);
    const buffer = await response.arrayBuffer();
    return {
      buffer,
      download: {
        bytes: await transferred,
        databaseBytes: buffer.byteLength,
        downloadMs: performance.now() - started,
      },
    };
  } finally {
    observer.disconnect();
  }
}

export function createProvider(
  backend,
  preloaded,
  latencyMs = 0,
  trackTransfer = false
) {
  const transferStats = { requests: 0, downloadBytes: 0 };
  let startup;
  let lastTimings;
  const lifetime = new AbortController();
  let worker;
  let database;
  let nextRequestId = 0;
  const requests = new Map();

  function getWorker() {
    if (worker) return worker;
    worker = new Worker(new URL("./sqlite.worker.js", import.meta.url), {
      type: "module",
    });
    worker.onmessage = ({ data: { id, result, error, timings, transfer } }) => {
      if (transfer) {
        transferStats.requests += transfer.requests;
        transferStats.downloadBytes += transfer.downloadBytes;
        return;
      }
      lastTimings = timings;
      const request = requests.get(id);
      if (!request) return;
      if (error) request.reject(new Error(error));
      else request.resolve(result ?? timings);
    };
    worker.onerror = (event) => {
      for (const request of requests.values())
        request.reject(new Error(event.message));
      worker.terminate();
      worker = undefined;
      database = undefined;
    };
    return worker;
  }

  function requestWorker(
    message,
    signal,
    ready = Promise.resolve(),
    transfer = []
  ) {
    signal?.throwIfAborted();
    return new Promise((resolve, reject) => {
      const id = ++nextRequestId;
      function finish(callback, value) {
        requests.delete(id);
        signal?.removeEventListener("abort", abort);
        callback(value);
      }
      function abort() {
        finish(reject, signal.reason);
      }
      requests.set(id, {
        resolve: (result) => finish(resolve, result),
        reject: (error) => finish(reject, error),
      });
      signal?.addEventListener("abort", abort, { once: true });
      ready.then(
        () => {
          if (!requests.has(id)) return;
          try {
            getWorker().postMessage({ id, ...message }, transfer);
          } catch (error) {
            finish(reject, error);
          }
        },
        (error) => finish(reject, error)
      );
    });
  }

  async function loadDatabase() {
    const initialized = performance.now();
    if (backend === "vfs") {
      const workerTimings = await requestWorker({
        backend,
        latencyMs,
        trackTransfer,
      });
      startup = {
        worker: workerTimings,
        totalMs: performance.now() - initialized,
      };
      return;
    }
    if (!preloaded) transferStats.requests++;
    const { buffer, download } = preloaded
      ? { buffer: preloaded.buffer.slice(0), download: preloaded.download }
      : await downloadDatabase(lifetime.signal, latencyMs);
    if (!preloaded) transferStats.downloadBytes += download.bytes;
    const workerTimings = await requestWorker(
      { buffer, backend },
      undefined,
      Promise.resolve(),
      [buffer]
    );
    startup = {
      download,
      preloaded: Boolean(preloaded),
      worker: workerTimings,
      totalMs: performance.now() - initialized,
    };
  }

  function execute(method, parameters, signal) {
    signal?.throwIfAborted();
    lifetime.signal.throwIfAborted();
    database ??= loadDatabase().catch((error) => {
      database = undefined;
      throw error;
    });
    return requestWorker({ method, parameters }, signal, database);
  }

  return {
    initialize() {
      lifetime.signal.throwIfAborted();
      database ??= loadDatabase();
      return database.then(() => startup);
    },
    getTimings: () => lastTimings,
    getTransferStats: () => ({ ...transferStats }),
    dispose() {
      lifetime.abort();
      for (const request of requests.values())
        request.reject(lifetime.signal.reason);
      worker?.terminate();
      worker = undefined;
      database = undefined;
    },
    getSourceHoldings: (parameters, signal) =>
      execute("getSourceHoldings", parameters, signal),
    getMetadata: (parameters, signal) =>
      execute("getMetadata", parameters, signal),
    getSummary: (parameters, signal) =>
      execute("getSummary", parameters, signal),
    getSinkHoldings: (parameters, signal) =>
      execute("getSinkHoldings", parameters, signal),
    getContractHoldings: (parameters, signal) =>
      execute("getContractHoldings", parameters, signal),
  };
}

export const wasmProvider = createProvider("wasm");
export const vfsProvider = createProvider("vfs");
