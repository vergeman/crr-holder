# Transcrypt browser build

This directory configures how the shared Python query services become browser
JavaScript.

- `entry.py` defines the functions exposed to the browser and delegates calls to
  the shared Python services. Its imports determine what Transcrypt compiles.
- `build.py` copies those services and browser compatibility stubs into a
  temporary workspace, sets the Transcrypt compiler options, and runs compilation.
  It removes unused source-map references and streams the generated JavaScript
  modules as a tar archive for the generation script to unpack.

Run `./scripts/generate-browser-services.sh` from the repository root to build
and copy the JavaScript into `web/src/generated/transcrypt/`.
