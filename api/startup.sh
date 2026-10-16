#!/bin/sh
set -eu

archive=$(mktemp)
trap 'rm -f "$archive"' EXIT

# Finish compilation before replacing the modules shared with the web container.
python browser/build.py > "$archive"
mkdir -p /browser-services
rm -f /browser-services/*.js
tar -xf "$archive" -C /browser-services
rm -f "$archive"
trap - EXIT

exec "$@"
