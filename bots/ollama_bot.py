# -*- coding: utf-8 -*-
"""
Ollama Bot — hub-assistant (Modelfile-defined)

Build the model first:
    ollama create hub-assistant -f bots/Modelfile

Run via sandbox (recommended — IRC-style colored chat):
    python -m bots.ollama_sandbox
    python -m bots.ollama_sandbox --bot ollama_bot
    python -m bots.ollama_sandbox --bot student_bot --color "#22C55E"

Run via hub CLI (JSON output):
    python -m bots.run_bot --bot ollama_bot --text "How do I deploy with Docker?"

Environment overrides:
    OLLAMA_HOST   — base URL  (default: http://localhost:11434)
    OLLAMA_MODEL  — model tag (default: hub-assistant)
"""
from __future__ import annotations
import os
from typing import Dict, Any, List
import requests

MODEL    = os.environ.get("OLLAMA_MODEL", "hub-assistant")
BASE_URL = (
    os.environ.get("OLLAMA_HOST")
    or os.environ.get("CITL_OLLAMA_HOST")
    or "http://localhost:11434"
)

# Sandbox identity — read by ollama_sandbox.py if this module is selected
BOT_ID     = "ollama_bot"
BOT_NAME   = "Hub Assistant"
BOT_COLOR  = "#22D3EE"   # bright cyan — override per-bot in registry or --color arg
BOT_SYSTEM = (
    "You are the AI Training Hub Assistant — a concise, expert AI tutor. "
    "Help with local LLM deployment (Ollama), agent frameworks (LangGraph, CrewAI, AutoGen), "
    "IT ticket triage, DevOps/SLURM workflows, and Python bot development. "
    "Be concise. Use bullet points for steps, code blocks for code. "
    "Never hallucinate commands or file paths."
)

# ── internal ─────────────────────────────────────────────────────────────────
def _options() -> Dict[str, Any]:
    return {"temperature": 0.3, "top_p": 0.9, "num_ctx": 8192, "num_predict": 1024}


def _chat(
    messages: List[Dict[str, str]],
    model: str = MODEL,
    base_url: str = BASE_URL,
) -> str:
    payload = {
        "model":    model,
        "messages": messages,
        "stream":   False,
        "options":  _options(),
    }
    r = requests.post(f"{base_url.rstrip('/')}/api/chat", json=payload, timeout=180)
    r.raise_for_status()
    return r.json()["message"]["content"]


# ── public run() ──────────────────────────────────────────────────────────────
def run(text: str, files=None, params=None) -> Dict[str, Any]:
    """
    Hub-compatible entry point (used by run_bot.py + bot_runtime.py).

    params keys (optional):
        model    — override model tag
        base_url — override Ollama host
        history  — list of prior {role, content} messages
    """
    params   = params or {}
    model    = params.get("model", MODEL)
    base_url = params.get("base_url", BASE_URL)
    history  = params.get("history", [])

    messages = [{"role": "system", "content": BOT_SYSTEM}]
    messages += [m for m in history if m.get("role") != "system"]
    messages.append({"role": "user", "content": text or "Hello!"})

    try:
        reply = _chat(messages, model=model, base_url=base_url)
        return {"bot": BOT_ID, "ok": True, "model": model, "reply": reply}
    except Exception as exc:
        return {"bot": BOT_ID, "ok": False, "model": model, "error": str(exc)}
