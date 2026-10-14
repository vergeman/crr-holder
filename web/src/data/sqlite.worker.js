// Imports
import { openDatabase } from './sqlite';

// Preparation: simultaneous requests share the same download and connection.
let database;

self.onmessage = async ({ data: { id, label, sql, params } }) => {
  try {
    database ??= openDatabase();
    const db = await database;
    const queryStart = performance.now();

    // Transformation: free each statement after returning ordinary row objects.
    const statement = db.prepare(sql);
    const rows = [];
    try {
      statement.bind(params);
      while (statement.step()) rows.push(statement.getAsObject());
    } finally {
      statement.free();
    }

    // Output: correlate responses even when several queries are pending.
    console.info('SQLite WASM query', { label, queryMs: performance.now() - queryStart });
    self.postMessage({ id, rows });
  } catch (error) {
    self.postMessage({ id, error: error.message });
  }
};
