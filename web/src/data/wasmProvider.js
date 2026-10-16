function createProvider(backend) {
  let worker;
  let database;
  let nextRequestId = 0;
  const requests = new Map();

  function getWorker() {
    if (worker) return worker;
    worker = new Worker(new URL("./sqlite.worker.js", import.meta.url), {
      type: "module",
    });
    worker.onmessage = ({ data: { id, result, error } }) => {
      const request = requests.get(id);
      if (!request) return;
      if (error) request.reject(new Error(error));
      else request.resolve(result);
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
    if (backend === "vfs") {
      await requestWorker({ backend });
      return;
    }
    const started = performance.now();
    const response = await fetch("/api/database", { cache: "no-store" });
    if (!response.ok)
      throw new Error(`Database download failed: ${response.status}`);
    const buffer = await response.arrayBuffer();
    console.info("SQLite WASM download", {
      bytes: buffer.byteLength,
      downloadMs: performance.now() - started,
    });
    await requestWorker({ buffer, backend }, undefined, Promise.resolve(), [
      buffer,
    ]);
  }

  function execute(method, parameters, signal) {
    signal?.throwIfAborted();
    database ??= loadDatabase().catch((error) => {
      database = undefined;
      throw error;
    });
    return requestWorker({ method, parameters }, signal, database);
  }

  return {
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
