#!/usr/bin/env bash
set -euo pipefail
# CITL_CWD_GUARD_V2
if ! pwd >/dev/null 2>&1; then
  cd "$HOME" 2>/dev/null || cd / 2>/dev/null || true
fi

bash scripts/ollama/bootstrap.sh
bash scripts/citl/write_runtime_env.sh
echo "[bootstrap] done."
