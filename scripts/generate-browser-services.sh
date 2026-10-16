#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Regenerate the modules in the volume shared by the API and web containers.
docker compose exec -T api sh /app/startup.sh
