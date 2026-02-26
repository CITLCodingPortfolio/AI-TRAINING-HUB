# -*- coding: utf-8 -*-
"""
ollama_sandbox.py — IRC-style colored CLI chat sandbox for Ollama bots.

Each bot defined in the registry (or via --color) gets its own unique color
scheme for responses, headers, and borders — like IRC channels per user.

Usage:
    python -m bots.ollama_sandbox                        # hub-assistant defaults
    python -m bots.ollama_sandbox --bot ollama_bot       # load bot from registry
    python -m bots.ollama_sandbox --bot student_bot      # student's custom bot color
    python -m bots.ollama_sandbox --model llama3.2       # override model
    python -m bots.ollama_sandbox --color "#FF6B6B"      # force a specific color
    python -m bots.ollama_sandbox --no-stream            # disable streaming

Commands inside the sandbox:
    /help            Show all commands
    /quit  /exit     Exit
    /clear           Clear conversation history
    /reset           Reset history + model + system prompt
    /model <name>    Switch Ollama model mid-session
    /system <text>   Replace system prompt
    /history         Print conversation history
    /models          List available Ollama models
    /color <hex>     Change bot response color live
    /bot <id>        Switch to a different registered bot
    /info            Show current session info
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests

# rich imports — available via requirements/hub.txt
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich.markup import escape
from rich.style import Style

# ── Console (stderr=False so piped output is clean) ──────────────────────────
console = Console(highlight=False)

# ── Defaults ─────────────────────────────────────────────────────────────────
DEFAULT_HOST   = (
    os.environ.get("OLLAMA_HOST")
    or os.environ.get("CITL_OLLAMA_HOST")
    or "http://localhost:11434"
)
DEFAULT_MODEL  = os.environ.get("OLLAMA_MODEL", "hub-assistant")
DEFAULT_COLOR  = "#22D3EE"   # bright cyan
USER_COLOR     = "yellow"
SYS_COLOR      = "dim white"
ERROR_COLOR    = "bright_red"
CMD_COLOR      = "bright_magenta"
BORDER_DIM     = "grey46"

DEFAULT_SYSTEM = (
    "You are the AI Training Hub Assistant — a concise, expert AI tutor. "
    "Help with local LLM deployment (Ollama), agent frameworks (LangGraph, "
    "CrewAI, AutoGen), IT ticket triage, DevOps/SLURM workflows, and Python "
    "bot development. Be concise. Use bullet points for steps, code blocks "
    "for code. Never hallucinate commands or file paths."
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def hex_to_rich(hex_color: str) -> str:
    """Return a rich-compatible color string from a hex value."""
    h = hex_color.strip().lstrip("#")
    if len(h) == 6:
        return f"#{h.upper()}"
    return hex_color  # pass through if already rich format


def ollama_models(host: str) -> List[str]:
    try:
        r = requests.get(f"{host.rstrip('/')}/api/tags", timeout=3)
        r.raise_for_status()
        return sorted(m["name"] for m in (r.json().get("models") or []) if m.get("name"))
    except Exception:
        return []


def stream_chat(
    host: str,
    model: str,
    messages: List[Dict[str, str]],
    options: Dict[str, Any],
    bot_color: str,
    bot_name: str,
) -> str:
    """Stream tokens from Ollama, printing each with bot_color. Returns full text."""
    console.print(f"[{bot_color}]  {bot_name} ▸[/{bot_color}] ", end="")
    full = ""
    try:
        payload = {"model": model, "messages": messages, "stream": True, "options": options}
        with requests.post(
            f"{host.rstrip('/')}/api/chat",
            json=payload,
            stream=True,
            timeout=300,
        ) as resp:
            resp.raise_for_status()
            for raw in resp.iter_lines():
                if not raw:
                    continue
                chunk = json.loads(raw)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    # Write raw so ANSI codes in model output pass through
                    sys.stdout.write(
                        f"\033[0m"  # reset
                        + f"\033[38;2;"
                        + _hex_to_ansi(bot_color)
                        + "m"
                        + token
                        + "\033[0m"
                    )
                    sys.stdout.flush()
                    full += token
                if chunk.get("done"):
                    break
    except KeyboardInterrupt:
        pass  # user pressed Ctrl+C mid-stream — partial is fine
    except Exception as exc:
        console.print(f"\n[{ERROR_COLOR}]Stream error: {escape(str(exc))}[/{ERROR_COLOR}]")
    console.print()  # newline after streamed content
    return full


def fetch_chat(
    host: str,
    model: str,
    messages: List[Dict[str, str]],
    options: Dict[str, Any],
) -> str:
    """Non-streaming fallback."""
    payload = {"model": model, "messages": messages, "stream": False, "options": options}
    r = requests.post(f"{host.rstrip('/')}/api/chat", json=payload, timeout=300)
    r.raise_for_status()
    return r.json()["message"]["content"]


def _hex_to_ansi(hex_color: str) -> str:
    """Convert '#RRGGBB' or 'RRGGBB' to '255;128;0' for ANSI escape."""
    h = hex_color.strip().lstrip("#")
    if len(h) != 6:
        return "34;212;238"  # fallback cyan
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return f"{r};{g};{b}"


# ── Ollama process management ────────────────────────────────────────────────

def _ping_ollama(host: str, timeout: float = 2.0) -> bool:
    """Return True if Ollama responds normally (not hung, not down)."""
    try:
        r = requests.get(f"{host.rstrip('/')}/api/tags", timeout=timeout)
        return r.status_code == 200
    except requests.exceptions.ConnectTimeout:
        return False   # hung — treats as down so caller can kill+restart
    except Exception:
        return False


def _ollama_is_hung(host: str) -> bool:
    """Return True if Ollama is listening but not responding (connection timeout)."""
    try:
        requests.get(f"{host.rstrip('/')}/api/tags", timeout=2.0)
        return False
    except requests.exceptions.ConnectTimeout:
        return True    # port open, no response = hung
    except Exception:
        return False   # refused = simply not running


def _kill_ollama() -> None:
    """Force-kill all Ollama processes so a clean restart can follow."""
    if sys.platform == "win32":
        for name in ("ollama.exe", "ollama_llama_server.exe"):
            subprocess.run(["taskkill", "/F", "/IM", name], capture_output=True)
    if sys.platform != "win32":
        subprocess.run(["pkill", "-9", "-f", "ollama serve"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "ollama_llama"],  capture_output=True)
    time.sleep(1)   # allow OS to release the port


def _start_ollama_process(host: str) -> bool:
    """Spawn 'ollama serve' silently; wait up to 15 s for it to respond."""
    try:
        kwargs: Dict[str, Any] = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
        subprocess.Popen(["ollama", "serve"], **kwargs)
    except FileNotFoundError:
        return False
    except Exception:
        return False

    console.print(f"  [{SYS_COLOR}]  Waiting", end="")
    for _ in range(15):
        time.sleep(1)
        console.print(".", end="")
        sys.stdout.flush()
        if _ping_ollama(host, timeout=1.5):
            console.print(f"  ready[/{SYS_COLOR}]")
            return True
    console.print(f"  timed out[/{SYS_COLOR}]")
    return False


def _ensure_ollama(sess: "Session") -> bool:
    """
    Guarantee Ollama is reachable. Handles three cases automatically:
      1. Already up           → nothing to do
      2. Hung (timeout)       → kill + restart silently
      3. Not running (refused)→ start silently
    Returns True if Ollama is reachable after all attempts.
    """
    if _ping_ollama(sess.host):
        console.print(f"  [{sess.bot_color}] OK [/{sess.bot_color}]  Ollama ready  ({sess.host})")
        return True

    if _ollama_is_hung(sess.host):
        console.print(f"  [{SYS_COLOR}] .. [/{SYS_COLOR}]  Ollama hung — killing and restarting ...")
        _kill_ollama()
    else:
        console.print(f"  [{SYS_COLOR}] .. [/{SYS_COLOR}]  Ollama not running — starting ...")

    if _start_ollama_process(sess.host):
        console.print(f"  [{sess.bot_color}] OK [/{sess.bot_color}]  Ollama started.")
        return True

    console.print(f"  [{ERROR_COLOR}] !! [/{ERROR_COLOR}]  Could not start Ollama automatically.")
    console.print(f"  [{SYS_COLOR}]      Install Ollama from  https://ollama.com[/{SYS_COLOR}]")
    console.print(f"  [{SYS_COLOR}]      Then type  /check  to retry.[/{SYS_COLOR}]")
    return False


def _model_exists(host: str, model: str) -> bool:
    """Return True if model (or prefix match) is in Ollama's local list."""
    try:
        r = requests.get(f"{host.rstrip('/')}/api/tags", timeout=3)
        r.raise_for_status()
        names = [m.get("name", "") for m in (r.json().get("models") or [])]
        base = model.split(":")[0]
        return any(n == model or n.startswith(base + ":") or n.split(":")[0] == base for n in names)
    except Exception:
        return False


def _find_modelfile() -> Optional[Path]:
    """Locate bots/Modelfile relative to this script or frozen EXE."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent
    for candidate in [base / "Modelfile", base.parent / "bots" / "Modelfile"]:
        if candidate.exists():
            return candidate
    return None


def _ensure_model(sess: "Session") -> None:
    """
    Guarantee the requested model is available. Auto-fixes without prompts:
      • hub-assistant + Modelfile found → build automatically
      • any other missing model         → switch to first available
      • no models at all                → print actionable hint
    """
    if _model_exists(sess.host, sess.model):
        console.print(f"  [{sess.bot_color}] OK [/{sess.bot_color}]  Model '{sess.model}' ready.")
        return

    console.print(f"  [{SYS_COLOR}] .. [/{SYS_COLOR}]  Model '{sess.model}' not found — fixing ...")
    mf = _find_modelfile()

    if sess.model == "hub-assistant" and mf:
        console.print(f"  [{SYS_COLOR}]      Building from {mf.name} (this takes a moment) ...[/{SYS_COLOR}]")
        try:
            result = subprocess.run(
                ["ollama", "create", sess.model, "-f", str(mf)],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                console.print(f"  [{sess.bot_color}] OK [/{sess.bot_color}]  Model '{sess.model}' built.")
                return
        except Exception:
            pass
        console.print(f"  [{ERROR_COLOR}] !! [/{ERROR_COLOR}]  Build failed — trying fallback model ...")

    # Fallback: use whatever is already available
    available = ollama_models(sess.host)
    if available:
        sess.model = available[0]
        console.print(f"  [{sess.bot_color}] >> [/{sess.bot_color}]  Using available model: {sess.model}")
    else:
        console.print(
            f"  [{ERROR_COLOR}] !! [/{ERROR_COLOR}]  No models found.\n"
            f"  [{SYS_COLOR}]      Pull one:  ollama pull llama3.2  then /check[/{SYS_COLOR}]"
        )


# ── Public diagnostics entry (also called by /check and /host) ───────────────

def run_startup_diagnostics(sess: "Session") -> None:
    """
    Fully automatic Ollama + model check. No user prompts. No raw errors.
    Called at launch and on /check or /host.
    """
    console.print(Rule(style=sess.bot_color))
    console.print(f"  [{SYS_COLOR}]Checking Ollama ...[/{SYS_COLOR}]")

    ollama_ok = _ensure_ollama(sess)
    if ollama_ok:
        _ensure_model(sess)

    console.print(Rule(style=sess.bot_color))


# ── Session state ─────────────────────────────────────────────────────────────

class Session:
    def __init__(
        self,
        host: str,
        model: str,
        bot_name: str,
        bot_color: str,
        system_prompt: str,
        stream: bool = True,
    ):
        self.host          = host
        self.model         = model
        self.bot_name      = bot_name
        self.bot_color     = hex_to_rich(bot_color)
        self.system_prompt = system_prompt
        self.stream        = stream
        self.history: List[Dict[str, str]] = []

    @property
    def options(self) -> Dict[str, Any]:
        return {"temperature": 0.3, "top_p": 0.9, "num_ctx": 8192, "num_predict": 1024}

    def messages(self, user_text: str) -> List[Dict[str, str]]:
        msgs = [{"role": "system", "content": self.system_prompt}]
        msgs += self.history
        msgs.append({"role": "user", "content": user_text})
        return msgs

    def ask(self, user_text: str) -> str:
        msgs = self.messages(user_text)
        if self.stream:
            reply = stream_chat(
                self.host, self.model, msgs,
                self.options, self.bot_color, self.bot_name,
            )
        else:
            with console.status(f"[{SYS_COLOR}]{self.bot_name} is thinking…[/{SYS_COLOR}]"):
                reply = fetch_chat(self.host, self.model, msgs, self.options)
            console.print(
                Panel(
                    Text(reply, style=Style(color=self.bot_color)),
                    title=f"[bold {self.bot_color}]{self.bot_name}[/bold {self.bot_color}]",
                    border_style=BORDER_DIM,
                    padding=(0, 1),
                )
            )
        # commit to history
        self.history.append({"role": "user",      "content": user_text})
        self.history.append({"role": "assistant",  "content": reply})
        return reply

    def clear(self):
        self.history.clear()


# ── Print helpers ─────────────────────────────────────────────────────────────

def print_header(sess: Session):
    console.print()
    title = Text()
    title.append("  AI Training Hub", style="bold white")
    title.append("  —  Ollama Bot Sandbox", style=SYS_COLOR)
    subtitle = (
        f"[{sess.bot_color}]Bot: {sess.bot_name}[/{sess.bot_color}]  "
        f"[{SYS_COLOR}]Model: {sess.model}  •  Host: {sess.host}[/{SYS_COLOR}]"
    )
    console.print(
        Panel(
            f"{title}\n{subtitle}",
            border_style=sess.bot_color,
            padding=(0, 2),
        )
    )
    console.print(
        f"[{SYS_COLOR}]  /help for commands  •  /quit to exit  •  Ctrl+C interrupts stream[/{SYS_COLOR}]\n"
    )


def print_help(bot_color: str):
    cmds = [
        ("/help",          "Show this help"),
        ("/quit  /exit",   "Exit sandbox"),
        ("/check",         "Re-run Ollama + model diagnostics and auto-fix"),
        ("/clear",         "Clear conversation history"),
        ("/reset",         "Reset history + model + system prompt"),
        ("/history",       "Print conversation history"),
        ("/info",          "Show current session info"),
        ("/model <name>",  "Switch Ollama model"),
        ("/models",        "List available Ollama models"),
        ("/host <url>",    "Switch Ollama host and re-run diagnostics"),
        ("/system <text>", "Replace system prompt for this session"),
        ("/color <hex>",   "Change bot response color (#RRGGBB)"),
        ("/bot <id>",      "Switch to another registered bot"),
    ]
    lines = [
        f"  [{CMD_COLOR}]{cmd:<22}[/{CMD_COLOR}] [{SYS_COLOR}]{desc}[/{SYS_COLOR}]"
        for cmd, desc in cmds
    ]
    console.print(
        Panel(
            "\n".join(lines),
            title=f"[bold {bot_color}]Commands[/bold {bot_color}]",
            border_style=bot_color,
            padding=(0, 1),
        )
    )


def print_info(sess: Session):
    lines = [
        f"  [{SYS_COLOR}]Host:[/{SYS_COLOR}]    [{sess.bot_color}]{sess.host}[/{sess.bot_color}]",
        f"  [{SYS_COLOR}]Model:[/{SYS_COLOR}]   [{sess.bot_color}]{sess.model}[/{sess.bot_color}]",
        f"  [{SYS_COLOR}]Bot:[/{SYS_COLOR}]     [{sess.bot_color}]{sess.bot_name}[/{sess.bot_color}]",
        f"  [{SYS_COLOR}]Color:[/{SYS_COLOR}]   [{sess.bot_color}]{sess.bot_color}[/{sess.bot_color}]",
        f"  [{SYS_COLOR}]Stream:[/{SYS_COLOR}]  [{sess.bot_color}]{sess.stream}[/{sess.bot_color}]",
        f"  [{SYS_COLOR}]History:[/{SYS_COLOR}] [{sess.bot_color}]{len(sess.history) // 2} turns[/{sess.bot_color}]",
        f"  [{SYS_COLOR}]System:[/{SYS_COLOR}]  {escape(sess.system_prompt[:80])}…",
    ]
    console.print(
        Panel(
            "\n".join(lines),
            title=f"[bold {sess.bot_color}]Session Info[/bold {sess.bot_color}]",
            border_style=BORDER_DIM,
            padding=(0, 1),
        )
    )


def print_history(sess: Session):
    if not sess.history:
        console.print(f"[{SYS_COLOR}]  (no history yet)[/{SYS_COLOR}]")
        return
    for msg in sess.history:
        if msg["role"] == "user":
            console.print(f"[{USER_COLOR}]  You    ▸[/{USER_COLOR}] {escape(msg['content'])}")
        else:
            console.print(f"[{sess.bot_color}]  {sess.bot_name:<6} ▸[/{sess.bot_color}] {escape(msg['content'][:120])}…")


# ── Command dispatcher ────────────────────────────────────────────────────────

def handle_command(line: str, sess: Session, default_system: str) -> bool:
    """
    Handle /command lines. Returns True to continue loop, False to exit.
    """
    parts = line.strip().split(None, 1)
    cmd   = parts[0].lower()
    arg   = parts[1].strip() if len(parts) > 1 else ""

    if cmd in ("/quit", "/exit"):
        console.print(f"\n[{sess.bot_color}]  Goodbye! ✓[/{sess.bot_color}]\n")
        return False

    elif cmd == "/help":
        print_help(sess.bot_color)

    elif cmd == "/clear":
        sess.clear()
        console.print(f"[{SYS_COLOR}]  History cleared.[/{SYS_COLOR}]")

    elif cmd == "/reset":
        sess.clear()
        sess.system_prompt = default_system
        console.print(f"[{SYS_COLOR}]  Session reset.[/{SYS_COLOR}]")

    elif cmd == "/history":
        print_history(sess)

    elif cmd == "/info":
        print_info(sess)

    elif cmd == "/model":
        if not arg:
            console.print(f"[{ERROR_COLOR}]  Usage: /model <model-name>[/{ERROR_COLOR}]")
        else:
            sess.model = arg
            console.print(f"[{SYS_COLOR}]  Model → [{sess.bot_color}]{arg}[/{sess.bot_color}][/{SYS_COLOR}]")

    elif cmd == "/models":
        names = ollama_models(sess.host)
        if names:
            console.print(
                Panel(
                    "\n".join(f"  [{sess.bot_color}]•[/{sess.bot_color}] {n}" for n in names),
                    title="Available Models",
                    border_style=BORDER_DIM,
                )
            )
        else:
            console.print(f"[{ERROR_COLOR}]  Could not reach Ollama at {sess.host}[/{ERROR_COLOR}]")

    elif cmd == "/system":
        if not arg:
            console.print(f"[{ERROR_COLOR}]  Usage: /system <new system prompt>[/{ERROR_COLOR}]")
        else:
            sess.system_prompt = arg
            console.print(f"[{SYS_COLOR}]  System prompt updated.[/{SYS_COLOR}]")

    elif cmd == "/color":
        if not arg.startswith("#") or len(arg) not in (4, 7):
            console.print(f"[{ERROR_COLOR}]  Usage: /color #RRGGBB[/{ERROR_COLOR}]")
        else:
            sess.bot_color = hex_to_rich(arg)
            console.print(f"  Color → [{sess.bot_color}]{sess.bot_color}[/{sess.bot_color}]")

    elif cmd == "/bot":
        if not arg:
            console.print(f"[{ERROR_COLOR}]  Usage: /bot <bot_id>[/{ERROR_COLOR}]")
        else:
            _switch_bot(arg, sess)

    elif cmd == "/check":
        run_startup_diagnostics(sess)

    elif cmd == "/host":
        if not arg:
            console.print(f"[{ERROR_COLOR}]  Usage: /host http://<ip>:11434[/{ERROR_COLOR}]")
        else:
            sess.host = arg.rstrip("/")
            console.print(f"  [{SYS_COLOR}]Host -> [{sess.bot_color}]{sess.host}[/{sess.bot_color}][/{SYS_COLOR}]")
            run_startup_diagnostics(sess)

    else:
        console.print(f"[{ERROR_COLOR}]  Unknown command: {escape(cmd)}  (try /help)[/{ERROR_COLOR}]")

    return True  # keep looping


def _switch_bot(bot_id: str, sess: Session):
    """Try to load bot identity from registry; update sess in-place."""
    try:
        # Late import so sandbox works even without full registry loaded
        from bots.registry import get_registry
        reg = get_registry()
        if bot_id not in reg:
            console.print(
                f"[{ERROR_COLOR}]  Unknown bot '{bot_id}'. Known: "
                f"{', '.join(sorted(reg.keys()))}[/{ERROR_COLOR}]"
            )
            return
        meta = reg[bot_id]
        sess.bot_name  = meta.name
        sess.bot_color = hex_to_rich(meta.color)
        sess.clear()
        console.print(
            f"[{sess.bot_color}]  Switched to {meta.name}  ({bot_id})[/{sess.bot_color}]"
        )
    except Exception as exc:
        console.print(f"[{ERROR_COLOR}]  Could not switch bot: {escape(str(exc))}[/{ERROR_COLOR}]")


# ── Main REPL ─────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Ollama Bot CLI Sandbox — IRC-style colored chat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--bot",      default="",         help="Bot ID from registry (sets name + color)")
    ap.add_argument("--model",    default="",         help="Ollama model tag (default: hub-assistant)")
    ap.add_argument("--host",     default="",         help="Ollama host URL")
    ap.add_argument("--color",    default="",         help="Bot response color (#RRGGBB)")
    ap.add_argument("--system",   default="",         help="Override system prompt")
    ap.add_argument("--no-stream", action="store_true", help="Disable token streaming")
    args = ap.parse_args()

    host          = args.host   or DEFAULT_HOST
    model         = args.model  or DEFAULT_MODEL
    bot_name      = "Hub Assistant"
    bot_color     = args.color  or DEFAULT_COLOR
    system_prompt = args.system or DEFAULT_SYSTEM

    # Load from registry if --bot given
    if args.bot:
        try:
            from bots.registry import get_registry
            reg = get_registry()
            if args.bot in reg:
                meta      = reg[args.bot]
                bot_name  = meta.name
                bot_color = args.color or meta.color   # --color can still override
            else:
                console.print(
                    f"[{ERROR_COLOR}]Bot '{args.bot}' not in registry — using defaults.[/{ERROR_COLOR}]"
                )
        except Exception as exc:
            console.print(f"[{ERROR_COLOR}]Registry error: {escape(str(exc))}[/{ERROR_COLOR}]")

    # Try to also load BOT_SYSTEM from the bot module if it defines one
    if args.bot and not args.system:
        try:
            import importlib
            mod = importlib.import_module(f"bots.{args.bot}")
            if hasattr(mod, "BOT_SYSTEM"):
                system_prompt = mod.BOT_SYSTEM
            if hasattr(mod, "MODEL") and not args.model:
                model = mod.MODEL
        except Exception:
            pass

    sess = Session(
        host=host,
        model=model,
        bot_name=bot_name,
        bot_color=bot_color,
        system_prompt=system_prompt,
        stream=not args.no_stream,
    )

    print_header(sess)

    # ── Startup diagnostics ───────────────────────────────────────────────────
    run_startup_diagnostics(sess)

    # ── REPL loop ────────────────────────────────────────────────────────────
    consecutive_errors = 0
    while True:
        try:
            console.print(f"[{USER_COLOR}]  You »[/{USER_COLOR}] ", end="")
            line = input()
        except (EOFError, KeyboardInterrupt):
            console.print(f"\n[{sess.bot_color}]  Goodbye![/{sess.bot_color}]\n")
            break

        line = line.strip()
        if not line:
            continue

        if line.startswith("/"):
            if not handle_command(line, sess, default_system=system_prompt):
                break
            consecutive_errors = 0
            continue

        # ── Send to Ollama ────────────────────────────────────────────────────
        console.print(Rule(style=BORDER_DIM))
        try:
            sess.ask(line)
            consecutive_errors = 0
        except requests.exceptions.ConnectionError:
            consecutive_errors += 1
            console.print(
                f"[{ERROR_COLOR}]  Ollama not reachable at {sess.host}[/{ERROR_COLOR}]"
            )
            if consecutive_errors >= 2:
                console.print(
                    f"  [{SYS_COLOR}]  Type [{sess.bot_color}]/check[/{sess.bot_color}]"
                    f" to auto-diagnose and fix, or [{sess.bot_color}]/host <url>[/{sess.bot_color}]"
                    f" to switch host.[/{SYS_COLOR}]"
                )
        except requests.exceptions.HTTPError as exc:
            consecutive_errors += 1
            console.print(f"[{ERROR_COLOR}]  Ollama HTTP error: {escape(str(exc))}[/{ERROR_COLOR}]")
            if "404" in str(exc):
                console.print(
                    f"  [{SYS_COLOR}]  Model '{sess.model}' not found. "
                    f"Try [{sess.bot_color}]/check[/{sess.bot_color}] to rebuild/switch.[/{SYS_COLOR}]"
                )
        except Exception as exc:
            consecutive_errors += 1
            console.print(f"[{ERROR_COLOR}]  Error: {escape(str(exc))}[/{ERROR_COLOR}]")
        console.print(Rule(style=BORDER_DIM))


if __name__ == "__main__":
    main()
