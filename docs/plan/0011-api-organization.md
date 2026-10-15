# 0011 - API Organization

Type: refactor
Branch: refactor/0011-api-organization

## Tasks and commit groups

Implement in order. Each group is one commit and includes its affected imports
and test changes; keep the API runnable between commits. Tests stay in
`api/tests/`. Do not collect test updates into a final bulk commit.

### 1. Shared service helpers

* Add `api/services/__init__.py`. Move `resolve_report` from `queries.py` and
  `holdings_filter` from `filters.py` into `api/services/helpers.py`.

* Update imports in `queries.py`, `holdings.py`, `rankings.py`, `geography.py`,
  and `tests/test_summary.py`; remove `filters.py`.

* Update Dockerfile copying to include root Python modules and `services/`,
  retaining `main:app`. This supports the remaining moves without image changes.

### 2. Metadata service

* Move `get_metadata` from `queries.py` into `api/services/metadata.py`.
  Update its imports in `main.py` and `tests/test_summary.py` together.

### 3. Summary services

* Move `get_summary` into `api/services/summary.py`; move `rankings.py` and
  `geography.py` alongside it. Remove the now-empty root `queries.py`.

* Update service imports, `main.py`, and summary imports in `test_summary.py`,
  `test_rankings.py`, `test_geography.py`, and `test_holdings.py` together.

### 4. Holdings service

* Move `holdings.py` into `api/services/holdings.py`, keeping source, sink,
  and contract queries together.

* Update imports in `main.py`, `test_holdings.py`, `test_sinks.py`, and
  `test_contracts.py` together.

### 5. HTTP modules

* Move response models into `api/models.py`, retaining class names and fields.

* Move all five endpoints and delivery-month validation into `api/routes.py`
  using one router. Keep app creation and router registration in `api/main.py`.

* Move database connection handling into `api/database.py`.
  Set `DB_FILE: /data/crr.sqlite` on the API service in `docker-compose.yml`;
  read it in `database.py`, retaining read-only access.
  Update the database mock target in `tests/test_contracts.py` in this commit.

* If formatting-only cleanup is needed, commit it separately immediately after
  its related refactor. Preserve SQL comments and clear phase spacing.

## Scope control

* Limit work to the modules above, existing test imports/patches, Dockerfile,
  and the API service's `DB_FILE` environment setting in `docker-compose.yml`.
  Keep SQL, response assembly, URLs, parameters, validation, and operation IDs
  unchanged. Add no dependencies or additional service layers.

* Keep generated client type names unchanged. Orval currently emits functions
  and types into `web/src/generated/client.ts`; no model renames or frontend
  edits are planned.

* Treat these tasks and verification as closed lists. Explain and ask before
  adding unplanned files, stored data, dependencies, or substantial verification.
  Resolve routine implementation choices within this scope without confirmation.

## Verification

* Run the existing API tests to check calculations, filters, and route validation.
  Compare OpenAPI before and after to check the generated-client contract.

* Inspect Compose configuration and `docker compose ps`; reuse running services.
  Recreate only the API service when applying the new `DB_FILE` setting:
  `docker compose up -d --no-deps api`.

* After each commit group, run
  `docker compose exec -T api python -m unittest discover -s tests -v`.

* Before and after the refactor, run
  `docker compose exec -T api python -c 'import json; from main import app; print(json.dumps(app.openapi(), sort_keys=True))'`
  into temporary files under `/tmp`, then compare with `diff -u`.
