# 0003 - Establish the Stack

Type: feat
Branch: feat/0003-establish-stack

## Goal

* Run FastAPI in `/api` and React in `/web` through Docker Compose.
* Fetch account-holder identifiers from SQLite and render an unstyled list.
* Reflect host source edits in the running development containers.

## Context

* Use the existing `db/crr/crr.sqlite` from Sprint 1. If absent, run the Docker
  preparation commands in [the dataset README](../../db/crr/README.md) once.
* This narrows Sprint 2 in [the outline](0001-init-outline.md) to a connection demo.

## Implementation limits

* One API module, one SQL query, one temporary endpoint, and one React view.
* Use Python's `sqlite3`; no ORM, migrations, database copies, or schema changes.
* Include `@tanstack/react-query` as a dependency and `orval` as a dev dependency
  in `web/package.json`, but use plain `fetch` for this demo.
* No generated client, Query provider, routing, shared access interface, styling,
  starter assets, application scaffolding, or explorer features yet.
* No automated tests, test dependencies, CI, production images, health checks,
  retry infrastructure, or extra services.

## Approach

### Commit group 1 - Minimal API

* Add `api/main.py`, pinned `api/requirements.txt`, and `api/Dockerfile`.
* Base the image on official Python slim; install FastAPI and Uvicorn.
* Implement temporary `GET /api/account-holders` using
  `SELECT account_holder FROM account_holders ORDER BY account_holder`.
* Return a JSON array of strings; no enrichment fields, filters, or pagination.
* Open the mounted database read-only and close the connection per request.
* Run Uvicorn on `0.0.0.0:8000` with source reload enabled.

### Commit group 2 - Minimal React demo

* Add only `web/package.json`, its npm lockfile, `web/index.html`,
  `web/src/main.jsx`, `web/vite.config.js`, and `web/Dockerfile`.
* Use React, React DOM, Vite, and the React Vite plugin, plus the two requested
  dependencies above. Use JavaScript for this demo.
* Base the image on official Node LTS; install dependencies with `npm ci`.
* Fetch `/api/account-holders` on mount and render identifiers in a plain list.
  Show brief loading or request-error text in the same view.
* Proxy `/api` through Vite to `http://api:8000`, retaining the path.
* Run Vite on `0.0.0.0:5173`; use its normal hot reload.

### Commit group 3 - Compose and run instructions

* Add root `docker-compose.yml` with only `api` and `web` services.
* Build from their Dockerfiles. Publish API port `8000` and web port `5173`.
* Bind-mount `/api` and `/web` source directories from the host.
  Keep container-installed `node_modules` outside the web bind mount using
  a dedicated volume; do not install dependencies on the host.
* Bind-mount `./db/crr` read-only into the API container so it reads the existing
  dataset directly. Do not run dataset preparation during Compose startup.
* Keep Compose syntax compatible with the installed `docker-compose` command.
* Add a brief root README with the dataset prerequisite, startup command
  `docker-compose up --remove-orphans`, browser URL `http://localhost:5173`,
  endpoint URL, shutdown command, and rebuild instruction for dependency edits.
  Also show the modern equivalent `docker compose up --remove-orphans`.
* Update ignore rules only for generated frontend dependencies/build output;
  add minimal Docker context exclusions where needed.
* Separate code phases with blank lines and brief purpose comments where useful.
  Use conventional commits with concise bullet bodies and lines within 80 chars.

## Scope control

* Use the smallest implementation satisfying the acceptance criteria.
* Treat acceptance criteria and verification below as closed lists.
* Before adding unplanned stored data, files, dependencies, or substantial
  verification, explain why, explicitly prompt the user for a scope decision,
  and wait for their reply. Existing authorization covers the requested work.
* Resolve routine implementation choices within this scope without prompting.
* Leave dataset preparation and later sprint designs unchanged.

## Validation and tests

* No automated tests or endpoint-to-query comparisons in this sprint.
* Start the services with the documented Compose command.
* The user will manually verify that the page renders the account-holder list.

## Acceptance

* [x] Compose starts both services on ports `8000` and `5173`.
* [x] The endpoint returns the sorted account-holder identifiers from SQLite.
* [x] React fetches and renders the same list without styling.
* [x] `package.json` includes TanStack Query and Orval; the demo uses plain fetch.
* [x] Run instructions are documented; no automated tests or extra features exist.
