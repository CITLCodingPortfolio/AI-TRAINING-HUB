from __future__ import annotations
import hashlib
import json
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests
import streamlit as st
st.set_page_config(page_title="Deployment Demo", layout="wide")
API_DEFAULT = "http://127.0.0.1:8787"
# --------- Styling (terminal + readable alternating bot colors) ----------
BOT_STYLES = [
    ("#0b1f2a", "#9fe7ff"),  # dark blue bg, bright cyan text
    ("#23112a", "#ffb3ff"),  # dark purple bg, light magenta text
    ("#1e2411", "#d8ff9f"),  # olive bg, lime text
    ("#2a1b0b", "#ffd49f"),  # brown bg, orange text
]
CSS = """
<style>
.term {
  border: 1px solid rgba(255,255,255,.12);
  background: rgba(10,10,10,.55);
  border-radius: 12px;
  padding: 12px;
  height: 360px;
  overflow-y: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  font-size: 13px;
  line-height: 1.35;
}
.term-line { margin: 6px 0; white-space: pre-wrap; word-break: break-word; }
.cmd { color: rgba(255,255,255,.65); }
.user { color: #9fe7ff; font-weight: 600; }
.err  { color: #ff7a7a; font-weight: 700; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
# --------- Helpers ----------
def hash_idx(s: str, n: int) -> int:
    h = hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()
    return int(h[:8], 16) % n
def bot_box(bot: str, text: str) -> str:
    bg, fg = BOT_STYLES[hash_idx(bot, len(BOT_STYLES))]
    safe = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<div class="term-line" style="background:{bg};color:{fg};padding:10px;border-radius:10px;"><b>BOT: {bot}</b>\\n{safe}</div>'
def user_box(text: str) -> str:
    safe = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<div class="term-line user"><b>USER</b>\\n{safe}</div>'
def cmd_line(cmd: str) -> str:
    safe = cmd.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<div class="term-line cmd">$ {safe}</div>'
def err_line(msg: str) -> str:
    safe = msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<div class="term-line err">ERROR: {safe}</div>'
def api_up(api: str) -> bool:
    try:
        r = requests.get(f"{api}/health", timeout=1.2)
        return r.ok and r.json().get("ok") is True
    except Exception:
        return False
def api_bots(api: str) -> List[str]:
    try:
        r = requests.get(f"{api}/bots", timeout=2)
        if r.ok:
            return list(r.json().get("bots", []))
    except Exception:
        pass
    return []
def run_via_api(api: str, bot: str, input_text: str, files: List[Tuple[str, str]]) -> Any:
    payload = {
        "bot": bot,
        "input": input_text or "",
        "files": [{"name": n, "text": t} for (n, t) in files],
    }
    r = requests.post(f"{api}/run", json=payload, timeout=120)
    r.raise_for_status()
    return r.json().get("result")
def run_local(bot: str, input_text: str, files: List[Tuple[str, str]]) -> Any:
    from bots.registry import get_registry
    reg = get_registry()
    if bot not in reg:
        return {"error": f"Unknown bot: {bot}", "available": sorted(list(reg.keys()))}
    combined = input_text or ""
    if files:
        combined += "\n\n[ATTACHED_FILES]\n"
        for n, t in files:
            combined += f"\n--- {n} ---\n{t}\n"
    impl = reg[bot]
    if callable(impl) and not hasattr(impl, "run") and not hasattr(impl, "invoke"):
        return impl(combined)
    obj = impl() if callable(impl) else impl
    if hasattr(obj, "run"):
        return obj.run(combined)
    if hasattr(obj, "invoke"):
        return obj.invoke(combined)
    return str(obj)
def norm_result(x: Any) -> str:
    if isinstance(x, (dict, list)):
        return json.dumps(x, indent=2, ensure_ascii=False)
    return "" if x is None else str(x)
# --------- Page ----------
st.title("Deployment Demo (Faux Local Server + CLI Runs)")
st.markdown(
"""
This page demonstrates **production-like behavior** on a local machine:
1) You run a bot from **CLI-only** (files + args)  
2) A **local API server logs each run**  
3) This GUI renders results in a **terminal-style console** with **readable alternating bot colors**
"""
)
c1, c2 = st.columns([1, 1])
with c1:
    st.subheader("Start Here (copy/paste)")
    st.markdown("**Windows (PowerShell):**")
    st.code(
        r""".\scripts\windows\setup.ps1
.\scripts\windows\demo_server.ps1
.\scripts\windows\run.ps1 -Port 8502
.\scripts\windows\run_bot.ps1 -Bot <bot_id> -InputFile .\data\demo\sample_ticket.txt -File .\data\demo\policy.txt""",
        language="powershell",
    )
    st.markdown("**Ubuntu 24 (bash):**")
    st.code(
        """bash scripts/linux/setup.sh
bash scripts/linux/demo_server.sh
bash scripts/linux/run.sh
bash scripts/linux/run_bot.sh --bot <bot_id> --input-file data/demo/sample_ticket.txt --file data/demo/policy.txt""",
        language="bash",
    )
with c2:
    st.subheader("Server Status")
    api = st.text_input("Demo API URL", value=API_DEFAULT)
    up = api_up(api)
    st.write("API:", api)
    st.success("UP") if up else st.warning("DOWN (start it in a terminal): scripts/windows/demo_server.ps1")
# --------- Console State ----------
if "console" not in st.session_state:
    st.session_state.console = []
    st.session_state.console.append(cmd_line("Ready. Paste a command below or use the form runner."))
def push(html: str) -> None:
    st.session_state.console.append(html)
    st.session_state.console = st.session_state.console[-200:]  # cap
# --------- Runner UI ----------
st.divider()
left, right = st.columns([1, 1])
with left:
    st.subheader("Form Runner (easiest)")
    mode = st.radio("Run mode", ["API server (recommended)", "Local direct (no server)"], horizontal=True)
    bots = api_bots(api) if (mode.startswith("API") and up) else []
    if not bots:
        # fallback to local registry list
        try:
            from bots.registry import list_bots
            bots = list_bots()
        except Exception:
            bots = []
    bot = st.selectbox("Bot", options=bots if bots else ["(no bots found)"])
    user_text = st.text_area("Input text", value="Use the attached policy to answer the ticket.", height=120)
    up_files = st.file_uploader("Attach files", accept_multiple_files=True)
    files: List[Tuple[str, str]] = []
    if up_files:
        for f in up_files:
            try:
                files.append((f.name, f.read().decode("utf-8", errors="ignore")))
            except Exception:
                files.append((f.name, "(binary file)"))
    if st.button("Run (writes to console)", type="primary", disabled=(bot == "(no bots found)")):
        push(cmd_line(f"run_bot --bot {bot} --text \"{user_text[:40]}...\""))
        push(user_box(user_text))
        try:
            if mode.startswith("API"):
                if not up:
                    raise RuntimeError("API is DOWN. Start it: scripts/windows/demo_server.ps1")
                res = run_via_api(api, bot, user_text, files)
            else:
                res = run_local(bot, user_text, files)
            push(bot_box(bot, norm_result(res)))
        except Exception as e:
            push(err_line(str(e)))
with right:
    st.subheader("Interactive CLI Console (command input)")
    st.caption("Type a command like you would in a terminal. We run it and render USER/BOT in color.")
    default_cmd = "run_bot --bot <bot_id> --input-file data/demo/sample_ticket.txt --file data/demo/policy.txt"
    cmd = st.text_input("Command", value=default_cmd)
    if st.button("Run Command (writes to console)"):
        push(cmd_line(cmd))
        try:
            parts = shlex.split(cmd)
            if not parts:
                raise RuntimeError("Empty command")
            if parts[0] in ("run_bot", "run_bot.py", "scripts/demo/run_bot.py"):
                # parse minimal args
                b = None
                input_text = ""
                input_file = None
                file_list: List[str] = []
                i = 1
                while i < len(parts):
                    if parts[i] in ("--bot",):
                        b = parts[i+1]; i += 2; continue
                    if parts[i] in ("--text", "--input"):
                        input_text = parts[i+1]; i += 2; continue
                    if parts[i] in ("--input-file",):
                        input_file = parts[i+1]; i += 2; continue
                    if parts[i] in ("--file",):
                        file_list.append(parts[i+1]); i += 2; continue
                    i += 1
                if not b:
                    raise RuntimeError("Missing --bot <bot_id>")
                if input_file:
                    input_text = Path(input_file).read_text(encoding="utf-8", errors="ignore")
                file_blobs: List[Tuple[str, str]] = []
                for fp in file_list:
                    p = Path(fp)
                    file_blobs.append((p.name, p.read_text(encoding="utf-8", errors="ignore")))
                push(user_box(input_text or "(empty input)"))
                # choose API if it's up, otherwise local
                if up:
                    res = run_via_api(api, b, input_text, file_blobs)
                else:
                    res = run_local(b, input_text, file_blobs)
                push(bot_box(b, norm_result(res)))
            else:
                raise RuntimeError("Only run_bot-style commands are supported here.")
        except Exception as e:
            push(err_line(str(e)))
# --------- Render console ----------
st.divider()
st.subheader("Console Output")
st.markdown('<div class="term">' + "\n".join(st.session_state.console) + "</div>", unsafe_allow_html=True)
col_a, col_b = st.columns([1, 1])
with col_a:
    if st.button("Clear console"):
        st.session_state.console = [cmd_line("Console cleared.")]
with col_b:
    st.caption("Tip: Start the demo API in a terminal to show bot listing + server logging.")