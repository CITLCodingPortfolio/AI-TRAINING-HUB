from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI(title="AI-Training-Hub Demo API", version="1.0")
LOG_PATH = Path("logs") / "demo_api.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
def log(event: str, payload: Dict[str, Any]) -> None:
    rec = {"ts": datetime.utcnow().isoformat() + "Z", "event": event, "payload": payload}
    LOG_PATH.write_text(LOG_PATH.read_text(encoding="utf-8", errors="ignore") + json.dumps(rec) + "\n"
                        if LOG_PATH.exists() else json.dumps(rec) + "\n",
                        encoding="utf-8")
class FileBlob(BaseModel):
    name: str
    text: str
class RunRequest(BaseModel):
    bot: str
    input: str = ""
    files: List[FileBlob] = []
def run_bot_local(bot: str, user_input: str) -> Any:
    from bots.registry import get_registry  # local import
    reg = get_registry()
    if bot not in reg:
        return {"error": f"Unknown bot: {bot}", "available": sorted(list(reg.keys()))}
    impl = reg[bot]
    if callable(impl) and not hasattr(impl, "run") and not hasattr(impl, "invoke"):
        return impl(user_input)
    obj = impl() if callable(impl) else impl
    if hasattr(obj, "run"):
        return obj.run(user_input)
    if hasattr(obj, "invoke"):
        return obj.invoke(user_input)
    return str(obj)
@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}
@app.get("/bots")
def bots() -> Dict[str, Any]:
    from bots.registry import list_bots
    return {"bots": list_bots()}
@app.post("/run")
def run(req: RunRequest) -> Dict[str, Any]:
    combined = req.input or ""
    if req.files:
        combined += "\n\n[ATTACHED_FILES]\n"
        for f in req.files:
            combined += f"\n--- {f.name} ---\n{f.text}\n"
    log("run", {"bot": req.bot, "chars": len(combined), "files": [f.name for f in req.files]})
    result = run_bot_local(req.bot, combined)
    return {"bot": req.bot, "result": result}