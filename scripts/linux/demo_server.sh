#!/usr/bin/env bash
set -euo pipefail
PORT="${1:-8787}"
source .venv/bin/activate
echo "Starting Demo API on http://127.0.0.1:${PORT}"
python -m uvicorn app.demo_api:app --host 127.0.0.1 --port "${PORT}"