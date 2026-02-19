#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
python scripts/demo/run_bot.py "$@"