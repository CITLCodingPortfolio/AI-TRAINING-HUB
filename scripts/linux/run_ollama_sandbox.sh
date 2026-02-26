#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# run_ollama_sandbox.sh — Launch the Ollama Bot CLI Sandbox (IRC-style colors)
#
# Usage:
#   bash scripts/linux/run_ollama_sandbox.sh
#   bash scripts/linux/run_ollama_sandbox.sh --bot student_bot
#   bash scripts/linux/run_ollama_sandbox.sh --bot student_bot --color "#FF6B6B"
#   bash scripts/linux/run_ollama_sandbox.sh --model llama3.2
#   bash scripts/linux/run_ollama_sandbox.sh --no-stream
#
# All flags are passed directly to bots/ollama_sandbox.py
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail
# CITL_CWD_GUARD_V2
if ! pwd >/dev/null 2>&1; then
  cd "$HOME" 2>/dev/null || cd / 2>/dev/null || true
fi


REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

VENV_PY="$REPO_ROOT/.venv/bin/python"
if [[ ! -f "$VENV_PY" ]]; then
    echo "ERROR: venv not found at .venv/  Run:  bash scripts/linux/setup.sh" >&2
    exit 1
fi

echo ""
echo "  AI Training Hub — Ollama Bot Sandbox"
echo "  python -m bots.ollama_sandbox $*"
echo ""

exec "$VENV_PY" -m bots.ollama_sandbox "$@"
