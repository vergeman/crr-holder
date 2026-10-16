import test from "node:test";
import assert from "node:assert/strict";
import {
  aggregate,
  responsesEqual,
  runBenchmark,
} from "../src/components/benchmark/runner.js";
import { createSuite } from "../src/components/benchmark/suite.js";
import { readFile } from "node:fs/promises";

const inputs = JSON.parse(
  await readFile(
    new URL(
      "../src/components/benchmark/measurement_inputs.json",
      import.meta.url
    )
  )
);
const suite = createSuite(inputs);

test("suite reuses the service matrix, filters, and both source pages", () => {
  assert.equal(suite.length, 22);
  assert.equal(suite[0].id, "getMetadata-market");
  assert.equal(
    suite.filter((item) => item.service === "getMetadata").length,
    2
  );
  assert.equal(
    suite.filter((item) => item.service === "getSourceHoldings").length,
    8
  );
  const combined = suite.find(
    (item) => item.id === "getSourceHoldings-combined-20"
  );
  assert.deepEqual(combined.parameters, {
    reportId: inputs.report_id,
    accountHolder: inputs.account_holder,
    settlementPoint: inputs.source,
    offset: 20,
    limit: 20,
  });
});

test("comparison ignores object key order but preserves values and row order", () => {
  assert.ok(
    responsesEqual({ a: 1, b: [{ x: null }] }, { b: [{ x: null }], a: 1 })
  );
  assert.ok(!responsesEqual([1, 2], [2, 1]));
  assert.ok(!responsesEqual({ a: null }, { a: 0 }));
  assert.ok(!responsesEqual({ a: 1 }, { a: "1" }));
  assert.ok(!responsesEqual([], {}));
});

test("aggregation retains a conventional median and nearest-rank p95", () => {
  assert.equal(aggregate([]), null);
  assert.deepEqual(aggregate([4, 1, 3, 2]), { median: 2.5, p95: 4 });
});

function options(overrides = {}) {
  const httpProvider = Object.fromEntries(
    [...new Set(suite.map((item) => item.service))].map((method) => [
      method,
      async () => ({ rows: [1] }),
    ])
  );
  return {
    backend: "vfs",
    suite,
    httpProvider,
    createProvider: () => ({
      ...httpProvider,
      initialize: async () => ({}),
      dispose() {},
    }),
    signal: new AbortController().signal,
    passes: 3,
    timeoutMs: 15,
    ...overrides,
  };
}

test("first, warmup, and warm passes stay separate and parity failures are visible", async () => {
  const configuration = options();
  const run = await runBenchmark(configuration);

  assert.equal(run.status, "complete");
  assert.equal(run.results[0].samples[0].phase, "first-call");
  assert.equal(run.results[1].samples[0].phase, "first");
  assert.ok(
    run.results.every((item) => item.samples.length === 4 && item.warm !== null)
  );
  const failed = await runBenchmark(
    options({
      createProvider: () => ({
        ...configuration.httpProvider,
        getMetadata: async () => ({}),
        dispose() {},
      }),
    })
  );
  assert.match(failed.results[0].error, /differs/);
  assert.equal(failed.results[1].status, "skipped");
  assert.equal(failed.results[2].status, "complete");
});

test("a stalled service is terminated and later services use a fresh instance", async () => {
  const configuration = options();
  let created = 0;
  let disposed = 0;
  const run = await runBenchmark(
    options({
      createProvider: () => {
        created++;
        return {
          ...configuration.httpProvider,
          initialize: async () => ({}),
          getMetadata: () => new Promise(() => {}),
          dispose: () => disposed++,
        };
      },
    })
  );

  assert.equal(created, 2);
  assert.equal(disposed, 2);
  assert.match(run.results[0].error, /Timed out/);
  assert.equal(run.results[1].status, "skipped");
  assert.equal(run.results[2].status, "complete");
  assert.equal(run.results[2].samples[0].phase, "first-call");
  assert.equal(run.startups.length, 2);
});

test("initialization timeout ends the run and stop disposes a stalled worker", async () => {
  const configuration = options();
  let disposed = 0;
  const initialization = await runBenchmark(
    options({
      createProvider: () => ({
        initialize: () => new Promise(() => {}),
        dispose: () => disposed++,
      }),
    })
  );

  assert.equal(initialization.status, "failed");
  assert.equal(disposed, 1);
  const controller = new AbortController();
  const stopped = await runBenchmark(
    options({
      signal: controller.signal,
      createProvider: () => ({
        ...configuration.httpProvider,
        getMetadata: () => {
          controller.abort();
          return new Promise(() => {});
        },
        dispose: () => disposed++,
      }),
    })
  );
  assert.equal(stopped.status, "stopped");
  assert.equal(disposed, 2);
});

test("baseline failure skips that service before provider execution", async () => {
  const configuration = options();
  configuration.httpProvider.getMetadata = () => new Promise(() => {});
  const run = await runBenchmark(configuration);

  assert.equal(run.results[0].status, "failed");
  assert.match(run.results[0].error, /HTTP baseline/);
  assert.equal(run.results[1].status, "skipped");
  assert.equal(run.results[2].status, "complete");
});
