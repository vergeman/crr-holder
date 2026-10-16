import sqlite3InitModule from "@sqlite.org/sqlite-wasm";
import sqliteWasmUrl from "@sqlite.org/sqlite-wasm/sqlite3.wasm?url";
import * as services from "../generated/transcrypt/entry.js";
import { sqliteAdapter } from "./sqliteAdapter";

let database;
let sqlMs = 0;

// SQLite 3.44 enumerates array arguments with for-in. Hide Transcrypt's
// prototype extensions so they are not mistaken for argument positions.
for (const name of Object.keys(Array.prototype)) {
  Object.defineProperty(Array.prototype, name, { enumerable: false });
}

async function initializeSQLite(backend) {
  if (backend === "vfs") {
    const { initSyncSQLite, createHttpBackend } =
      await import("sqlite-wasm-http");
    return initSyncSQLite({ http: createHttpBackend({ backendType: "sync" }) });
  }
  return sqlite3InitModule({ locateFile: () => sqliteWasmUrl });
}

async function loadDatabase(buffer, backend) {
  const started = performance.now();
  const sqlite3 = await initializeSQLite(backend);
  const openStarted = performance.now();
  let db;
  if (backend === "vfs") {
    const url = new URL("/api/database", self.location.origin).href;
    db = new sqlite3.oo1.DB(`file:${encodeURI(url)}`, "r", "http");
  } else {
    const bytes = new Uint8Array(buffer);
    db = new sqlite3.oo1.DB();
    const pointer = sqlite3.wasm.allocFromTypedArray(bytes);
    const rc = sqlite3.capi.sqlite3_deserialize(
      db.pointer,
      "main",
      pointer,
      bytes.byteLength,
      bytes.byteLength,
      sqlite3.capi.SQLITE_DESERIALIZE_FREEONCLOSE |
        sqlite3.capi.SQLITE_DESERIALIZE_READONLY
    );
    if (rc) {
      sqlite3.wasm.dealloc(pointer);
      db.close();
      throw new Error(`SQLite database import failed: ${rc}`);
    }
  }
  db.exec("PRAGMA query_only = ON");
  const timings = {
    runtimeMs: openStarted - started,
    openMs: performance.now() - openStarted,
    totalMs: performance.now() - started,
  };
  console.info("SQLite WASM database ready", {
    backend,
    sqliteVersion: sqlite3.version.libVersion,
    ...timings,
  });
  database = sqliteAdapter(db, (elapsed) => {
    sqlMs += elapsed;
  });
  return timings;
}

// Provider arguments stay independent of Python naming and parameter order.
function execute(
  method,
  {
    reportId = null,
    accountHolder = null,
    settlementPoint = null,
    source,
    sink,
    deliveryMonth,
    hedgeType,
    limit = 20,
    offset = 0,
  }
) {
  const portfolio = [reportId, accountHolder, settlementPoint];
  switch (method) {
    case "getMetadata":
      return services.metadata(database, reportId, accountHolder);
    case "getSummary":
      return services.summary(database, ...portfolio);
    case "getSourceHoldings":
      return services.sources(database, ...portfolio, limit, offset);
    case "getSinkHoldings":
      return services.sinks(database, source, ...portfolio);
    case "getContractHoldings":
      return services.contracts(
        database,
        source,
        sink,
        deliveryMonth,
        hedgeType,
        ...portfolio
      );
  }
}

self.onmessage = async ({
  data: { id, buffer, backend, method, parameters },
}) => {
  try {
    if (backend) {
      const timings = await loadDatabase(buffer, backend);
      self.postMessage({ id, timings });
      return;
    }
    sqlMs = 0;
    const started = performance.now();
    // Generated dictionaries carry methods that structured cloning cannot copy.
    const response = execute(method, parameters);
    const normalized = performance.now();
    const result = JSON.parse(JSON.stringify(response));
    const timings = {
      serviceMs: normalized - started,
      sqlMs,
      orchestrationMs: normalized - started - sqlMs,
      normalizationMs: performance.now() - normalized,
      totalMs: performance.now() - started,
    };
    console.info("SQLite WASM query", {
      method,
      ...parameters,
      elapsedMs: timings.totalMs,
    });
    self.postMessage({ id, result, timings });
  } catch (error) {
    self.postMessage({ id, error: error.stack ?? String(error) });
  }
};
