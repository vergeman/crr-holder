import React, { useState } from "react";

export function BenchmarkPage() {
  const [provider, setProvider] = useState("http");

  return (
    <main>
      <h1>Provider benchmarks</h1>
      <p>Compare HTTP, WASM, and VFS service calls.</p>
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
    </main>
  );
}
