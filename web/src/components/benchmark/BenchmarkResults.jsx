import React from "react";
import { aggregate } from "./runner";

const ms = (value) => (value == null ? "—" : `${value.toFixed(1)} ms`);

export function BenchmarkResults({ runs, preloaded }) {
  function downloadRuns() {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(runs, null, 2)], { type: "application/json" })
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "provider-benchmarks.json";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section aria-label="Benchmark results">
      {preloaded && (
        <p>
          Preloaded {preloaded.bytes.toLocaleString()} bytes in{" "}
          {ms(preloaded.downloadMs)}. Estimated transfer at 100 Mbit/s:{" "}
          {ms((preloaded.bytes * 8) / 100000)} before added latency. Estimate
          excludes protocol overhead and replaces no measured timing.
        </p>
      )}
      <button disabled={!runs.length} onClick={downloadRuns}>
        Download JSON
      </button>
      <p>
        Fresh workers reset SQLite state, not server or OS caches. Network delay
        is applied by the development proxy and does not limit bandwidth. Warm
        statistics exclude first calls and warm-up passes.
      </p>
      <div
        className="benchmark-table"
        tabIndex="0"
        aria-label="Provider comparison"
      >
        <table>
          <caption>Retained runs</caption>
          <thead>
            <tr>
              <th>Provider</th>
              <th>Network</th>
              <th>API latency</th>
              <th>Status</th>
              <th>Completed</th>
              <th>Failed</th>
              <th>Skipped</th>
              <th>Total initialization</th>
              <th>First-pass total</th>
              <th>Warm call median</th>
              <th>Warm call p95</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run, index) => {
              const samples = run.results.flatMap((result) => result.samples);
              const firstPass = samples.filter((sample) =>
                ["first", "first-call"].includes(sample.phase)
              );
              const warm = aggregate(
                samples
                  .filter((sample) => typeof sample.phase === "number")
                  .map((sample) => sample.clientMs)
              );

              return (
                <tr key={index}>
                  <td>
                    <a href={`#run-${index}`}>
                      {run.backend} #{index + 1}
                    </a>
                  </td>
                  <td>{run.networkLabel}</td>
                  <td>{ms(run.latencyMs ?? 0)}</td>
                  <td>{run.status}</td>
                  {["complete", "failed", "skipped"].map((status) => (
                    <td key={status}>
                      {
                        run.results.filter((result) => result.status === status)
                          .length
                      }
                    </td>
                  ))}
                  <td>
                    {ms(
                      run.startups.length
                        ? run.startups.reduce(
                            (total, startup) => total + startup.totalMs,
                            0
                          )
                        : null
                    )}
                  </td>
                  <td>
                    {ms(
                      firstPass.length
                        ? firstPass.reduce(
                            (total, sample) => total + sample.clientMs,
                            0
                          )
                        : null
                    )}
                  </td>
                  <td>{ms(warm?.median)}</td>
                  <td>{ms(warm?.p95)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p>
        Totals include recorded initialization and first-pass calls. Warm median
        and p95 pool all recorded warm query calls. Failed and skipped calls
        have no query samples; compare runs with matching workload coverage.
      </p>
      {runs.map((run, index) => (
        <article key={index} id={`run-${index}`}>
          <h2>
            {run.backend} #{index + 1} · {run.networkLabel}
          </h2>
          <p>
            {run.timestamp} · {run.status}
            {run.error && `: ${run.error}`}
          </p>
          {run.preloadedDownload && (
            <p>
              Used a preloaded database. Actual unshaped download:{" "}
              {ms(run.preloadedDownload.downloadMs)}; estimated transfer at 100
              Mbit/s + {run.latencyMs ?? 0} ms:{" "}
              {ms(
                (run.preloadedDownload.bytes * 8) / 100000 +
                  (run.latencyMs ?? 0)
              )}
              . Download estimate is excluded from measured initialization.
            </p>
          )}
          <div
            className="benchmark-table"
            tabIndex="0"
            aria-label="Startup measurements"
          >
            <table>
              <caption>Initialization and first call</caption>
              <thead>
                <tr>
                  <th>Before workload</th>
                  <th>Status</th>
                  <th>Initialization</th>
                  <th>Download bytes / time</th>
                  <th>Runtime / DB open</th>
                  <th>Startup + first call</th>
                </tr>
              </thead>
              <tbody>
                {run.startups.map((startup, startupIndex) => {
                  const first = run.results
                    .flatMap((result) => result.samples)
                    .find(
                      (sample) =>
                        sample.startupIndex === startupIndex &&
                        sample.phase === "first-call"
                    );
                  return (
                    <tr key={startupIndex}>
                      <td>{startup.before}</td>
                      <td>
                        {startup.status}
                        {startup.error && `: ${startup.error}`}
                      </td>
                      <td>{ms(startup.totalMs)}</td>
                      <td>
                        {startup.timings?.preloaded
                          ? "Preloaded"
                          : startup.timings?.download
                          ? `${startup.timings.download.bytes.toLocaleString()} / ${ms(
                              startup.timings.download.downloadMs
                            )}`
                          : "—"}
                      </td>
                      <td>
                        {ms(startup.timings?.worker?.runtimeMs)} /{" "}
                        {ms(startup.timings?.worker?.openMs)}
                      </td>
                      <td>
                        {first ? ms(startup.totalMs + first.clientMs) : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div
            className="benchmark-table"
            tabIndex="0"
            aria-label="Query measurements"
          >
            <table>
              <caption>Query comparison (client call times)</caption>
              <thead>
                <tr>
                  <th>Workload</th>
                  <th>Status / parity</th>
                  <th>First pass</th>
                  <th>Warm median</th>
                  <th>Warm p95</th>
                  <th>Samples</th>
                </tr>
              </thead>
              <tbody>
                {run.results.map((result) => (
                  <tr key={result.id}>
                    <td>{result.id}</td>
                    <td>
                      {result.status === "complete"
                        ? "Matched HTTP"
                        : result.status}
                      {result.error && `: ${result.error}`}
                    </td>
                    <td>
                      {ms(
                        result.samples.find((sample) =>
                          ["first", "first-call"].includes(sample.phase)
                        )?.clientMs
                      )}
                    </td>
                    <td>{ms(result.warm?.median)}</td>
                    <td>{ms(result.warm?.p95)}</td>
                    <td>
                      <details>
                        <summary>{result.samples.length} samples</summary>
                        <pre>
                          {JSON.stringify(
                            {
                              parameters: result.parameters,
                              samples: result.samples,
                            },
                            null,
                            2
                          )}
                        </pre>
                      </details>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      ))}
    </section>
  );
}
