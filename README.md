# CRR holdings explorer development

Use the existing `db/crr/crr.sqlite`. If absent, run the Docker preparation
commands in [the dataset README](db/crr/README.md) once.

From the repository root:

```sh
docker compose up --remove-orphans
```

Use the installed modern Compose command. Legacy `docker-compose` can fail with
`ContainerConfig` on recent Docker Engines when recreating existing containers.

With the services running, install frontend dependencies and generate browser
services before opening the app:

```sh
docker compose exec -T web npm ci
bash scripts/generate-browser-services.sh
```

Regenerate after changing Python services and before `npx vite build`. The script
installs the pinned compiler in the API container and exports ignored JavaScript
artifacts; do not edit those artifacts.

Open http://localhost:5173 to explore report and portfolio summaries.
The API endpoints are http://localhost:8000/api/metadata and
http://localhost:8000/api/summary.

Host source edits reload FastAPI and update React automatically.
The web development command waits for the API and generates HTTP code/types in
`web/src/generated/` before starting Vite. It checks the OpenAPI schema every
two seconds and regenerates on changes; failures are printed and retried.
Keep handwritten provider and query hooks in `web/src/data/`, outside the
replaceable generated directory. The header selects WASM (default), HTTP API, or
HTTP range VFS. WASM downloads the database once per page session; VFS's market-wide startup scan remains
unusable. See [browser services](docs/web.md#browser-services).
After frontend dependency changes, run `docker compose exec -T web npm ci`.
Inspect `docker compose ps` and reuse running services; rebuild only when needed.

Stop with Ctrl+C, then remove the containers with `docker compose down`.
