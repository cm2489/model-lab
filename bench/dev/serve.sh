#!/bin/sh
# Serve the repo root so the bench runs exactly as GitHub Pages serves it.
#   sh bench/dev/serve.sh            then open http://localhost:8787/bench/
# Test data:  /bench/?fixture=first-day | mid-track | all-done
cd "$(dirname "$0")/../.." && exec python3 -m http.server "${PORT:-8787}" --bind 127.0.0.1
