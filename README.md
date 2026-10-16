# CRR holdings explorer development

Use the existing `db/crr/crr.sqlite`. If absent, run the Docker preparation
commands in [the dataset README](db/crr/README.md) once.

From the repository root:

```sh
docker compose up --remove-orphans
```

Use the installed modern Compose command. Legacy `docker-compose` can fail with
`ContainerConfig` on recent Docker Engines when recreating existing containers.

Open http://localhost:5173 to explore report and portfolio summaries.
The API endpoints are http://localhost:8000/api/metadata and
http://localhost:8000/api/summary.

Host source edits reload FastAPI and update React automatically.
The web development command waits for the API and generates HTTP code/types in
`web/src/generated/` before starting Vite. It checks the OpenAPI schema every
two seconds and regenerates on changes; failures are printed and retried.
Keep handwritten provider and query hooks in `web/src/data/`, outside the
replaceable generated directory. The provider selection is the swap point for
future browser SQLite and VFS access.
After dependency changes, rebuild and refresh the frontend dependency volume:

```sh
docker compose down -v
docker compose up --build --remove-orphans
```

Stop with Ctrl+C, then remove the containers with `docker compose down`.

MCP clients can connect to `http://localhost:8000/mcp/` using remote Streamable
HTTP. The endpoint runs alongside `/api/*` in the same process. For clients that
accept a URL-based MCP configuration:

```json
{
  "mcpServers": {
    "crr-holdings": {
      "type": "http",
      "url": "http://localhost:8000/mcp/"
    }
  }
}
```

The five read-only tools are `get_metadata`, `get_summary`,
`get_source_holdings`, `get_sink_holdings`, and `get_contract_holdings`.
Start with `get_metadata` to select a `report_id` and optional `account_holder`.
Call `get_summary` and `get_source_holdings` with that selection; follow
`nextOffset` by passing it as `offset` for the next source page. Expand a returned
`source` with `get_sink_holdings`, then call `get_contract_holdings` with that
source, a returned `sink`, a delivery `month` such as `2026-10-01`, and
`hedge_type` (`OPT` or `OBL`). Keep the same report and portfolio filters through
the drill-down. Source pages default to 20 rows, accept limits from 1 to 100,
and start at offset 0. Months must be real first-of-month ISO dates.

MCP usage logs are enabled by default as JSON INFO messages on `uvicorn.error`.
Each dispatched call records `tool`, normalized `parameters` (including defaults),
`status`, `elapsed_ms`, `cpu_ms`, `rss_before_bytes`, and `rss_after_bytes`.
`input_payload_bytes` counts compact UTF-8 JSON for normalized parameters;
`output_payload_bytes` counts the response model's UTF-8 JSON, or is null when
the tool fails. These payload sizes exclude MCP/HTTP framing and compression
and do not measure actual network traffic or bandwidth rates.
Failures also record `error_type`, without exception messages or response data.
Elapsed time includes database connection setup and response model conversion.
CPU milliseconds measure the invocation thread; RSS samples shared process memory
at two instants. These are not peak or per-customer memory measurements or
isolated CPU attribution across worker threads. Schema failures rejected before
dispatch produce no usage record. Counts represent dispatched calls, not billable
operations or unique user questions. `ENABLED_TIMED=1` independently adds the
existing service timing messages. No usage data or logs are written to files by
the application.

This connection is for local development. Hosted authentication, public
deployment, and billing are separate work. The pinned official SDK (`mcp==2.3.0`)
runs synchronous tools in worker threads; each read-only SQLite connection is
opened, used, and closed within its invocation thread.

Run the API verification from the repository root:

```sh
docker compose exec -T api python -m unittest discover -s tests -v
docker compose exec -T api python -m pip check
git diff --check
```

Run this SDK smoke check against the running mounted endpoint. Entering `Client`
initializes the connection:

```sh
docker compose exec -T api python - <<'PY'
import asyncio
from mcp import Client

async def main():
    async with Client('http://localhost:8000/mcp/') as client:
        tools = await client.list_tools()
        print([tool.name for tool in tools.tools])
        result = await client.call_tool('get_metadata')
        assert not result.is_error
        print('metadata report:', result.structured_content['reportId'])

asyncio.run(main())
PY
```
