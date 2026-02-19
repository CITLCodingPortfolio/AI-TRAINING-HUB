#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate
START="${1:-8787}"
FREE_PORT="$(python - <<'PY'
import socket, os
start=int(os.environ.get("START_PORT","8787"))
for p in range(start, start+50):
    s=socket.socket()
    try:
        s.bind(("127.0.0.1", p))
        s.close()
        print(p)
        raise SystemExit(0)
    except OSError:
        pass
    finally:
        try: s.close()
        except: pass
raise SystemExit("No free port found")
PY
)"
export AI_TRAINING_HUB_API_PORT="$FREE_PORT"
echo "Starting Faux API on port $FREE_PORT ..."
echo "Health: http://127.0.0.1:$FREE_PORT/health"
python -m bots.api_server --port "$FREE_PORT"