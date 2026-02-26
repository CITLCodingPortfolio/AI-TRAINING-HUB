#!/usr/bin/env bash
set -euo pipefail
# CITL_CWD_GUARD_V2
if ! pwd >/dev/null 2>&1; then
  cd "$HOME" 2>/dev/null || cd / 2>/dev/null || true
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_DIR"

if command -v apt-get >/dev/null 2>&1; then
  if command -v sudo >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-venv python3-pip python3-dev python3-tk xdg-utils
  fi
fi

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
python -m pip install -U pip setuptools wheel

# Prefer requirements folder if present
if [[ -f "requirements/requirements-linux.txt" ]]; then
  pip install -r requirements/requirements-linux.txt
elif [[ -f "requirements/requirements.txt" ]]; then
  pip install -r requirements/requirements.txt
elif [[ -f "requirements.txt" ]]; then
  pip install -r requirements.txt
fi

echo "Setup complete."
