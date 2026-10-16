export function responsesEqual(actual, expected) {
  if (actual === expected) return true;
  if (
    actual === null ||
    expected === null ||
    typeof actual !== "object" ||
    typeof expected !== "object"
  )
    return false;
  if (Array.isArray(actual) !== Array.isArray(expected)) return false;
  const keys = Object.keys(actual);
  return (
    keys.length === Object.keys(expected).length &&
    keys.every(
      (key) =>
        Object.hasOwn(expected, key) &&
        responsesEqual(actual[key], expected[key])
    )
  );
}

export function aggregate(samples) {
  if (!samples.length) return null;
  const sorted = [...samples].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return {
    median:
      sorted.length % 2
        ? sorted[middle]
        : (sorted[middle - 1] + sorted[middle]) / 2,
    p95: sorted[Math.ceil(sorted.length * 0.95) - 1],
  };
}

// Race the operation itself: synchronous worker SQL cannot honor an abort signal.
async function bounded(operation, timeoutMs, signal) {
  signal.throwIfAborted();
  const controller = new AbortController();
  let timer;
  let abort;
  const interrupted = new Promise((_, reject) => {
    abort = () => {
      controller.abort(signal.reason);
      reject(signal.reason);
    };
    signal.addEventListener("abort", abort, { once: true });
    timer = setTimeout(() => {
      const error = new Error(`Timed out after ${timeoutMs / 1000}s`);
      error.name = "TimeoutError";
      controller.abort(error);
      reject(error);
    }, timeoutMs);
  });
  try {
    return await Promise.race([interrupted, operation(controller.signal)]);
  } finally {
    clearTimeout(timer);
    signal.removeEventListener("abort", abort);
  }
}

export async function runBenchmark({
  backend,
  suite,
  httpProvider,
  createProvider,
  timeoutMs = 10000,
  passes = 3,
  networkLabel = "",
  latencyMs = 0,
  preloadedDownload,
  signal,
  onProgress = () => {},
}) {
  const run = {
    backend,
    timestamp: new Date().toISOString(),
    networkLabel,
    latencyMs,
    timeoutMs,
    passes,
    preloadedDownload,
    status: "running",
    startups: [],
    transfer: {
      requests: preloadedDownload ? 1 : 0,
      downloadBytes: preloadedDownload?.bytes ?? 0,
      startupBytes: preloadedDownload?.bytes ?? 0,
    },
    results: suite.map((workload) => ({
      ...workload,
      status: "pending",
      samples: [],
    })),
  };
  const references = new Map();
  const skipped = new Set();
  let provider;
  let startupIndex;
  let firstCall;
  let current;

  function disposeProvider() {
    const transfer = provider?.getTransferStats?.();
    if (transfer) {
      run.transfer.requests += transfer.requests;
      run.transfer.downloadBytes += transfer.downloadBytes;
    }
    provider?.dispose?.();
    provider = undefined;
  }

  function skipService(service, reason) {
    skipped.add(service);
    for (const result of run.results) {
      if (
        result.service === service &&
        result !== current &&
        result.status === "pending"
      ) {
        result.status = "skipped";
        result.error = reason;
      }
    }
  }

  async function initialize() {
    provider = backend === "http" ? httpProvider : createProvider(backend);
    const startup = { before: current.id, status: "running" };
    run.startups.push(startup);
    startupIndex = run.startups.length - 1;
    onProgress(`Initializing ${backend}`);
    const started = performance.now();
    try {
      startup.timings = await bounded(
        () => provider.initialize?.(),
        timeoutMs,
        signal
      );
      startup.totalMs = performance.now() - started;
      startup.status = "complete";
      firstCall = true;
    } catch (error) {
      startup.totalMs = performance.now() - started;
      startup.status = "failed";
      startup.error = error.message;
      throw error;
    } finally {
      run.transfer.startupBytes +=
        provider.getTransferStats?.().downloadBytes ?? 0;
    }
  }

  try {
    // Correctness references are collected before any browser database startup.
    for (current of run.results) {
      if (skipped.has(current.service)) continue;
      onProgress(`HTTP baseline: ${current.id}`);
      try {
        references.set(
          current.id,
          await bounded(
            (callSignal) =>
              httpProvider[current.service](current.parameters, callSignal),
            timeoutMs,
            signal
          )
        );
      } catch (error) {
        if (signal.aborted) throw error;
        current.status = "failed";
        current.error = `HTTP baseline: ${error.message}`;
        skipService(current.service, "HTTP baseline unavailable");
      }
    }

    // Baseline downloads are verification overhead, not provider traffic.
    httpProvider.resetTransferStats?.();

    for (const phase of [
      "first",
      "warmup",
      ...Array.from({ length: passes }, (_, index) => index + 1),
    ]) {
      for (current of run.results) {
        if (skipped.has(current.service)) continue;
        if (!provider) await initialize();
        onProgress(`${phase}: ${current.id}`);
        const cold = firstCall;
        const started = performance.now();
        try {
          const response = await bounded(
            (callSignal) =>
              provider[current.service](current.parameters, callSignal),
            timeoutMs,
            signal
          );
          const clientMs = performance.now() - started;
          firstCall = false;
          const samplePhase = cold ? "first-call" : phase;
          if (phase !== "warmup" || cold)
            current.samples.push({
              phase: samplePhase,
              clientMs,
              worker: provider.getTimings?.(),
              startupIndex,
            });
          // Object key order is irrelevant; array order and numeric values matter.
          if (!responsesEqual(response, references.get(current.id))) {
            current.status = "failed";
            current.error = "Response differs from HTTP baseline";
            skipService(current.service, "Service failed response comparison");
          } else {
            current.status = "complete";
          }
        } catch (error) {
          if (signal.aborted) throw error;
          current.status = "failed";
          current.error = error.message;
          skipService(
            current.service,
            "Service failed; remaining calls skipped"
          );
          disposeProvider();
        }
      }
    }
    run.status = "complete";
  } catch (error) {
    run.status = signal.aborted ? "stopped" : "failed";
    run.error = error.message;
  } finally {
    disposeProvider();
    for (const result of run.results) {
      if (result.status === "pending") result.status = "skipped";
      result.warm = aggregate(
        result.samples
          .filter((sample) => typeof sample.phase === "number")
          .map((sample) => sample.clientMs)
      );
    }
  }
  return run;
}
