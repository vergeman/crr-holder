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
