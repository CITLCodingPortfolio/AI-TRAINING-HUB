from __future__ import annotations
import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from pathlib import Path
from bots.registry import get_registry
LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "api_server.log"
def log_line(s: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} {s}\n"
    if LOG_FILE.exists():
        prev = LOG_FILE.read_text(encoding="utf-8", errors="ignore")
        LOG_FILE.write_text(prev + line, encoding="utf-8", errors="replace")
    else:
        LOG_FILE.write_text(line, encoding="utf-8", errors="replace")
def json_bytes(obj) -> bytes:
    return (json.dumps(obj, indent=2) + "\n").encode("utf-8")
class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj):
        body = json_bytes(obj)
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, fmt, *args):
        # keep console quieter; logs go to file via log_line()
        return
    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/":
            self._send(200, {
                "ok": True,
                "service": "ai-training-hub-faux-api",
                "endpoints": ["/health", "/bots", "/logs", "/run"]
            })
            return
        if p == "/health":
            self._send(200, {"ok": True, "service": "ai-training-hub-faux-api"})
            return
        if p == "/bots":
            reg = get_registry()
            bots = [{
                "bot_id": b.bot_id,
                "name": b.name,
                "color": b.color,
                "description": b.description,
                "demos": [{"title": d.title, "description": d.description, "args": d.args} for d in b.demos],
            } for b in reg.values()]
            self._send(200, {"ok": True, "bots": sorted(bots, key=lambda x: x["bot_id"])})
            return
        if p == "/logs":
            n = 200
            try:
                qs = urlparse(self.path).query
                if "n=" in qs:
                    n = int(qs.split("n=")[1].split("&")[0])
            except Exception:
                pass
            if LOG_FILE.exists():
                lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
            else:
                lines = []
            self._send(200, {"ok": True, "lines": lines})
            return
        self._send(404, {"ok": False, "error": f"not found: {p}"})
    def do_POST(self):
        p = urlparse(self.path).path
        if p != "/run":
            self._send(404, {"ok": False, "error": f"not found: {p}"})
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8", errors="replace"))
        except Exception as e:
            self._send(400, {"ok": False, "error": f"bad json: {e}"})
            return
        bot_id = (payload.get("bot_id") or "").strip()
        args = payload.get("args") or {}
        log_line(f"RUN bot_id={bot_id} args={args}")
        reg = get_registry()
        if bot_id not in reg:
            self._send(400, {"ok": False, "error": f"Unknown bot_id: {bot_id}"})
            return
        # For now: just echo back (stable demo). You can wire real bot runners later.
        self._send(200, {"ok": True, "bot_id": bot_id, "args": args, "note": "Demo API received request."})
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    srv = HTTPServer((args.host, args.port), Handler)
    print(f"Faux API listening on http://{args.host}:{args.port}")
    srv.serve_forever()
if __name__ == "__main__":
    main()
