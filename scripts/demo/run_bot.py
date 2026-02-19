from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any
import requests
def run_local(bot: str, text: str) -> Any:
    from bots.registry import get_registry
    reg = get_registry()
    if bot not in reg:
        return {"error": f"Unknown bot: {bot}", "available": sorted(reg.keys())}
    impl = reg[bot]
    if callable(impl) and not hasattr(impl, "run") and not hasattr(impl, "invoke"):
        return impl(text)
    obj = impl() if callable(impl) else impl
    if hasattr(obj, "run"):
        return obj.run(text)
    if hasattr(obj, "invoke"):
        return obj.invoke(text)
    return str(obj)
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", required=True)
    ap.add_argument("--api", default="http://127.0.0.1:8787")
    ap.add_argument("--no-server", action="store_true")
    ap.add_argument("--input", default="")
    ap.add_argument("--input-file")
    ap.add_argument("--file", action="append", default=[])
    args = ap.parse_args()
    text = args.input or ""
    if args.input_file:
        text = Path(args.input_file).read_text(encoding="utf-8", errors="ignore")
    files = []
    for fp in args.file:
        p = Path(fp)
        files.append({"name": p.name, "text": p.read_text(encoding="utf-8", errors="ignore")})
    if args.no_server:
        combined = text
        if files:
            combined += "\n\n[ATTACHED_FILES]\n"
            for f in files:
                combined += f"\n--- {f['name']} ---\n{f['text']}\n"
        out = run_local(args.bot, combined)
        print(json.dumps({"bot": args.bot, "result": out}, indent=2, ensure_ascii=False))
        return 0
    r = requests.post(f"{args.api}/run", json={"bot": args.bot, "input": text, "files": files}, timeout=120)
    r.raise_for_status()
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())