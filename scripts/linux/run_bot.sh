#!/usr/bin/env bash
set -euo pipefail
# CITL_CWD_GUARD_V2
if ! pwd >/dev/null 2>&1; then
  cd "$HOME" 2>/dev/null || cd / 2>/dev/null || true
fi

source .venv/bin/activate
python scripts/demo/run_bot.py "$@"
