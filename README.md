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

For a second worktree, use a distinct Compose project name and unused host ports:

```sh
WEB_PORT=5174 API_PORT=8001 docker compose -p crr-wasm up -d --remove-orphans
```

Open http://localhost:5174 for that instance. Container ports and the internal
API address stay the same. Each project has its own containers and dependency
volume; use the same `-p crr-wasm` for later commands. Keep both browser origins
in the S3 CORS configuration when using WASM in both instances.

Host source edits reload FastAPI and update React automatically.
The web development command waits for the API and generates HTTP code/types in
`web/src/generated/` before starting Vite. It checks the OpenAPI schema every
two seconds and regenerates on changes; failures are printed and retried.
Keep handwritten provider and query hooks in `web/src/data/`, outside the
replaceable generated directory. The provider selection is the swap point for
browser SQLite and VFS access.

## Browser SQLite experiment

HTTP is the default provider. To run the same filters and portfolio summaries
with SQLite WASM, put this setting in `web/.env.local`:

```dotenv
VITE_DATA_PROVIDER=wasm
```

Vite reloads its configuration when the environment file changes. Refresh the
browser after switching providers to clear the previous provider's query cache.
Set `VITE_DATA_PROVIDER=http` to return to the API baseline.

The WASM provider runs sql.js in a browser worker and downloads
`https://crr-holder.s3.us-east-2.amazonaws.com/crr.sqlite` once per page load.
It retains a query-only connection for subsequent filters. The initial download
is 333 MiB; the database lives in browser memory. No persistent browser database
is created. S3 must allow the page's origin through CORS.

Browser console messages report database bytes, download time, database-open
time, and individual SQL query times. Query timings exclude initialization.
Use browser network tools to distinguish a fresh download from an HTTP-cache hit.
The existing development command still uses the API for HTTP client generation.

After dependency changes, rebuild and refresh the frontend dependency volume:

```sh
docker compose down -v
docker compose up --build --remove-orphans
```

Stop with Ctrl+C, then remove the containers with `docker compose down`.
