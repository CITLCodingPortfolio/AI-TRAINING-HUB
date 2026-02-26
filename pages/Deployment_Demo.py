import os
import re
import sys
import json
import shlex
import importlib
import inspect
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import streamlit as st

# =========================
# Core helpers
# =========================
def hub_root() -> Path:
    here = Path(__file__).resolve()
    # pages/ -> HUB
    for p in [here.parent] + list(here.parents):
        if (p / "bots").exists() and (p / ".venv").exists():
            return p
        if (p / "bots").exists() and (p / "scripts").exists():
            return p
    # fallback
    return here.parents[1]

HUB = hub_root()
BOTS_DIR = HUB / "bots"
SCRIPTS_DIR = HUB / "scripts"

if str(HUB) not in sys.path:
    sys.path.insert(0, str(HUB))

def discover_bots() -> List[str]:
    bots: List[str] = []
    if not BOTS_DIR.exists():
        return bots
    for p in BOTS_DIR.glob("*.py"):
        name = p.stem
        if name.startswith("_"):
            continue
        if name in {"__init__", "run_bot", "citl_cli"}:
            continue
        # convention: *_bot or demo_host_bot etc
        if name.endswith("_bot") or name in {"demo_host_bot"}:
            bots.append(name)
    return sorted(set(bots), key=lambda s: s.lower())

def normalize_result(bot: str, out: Any) -> Dict[str, Any]:
    # allow bot to return plain dict, str, list, etc.
    if isinstance(out, dict):
        return {"bot": bot, "ok": True, "result": out}
    return {"bot": bot, "ok": True, "result": {"output": out}}

def try_direct_import(bot: str, message: str) -> Optional[Dict[str, Any]]:
    try:
        mod = importlib.import_module(f"bots.{bot}")
    except Exception:
        return None

    # run(message)
    fn = getattr(mod, "run", None)
    if callable(fn):
        try:
            sig = inspect.signature(fn)
            if len(sig.parameters) >= 1:
                out = fn(message)
            else:
                out = fn()
            return normalize_result(bot, out)
        except Exception as e:
            return {"bot": bot, "ok": False, "result": {"error": str(e)}}

    # BOT.run(message)
    for attr in ("BOT", "bot"):
        obj = getattr(mod, attr, None)
        if obj is not None and callable(getattr(obj, "run", None)):
            try:
                out = obj.run(message)
                return normalize_result(bot, out)
            except Exception as e:
                return {"bot": bot, "ok": False, "result": {"error": str(e)}}

    return None

def extract_json_maybe(text: str) -> Optional[Dict[str, Any]]:
    t = (text or "").strip()
    if not t:
        return None
    if t.startswith("{") and t.endswith("}"):
        try:
            return json.loads(t)
        except Exception:
            pass
    # fallback: last {...} block
    # (simple greedy heuristic)
    m = re.findall(r"\{[\s\S]*\}", t)
    for chunk in reversed(m):
        try:
            return json.loads(chunk)
        except Exception:
            continue
    return None

def try_run_bot_py(bot: str, message: str) -> Dict[str, Any]:
    run_bot = BOTS_DIR / "run_bot.py"
    if not run_bot.exists():
        return {"bot": bot, "ok": False, "result": {"error": "bots/run_bot.py not found"}}

    attempts = [
        [sys.executable, str(run_bot), "--bot", bot, "--message", message],
        [sys.executable, str(run_bot), "--bot", bot, "--msg", message],
        [sys.executable, str(run_bot), bot, message],
    ]
    last = ""
    for cmd in attempts:
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, cwd=str(HUB))
            last = out
            obj = extract_json_maybe(out)
            if obj:
                obj.setdefault("bot", bot)
                obj.setdefault("ok", True)
                return obj
            if out.strip():
                return {"bot": bot, "ok": True, "result": {"raw_output": out.strip()}}
        except subprocess.CalledProcessError as e:
            last = e.output or ""
            continue
    return {"bot": bot, "ok": False, "result": {"error": "Unable to run bot via run_bot.py", "last_output": last.strip()}}

def run_bot(bot: str, message: str) -> Dict[str, Any]:
    res = try_direct_import(bot, message)
    if res is not None:
        return res
    return try_run_bot_py(bot, message)

def bot_doc(bot: str) -> str:
    p = BOTS_DIR / f"{bot}.py"
    if not p.exists():
        return "No bot file found."
    try:
        s = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return "Unable to read bot file."
    # module docstring
    m = re.match(r'^\s*(?P<q>["\']{3})(?P<body>[\s\S]*?)(?P=q)', s)
    if m:
        return m.group("body").strip()
    return "No module docstring."

# =========================
# Built-in CLI command layer
# =========================
HELP_TEXT = """\
Commands:
- /help                         show this help
- /list                         list available bots
- /use <bot_id>                 set active bot
- /describe                     show docstring + file path for active bot
- /run "<message>"              run active bot with message (quotes recommended)
- /run <bot_id> "<message>"     run specified bot
- /clear                        clear output + history
"""

def ensure_state():
    st.session_state.setdefault("bots", discover_bots())
    st.session_state.setdefault("active_bot", (st.session_state["bots"][0] if st.session_state["bots"] else "demo_host_bot"))
    st.session_state.setdefault("cli_history", [])   # list[str]
    st.session_state.setdefault("cli_output", [])    # list[dict]
    st.session_state.setdefault("chat_history", {})  # bot -> list[(role, text)]

def append_output(obj: Dict[str, Any]):
    st.session_state["cli_output"].append(obj)

def render_result(obj: Dict[str, Any]):
    bot = obj.get("bot","bot")
    ok = obj.get("ok", True)
    res = obj.get("result", {})

    st.markdown(f"### {bot} — {'✅ OK' if ok else '❌ FAIL'}")
    if isinstance(res, dict):
        # display common fields nicely
        if "triage_plan" in res and isinstance(res["triage_plan"], list):
            st.markdown("**Triage plan**")
            for i, step in enumerate(res["triage_plan"], 1):
                st.write(f"{i}. {step}")
        if "notes" in res and isinstance(res["notes"], str) and res["notes"].strip():
            st.markdown("**Notes**")
            st.write(res["notes"].strip())

        leftovers = {k:v for k,v in res.items() if k not in {"triage_plan","notes"}}
        if leftovers:
            st.markdown("**Details**")
            st.json(leftovers)
    else:
        st.write(res)

def handle_command(cmdline: str):
    cmdline = (cmdline or "").strip()
    if not cmdline:
        return

    st.session_state["cli_history"].append(cmdline)

    # /run with quotes, etc.
    if cmdline == "/help":
        append_output({"bot":"cli", "ok":True, "result":{"notes": HELP_TEXT}})
        return

    if cmdline == "/list":
        bots = st.session_state["bots"]
        append_output({"bot":"cli", "ok":True, "result":{"bots": bots, "notes": f"{len(bots)} bot(s) found."}})
        return

    if cmdline.startswith("/use "):
        bot = cmdline.split(" ", 1)[1].strip()
        if bot in st.session_state["bots"]:
            st.session_state["active_bot"] = bot
            append_output({"bot":"cli", "ok":True, "result":{"notes": f"Active bot set to: {bot}"}})
        else:
            append_output({"bot":"cli", "ok":False, "result":{"error": f"Unknown bot: {bot}"}})
        return

    if cmdline == "/describe":
        bot = st.session_state["active_bot"]
        doc = bot_doc(bot)
        path = str((BOTS_DIR / f"{bot}.py").resolve())
        append_output({"bot":"cli", "ok":True, "result":{"bot": bot, "path": path, "doc": doc}})
        return

    if cmdline == "/clear":
        st.session_state["cli_output"] = []
        st.session_state["cli_history"] = []
        return

    if cmdline.startswith("/run"):
        # /run "<message>" or /run bot "<message>"
        try:
            parts = shlex.split(cmdline)
        except Exception as e:
            append_output({"bot":"cli", "ok":False, "result":{"error": f"Parse error: {e}"}})
            return

        if len(parts) == 1:
            append_output({"bot":"cli", "ok":False, "result":{"error":"Usage: /run \"message\" OR /run bot_id \"message\""}})
            return

        if len(parts) == 2:
            bot = st.session_state["active_bot"]
            msg = parts[1]
        else:
            bot = parts[1]
            msg = " ".join(parts[2:]).strip()

        if bot not in st.session_state["bots"]:
            append_output({"bot":"cli", "ok":False, "result":{"error": f"Unknown bot: {bot}"}})
            return

        obj = run_bot(bot, msg)
        append_output(obj)
        return

    append_output({"bot":"cli", "ok":False, "result":{"error":"Unknown command. Try /help"}})

# =========================
# UI
# =========================
st.set_page_config(page_title="Deployment Demo — Live CLI", layout="wide")
ensure_state()

st.title("Deployment Demo — Live CLI + Bot Chat")
st.caption("High priority: a working built-in CLI to demo bots from a dropdown list, with common commands (/list, /use, /run, /describe).")

left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("Bot Control")
    bots = discover_bots()
    st.session_state["bots"] = bots

    if not bots:
        st.error("No bots found in HUB/bots. Expected files like it_ticket_bot.py")
    else:
        # bot dropdown
        active = st.selectbox("Active bot", options=bots, index=max(0, bots.index(st.session_state["active_bot"])) if st.session_state["active_bot"] in bots else 0)
        st.session_state["active_bot"] = active

        st.markdown("**Common commands**")
        st.code("/list\n/use <bot_id>\n/run \"message\"\n/describe\n/help", language="text")

        st.markdown("**Quick run (no commands)**")
        msg = st.text_area("Message", value="", height=120, placeholder="Type the input to send to the selected bot…")
        if st.button("Run Bot", use_container_width=True):
            obj = run_bot(st.session_state["active_bot"], msg)
            append_output(obj)

        st.markdown("---")
        st.markdown("**Command bar (built-in CLI)**")
        cmd = st.text_input("CLI", value="", placeholder='Try: /list   or: /run "Create VPN access ticket due Friday"')
        cols = st.columns([1,1,1])
        if cols[0].button("Send Command"):
            handle_command(cmd)
        if cols[1].button("Help"):
            handle_command("/help")
        if cols[2].button("Clear"):
            handle_command("/clear")

with right:
    tabs = st.tabs(["Live CLI Output", "Chat", "Server", "Glossary (low priority)"])

    with tabs[0]:
        st.subheader("Output")
        if not st.session_state["cli_output"]:
            st.info("Run a bot or a CLI command to see output here.")
        else:
            # render newest first
            for obj in reversed(st.session_state["cli_output"][-30:]):
                render_result(obj)
                st.markdown("---")

        with st.expander("CLI History"):
            st.write("\n".join(st.session_state["cli_history"][-50:]) or "(empty)")

    with tabs[1]:
        st.subheader("Direct Chat with Selected Bot")
        bot = st.session_state["active_bot"]
        st.caption("This is a simple, session-based chat. Each user message triggers one bot invocation; results are shown inline.")

        st.session_state["chat_history"].setdefault(bot, [])
        history = st.session_state["chat_history"][bot]

        for role, text in history:
            with st.chat_message(role):
                st.write(text)

        user_msg = st.chat_input(f"Message to {bot}…")
        if user_msg:
            history.append(("user", user_msg))
            obj = run_bot(bot, user_msg)
            # summarize result for chat display
            res = obj.get("result", {})
            if isinstance(res, dict):
                # prefer notes/output if present
                reply = res.get("notes") or res.get("output") or json.dumps(res, ensure_ascii=False, indent=2)
            else:
                reply = str(res)
            history.append(("assistant", reply))

            st.session_state["chat_history"][bot] = history
            st.rerun()

    with tabs[2]:
        st.subheader("Server Status")
        st.write("This page focuses on *live bot demos*. If you also run a demo API server, start it from a terminal using your existing scripts.")
        st.code(
            "Ubuntu:\n"
            "  bash scripts/linux/setup.sh\n"
            "  bash scripts/linux/demo_server.sh\n"
            "  bash scripts/linux/run_bot.sh --bot <bot_id> --input-file data/demo/sample_ticket.txt\n",
            language="bash"
        )
        st.caption("Optional improvement later: in-app process supervisor for demo_server (start/stop/log tail).")

    with tabs[3]:
        st.subheader("Glossary")
        st.write("Low priority. Keep it collapsed by default. Replace with searchable docs later.")
        with st.expander("Show glossary"):
            st.write(
                "- Tip: move definitions into a searchable help system.\n"
                "- Future: add predictive command search in the CLI."
            )

# Footer
st.markdown("---")
st.caption(f"HUB: {HUB}")
