#!/usr/bin/env python3
import argparse
import importlib
import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

def _has_tty() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False

def _try_rich():
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich import box
        return Console(), Panel, Table, box
    except Exception:
        return None, None, None, None

CONSOLE, Panel, Table, box = _try_rich()

def rprint(*a, **k):
    if CONSOLE:
        CONSOLE.print(*a, **k)
    else:
        print(*a)

def _extract_json_maybe(text: str) -> Dict[str, Any] | None:
    # If output includes extra lines (like "BOT OUTPUT (...)"), grab the last {...}
    if not text:
        return None
    # quick path: whole output is json
    t = text.strip()
    if t.startswith("{") and t.endswith("}"):
        try:
            return json.loads(t)
        except Exception:
            pass
    # fallback: find last json object
    m = list(re.finditer(r'\{(?:[^{}]|(?R))*\}', t, flags=re.S))
    if m:
        for mm in reversed(m):
            chunk = mm.group(0)
            try:
                return json.loads(chunk)
            except Exception:
                continue
    return None

def _pretty_result(obj: Dict[str, Any]):
    bot = obj.get("bot") or "bot"
    ok = obj.get("ok", True)
    res = obj.get("result") if isinstance(obj.get("result"), dict) else obj

    if CONSOLE and Panel:
        title = f"[bold]{bot}[/bold]  " + ("[green]OK[/green]" if ok else "[red]FAIL[/red]")
        CONSOLE.print(Panel.fit(title, border_style="cyan"))
    else:
        print(f"\n=== {bot} === {'OK' if ok else 'FAIL'}\n")

    # Common shapes: triage_plan(list), notes(str), etc.
    if isinstance(res, dict):
        # triage_plan
        plan = res.get("triage_plan")
        if isinstance(plan, list) and plan:
            rprint("\n[bold]Triage plan[/bold]" if CONSOLE else "\nTriage plan")
            for i, step in enumerate(plan, 1):
                rprint(f"  {i}. {step}")
        # notes
        notes = res.get("notes")
        if isinstance(notes, str) and notes.strip():
            rprint("\n[bold]Notes[/bold]" if CONSOLE else "\nNotes")
            rprint(notes.strip())

        # print remaining keys
        leftovers = {k: v for k, v in res.items() if k not in {"triage_plan", "notes"}}
        if leftovers:
            rprint("\n[bold]Details[/bold]" if CONSOLE else "\nDetails")
            if CONSOLE and Table:
                tbl = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
                tbl.add_column("Key")
                tbl.add_column("Value")
                for k, v in leftovers.items():
                    tbl.add_row(str(k), json.dumps(v, ensure_ascii=False, indent=2) if not isinstance(v, str) else v)
                CONSOLE.print(tbl)
            else:
                print(json.dumps(leftovers, ensure_ascii=False, indent=2))
    else:
        rprint(res)

def _run_bot_direct_import(bot: str, message: str) -> Dict[str, Any] | None:
    """
    Best-effort direct import runner:
      - bots.<bot>.run(message)
      - bots.<bot>.main(message?) / main()
      - bots.<bot>.BOT.run(message)
    Returns normalized dict or None if unknown interface.
    """
    try:
        mod = importlib.import_module(f"bots.{bot}")
    except Exception:
        return None

    # 1) run(message)
    if hasattr(mod, "run") and callable(getattr(mod, "run")):
        fn = getattr(mod, "run")
        try:
            sig = inspect.signature(fn)
            if len(sig.parameters) >= 1:
                out = fn(message)
            else:
                out = fn()
            return {"bot": bot, "ok": True, "result": out}
        except Exception as e:
            return {"bot": bot, "ok": False, "result": {"error": str(e)}}

    # 2) BOT.run(message)
    for name in ("BOT", "bot"):
        obj = getattr(mod, name, None)
        if obj is not None and hasattr(obj, "run") and callable(getattr(obj, "run")):
            try:
                out = obj.run(message)
                return {"bot": bot, "ok": True, "result": out}
            except Exception as e:
                return {"bot": bot, "ok": False, "result": {"error": str(e)}}

    # 3) main()
    if hasattr(mod, "main") and callable(getattr(mod, "main")):
        fn = getattr(mod, "main")
        try:
            sig = inspect.signature(fn)
            if len(sig.parameters) >= 1:
                out = fn(message)
            else:
                out = fn()
            return {"bot": bot, "ok": True, "result": out}
        except SystemExit:
            return {"bot": bot, "ok": True, "result": {"notes": "Bot exited."}}
        except Exception as e:
            return {"bot": bot, "ok": False, "result": {"error": str(e)}}

    return None

def _run_via_run_bot_py(bot: str, message: str) -> Dict[str, Any]:
    """
    Fallback: call existing bots/run_bot.py using a few common arg layouts.
    We expect it to print JSON somewhere in stdout.
    """
    here = Path(__file__).resolve().parent
    run_bot = here / "run_bot.py"
    if not run_bot.exists():
        return {"bot": bot, "ok": False, "result": {"error": "bots/run_bot.py not found"}}

    attempts = [
        # common patterns
        [sys.executable, str(run_bot), "--bot", bot, "--message", message],
        [sys.executable, str(run_bot), "--bot", bot, "--msg", message],
        [sys.executable, str(run_bot), bot, message],
        [sys.executable, str(run_bot), bot],
    ]

    last_out = ""
    for cmd in attempts:
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            last_out = out
            obj = _extract_json_maybe(out)
            if obj is not None:
                # normalize
                if "bot" not in obj:
                    obj["bot"] = bot
                if "ok" not in obj:
                    obj["ok"] = True
                return obj
            # if no json but something printed, wrap it
            if out.strip():
                return {"bot": bot, "ok": True, "result": {"raw_output": out.strip()}}
        except subprocess.CalledProcessError as e:
            last_out = e.output or ""
            continue

    return {"bot": bot, "ok": False, "result": {"error": "Could not execute run_bot.py with known arg patterns", "last_output": last_out.strip()}}

def interactive_loop(bot: str, message: str):
    # Run the bot
    rprint("\n[bold]Running bot...[/bold]" if CONSOLE else "\nRunning bot...")

    obj = _run_bot_direct_import(bot, message)
    if obj is None:
        obj = _run_via_run_bot_py(bot, message)

    _pretty_result(obj)

    # Optional: simple interactive follow-up scaffold (ticket-style)
    rprint("\n[bold]Next steps (interactive)[/bold]" if CONSOLE else "\nNext steps (interactive)")
    rprint("1) Save output to a ticket markdown file")
    rprint("2) Run again with a new message")
    rprint("3) Exit")

    while True:
        try:
            choice = input("\nSelect [1/2/3]: ").strip()
        except EOFError:
            choice = "3"
        if choice == "1":
            outdir = Path.home() / "CITL_TICKETS"
            outdir.mkdir(parents=True, exist_ok=True)
            fn = outdir / f"{bot}_ticket_{os.getpid()}.md"

            # render minimal ticket
            res = obj.get("result", {})
            plan = res.get("triage_plan", []) if isinstance(res, dict) else []
            notes = res.get("notes", "") if isinstance(res, dict) else ""

            md = []
            md.append(f"# Ticket Triage Output: {bot}\n")
            md.append(f"- Generated: {__import__('datetime').datetime.utcnow().isoformat()}Z\n")
            if plan:
                md.append("## Triage Plan\n")
                for i, step in enumerate(plan, 1):
                    md.append(f"{i}. {step}\n")
            if notes:
                md.append("\n## Notes\n")
                md.append(notes + "\n")

            fn.write_text("".join(md), encoding="utf-8")
            rprint(f"\nSaved: {fn}")
        elif choice == "2":
            new_msg = input("\nEnter new message: ").rstrip("\n")
            if new_msg.strip():
                return interactive_loop(bot, new_msg)
        elif choice == "3":
            rprint("\nBye.\n")
            return
        else:
            rprint("Choose 1, 2, or 3.")

def main():
    ap = argparse.ArgumentParser(description="CITL Interactive Bot CLI (non-JSON, terminal-friendly)")
    ap.add_argument("--bot", required=True, help="Bot module name (e.g., it_ticket_bot)")
    ap.add_argument("--message", default="", help="Message/input for bot")
    ap.add_argument("--json", action="store_true", help="Print raw JSON output only (no interactive UI)")
    args = ap.parse_args()

    bot = args.bot.strip()
    msg = args.message

    if not msg:
        try:
            msg = input("Message: ").rstrip("\n")
        except EOFError:
            msg = ""

    if args.json or not _has_tty():
        obj = _run_bot_direct_import(bot, msg)
        if obj is None:
            obj = _run_via_run_bot_py(bot, msg)
        print(json.dumps(obj, ensure_ascii=False, indent=2))
        return

    interactive_loop(bot, msg)

if __name__ == "__main__":
    main()
