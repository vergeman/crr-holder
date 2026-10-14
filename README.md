# CRR holder development demo

Use the existing `db/crr/crr.sqlite`. If absent, run the Docker preparation
commands in [the dataset README](db/crr/README.md) once.

From the repository root:

```sh
docker-compose up --remove-orphans
```

The modern equivalent is `docker compose up --remove-orphans`.

Open http://localhost:5173 to see account holders fetched from SQLite.
The temporary API is http://localhost:8000/api/account-holders.

Host source edits reload FastAPI and update React automatically.
After dependency changes, rebuild and refresh the frontend dependency volume:

```sh
docker-compose down -v
docker-compose up --build --remove-orphans
```

Stop with Ctrl+C, then remove the containers with `docker-compose down`.
