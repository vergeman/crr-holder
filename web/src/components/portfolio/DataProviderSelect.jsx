export default function DataProviderSelect() {
  const parameters = new URLSearchParams(window.location.search);
  const provider = parameters.get("provider") || "wasm";

  function changeProvider(event) {
    const url = new URL(window.location.href);
    url.searchParams.set("provider", event.target.value);
    for (const method of [
      "metadata",
      "summary",
      "sources",
      "sinks",
      "contracts",
    ]) {
      url.searchParams.delete(method);
    }
    window.location.assign(url);
  }

  return (
    <label>
      Data provider
      <select value={provider} onChange={changeProvider}>
        <option value="wasm">WASM full download</option>
        <option value="vfs">SQL HTTP VFS</option>
        <option value="http">HTTP API</option>
      </select>
    </label>
  );
}
