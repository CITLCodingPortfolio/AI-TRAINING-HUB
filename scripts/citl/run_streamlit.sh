#!/usr/bin/env bash
set -euo pipefail
# CITL_CWD_GUARD_V2
if ! pwd >/dev/null 2>&1; then
  cd "$HOME" 2>/dev/null || cd / 2>/dev/null || true
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Load runtime env (models + host)
if [[ -f "$ROOT/config/runtime.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ROOT/config/runtime.env"
  set +a
fi

cd "$ROOT"

# venv if present
if [[ -d ".venv" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

# Pick entrypoint
EP="${CITL_STREAMLIT_ENTRYPOINT:-}"
if [[ -z "$EP" ]]; then
  for cand in streamlit_app.py app.py main.py ui.py; do
    [[ -f "$cand" ]] && EP="$cand" && break
  done
fi
if [[ -z "$EP" ]]; then
  echo "No streamlit entrypoint found. Set CITL_STREAMLIT_ENTRYPOINT in config/runtime.env"
  exit 2
fi

python3 -m streamlit run "$EP"
