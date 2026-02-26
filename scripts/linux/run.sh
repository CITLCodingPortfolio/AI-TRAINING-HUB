#!/usr/bin/env bash
set -euo pipefail
# CITL_CWD_GUARD_V2
if ! pwd >/dev/null 2>&1; then
  cd "$HOME" 2>/dev/null || cd / 2>/dev/null || true
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_DIR"

if [[ ! -d ".venv" ]]; then
  echo "venv missing. Run: ./scripts/linux/setup.sh"
  exit 1
fi

. .venv/bin/activate

# Canonical entry:
python3 hub_launcher.py
