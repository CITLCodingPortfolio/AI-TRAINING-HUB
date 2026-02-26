#!/usr/bin/env bash
set -euo pipefail
# CITL_CWD_GUARD_V2
if ! pwd >/dev/null 2>&1; then
  cd "$HOME" 2>/dev/null || cd / 2>/dev/null || true
fi

PORT="${1:-8787}"
source .venv/bin/activate
echo "Starting Demo API on http://127.0.0.1:${PORT}"
python -m uvicorn app.demo_api:app --host 127.0.0.1 --port "${PORT}"
