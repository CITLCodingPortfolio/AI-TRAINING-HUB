#!/usr/bin/env bash
set -euo pipefail
bash scripts/ollama/bootstrap.sh
bash scripts/citl/write_runtime_env.sh
echo "[bootstrap] done."
