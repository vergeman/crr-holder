// Imports
import initSqlJs from 'sql.js';
import wasmUrl from 'sql.js/dist/sql-wasm.wasm?url';

// Import: load the published snapshot into SQLite's in-memory filesystem.
export async function openDatabase() {
  const sqlite = initSqlJs({ locateFile: () => wasmUrl });
  const downloadStart = performance.now();
  const response = await fetch('https://crr-holder.s3.us-east-2.amazonaws.com/crr.sqlite');
  if (!response.ok) throw new Error(`Database download failed: ${response.status}`);
  const bytes = new Uint8Array(await response.arrayBuffer());
  const downloadMs = performance.now() - downloadStart;
  const SQL = await sqlite;

  // Preparation: retain one connection for the worker's lifetime.
  const openStart = performance.now();
  const db = new SQL.Database(bytes);
  db.run('PRAGMA query_only = ON');
  console.info('SQLite WASM initialization', {
    bytes: bytes.byteLength,
    downloadMs,
    openMs: performance.now() - openStart,
  });
  return db;
}
