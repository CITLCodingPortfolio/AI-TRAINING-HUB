from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import importlib.util
import traceback
from typing import Callable, Dict, Any, Optional, List
@dataclass
class BotSpec:
    bot_id: str
    bot_name: str
    path: Path
    run: Callable[[str, Dict[str, str]], str]
def _load_module(py_path: Path):
    spec = importlib.util.spec_from_file_location(py_path.stem, py_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {py_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod
def discover_bots(bots_dir: Path) -> List[BotSpec]:
    bots: List[BotSpec] = []
    if not bots_dir.exists():
        return bots
    for p in sorted(bots_dir.glob("*.py")):
        if p.name.startswith("_") or p.name.startswith("__"):
            continue
        try:
            mod = _load_module(p)
            run_fn = getattr(mod, "run", None)
            if not callable(run_fn):
                continue
            bot_id = getattr(mod, "BOT_ID", p.stem)
            bot_name = getattr(mod, "BOT_NAME", bot_id)
            bots.append(BotSpec(bot_id=str(bot_id), bot_name=str(bot_name), path=p, run=run_fn))
        except Exception:
            # skip broken bots, but don't crash
            continue
    # If none found, create a fallback demo bot
    if not bots:
        def _fallback_run(input_text: str, files: Dict[str, str]) -> str:
            fkeys = ", ".join(files.keys()) if files else "(no files)"
            return f"[FallbackBot] Received input ({len(input_text)} chars). Files: {fkeys}"
        bots.append(BotSpec(bot_id="fallback_bot", bot_name="Fallback Bot", path=bots_dir / "fallback", run=_fallback_run))
    return bots
def run_bot(bots_dir: Path, bot_id: str, input_text: str, files: Dict[str, str]) -> str:
    bots = discover_bots(bots_dir)
    by_id = {b.bot_id: b for b in bots}
    if bot_id not in by_id:
        known = ", ".join(sorted(by_id.keys()))
        return f"ERROR: Unknown bot_id='{bot_id}'. Known: {known}"
    try:
        return str(by_id[bot_id].run(input_text, files))
    except Exception:
        return "BOT_RUNTIME_ERROR:\n" + traceback.format_exc()
