#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Compile the Python query services into JavaScript with Transcrypt, then place
# the generated modules in web/src/generated/transcrypt/ for the browser build.

# Keep compiler dependencies outside the API runtime environment.
docker compose exec -T api sh -c '
  test -f /tmp/crr-transcrypt/ready || {
    python -m pip install --target /tmp/crr-transcrypt -r browser/requirements.txt >&2
    touch /tmp/crr-transcrypt/ready
  }
'

output=$(mktemp -d)
trap 'rm -rf "$output"' EXIT
docker compose exec -T -e PYTHONPATH=/tmp/crr-transcrypt api \
  python browser/build.py | tar -xf - -C "$output"
mkdir -p web/src/generated/transcrypt
rm -f web/src/generated/transcrypt/*.js
cp "$output"/*.js web/src/generated/transcrypt/
