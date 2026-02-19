#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_DIR"
echo "== AI TRAINING HUB (Ubuntu Wizard) =="
echo "Repo: $REPO_DIR"
# --- system deps ---
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 missing. Install with:"
  echo "  sudo apt-get update && sudo apt-get install -y python3 python3-venv"
  exit 1
fi
# --- venv ---
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -U pip
# --- requirements selection ---
REQ=""
if [ -f "requirements/requirements.txt" ]; then REQ="requirements/requirements.txt"; fi
if [ -z "$REQ" ] && [ -f "requirements.txt" ]; then REQ="requirements.txt"; fi
if [ -z "$REQ" ] && [ -f "requirements/base.txt" ]; then REQ="requirements/base.txt"; fi
# --- install deps: wheelhouse if present, else pip online ---
if [ -n "$REQ" ]; then
  if [ -d "wheelhouse" ]; then
    echo "Installing from OFFLINE wheelhouse/ ..."
    pip install --no-index --find-links wheelhouse -r "$REQ"
  else
    echo "Installing deps (pip)..."
    pip install -r "$REQ"
  fi
else
  echo "WARNING: No requirements file found. Skipping pip install."
fi
# --- free port function ---
port_free() {
  local p="$1"
  python - <<PY >/dev/null 2>&1
import socket, sys
p=int(sys.argv[1])
s=socket.socket()
try:
  s.bind(("127.0.0.1", p))
  print("OK")
except OSError:
  sys.exit(1)
finally:
  s.close()
PY
}
next_free_port() {
  local p="$1"
  while true; do
    if port_free "$p" ; then echo "$p"; return 0; fi
    p=$((p+1))
  done
}
# --- start API (optional) ---
API_PORT_FILE="data/runtime/api_port.txt"
mkdir -p data/runtime
if [ -f "bots/api_server.py" ]; then
  ap="$(next_free_port 8787)"
  echo "$ap" > "$API_PORT_FILE"
  echo "Starting API: http://127.0.0.1:${ap} ..."
  nohup python -m bots.api_server --host 127.0.0.1 --port "$ap" > logs/api_server_stdout.log 2>&1 &
else
  echo "WARNING: bots/api_server.py not found. API not started."
fi
# --- start Hub ---
hp="$(next_free_port 8502)"
echo "Launching Hub: http://localhost:${hp}"
python -m streamlit run app/hub.py --server.port "$hp"