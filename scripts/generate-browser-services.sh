#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Let the web process write its HTTP client beside the mounted Transcrypt output.
docker compose exec -T --user root web sh -c \
    'mkdir -p /app/src/generated && chown node:node /app/src/generated'

# Regenerate the modules in the volume shared by the API and web containers.
docker compose exec -T api sh /app/startup.sh
