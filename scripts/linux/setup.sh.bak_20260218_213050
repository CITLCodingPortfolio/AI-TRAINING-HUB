#!/usr/bin/env bash
set -euo pipefail
echo "== AI-Training-Hub Setup (Ubuntu 24) =="
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip ffmpeg
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
# Preferred order
if [ -f "requirements/requirements-lock.txt" ]; then
  pip install -r requirements/requirements-lock.txt
fi
if [ -f "requirements/requirements-demo.txt" ]; then
  pip install -r requirements/requirements-demo.txt
fi
if [ -f "requirements/requirements-transcribe.txt" ]; then
  pip install -r requirements/requirements-transcribe.txt
fi
if [ -f "requirements/requirements-rag.txt" ]; then
  pip install -r requirements/requirements-rag.txt
fi
if [ -f "requirements/requirements.txt" ]; then
  pip install -r requirements/requirements.txt
elif [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi
echo "Setup complete."
echo "Next:"
echo "  1) Start demo API:  bash scripts/linux/demo_server.sh"
echo "  2) Start Hub GUI:   bash scripts/linux/run.sh"