"""
demo_host_bot
A lightweight helper bot used inside the AI Training Hub Deployment Demo page.

Purpose:
- Provide a "narrator" that suggests which bot to run next
- Provide quick demo scripts and step-by-step CLI usage

It intentionally does NOT require any external services.
If you want it to call Ollama, set DEMO_HOST_USE_OLLAMA=1.
"""

from __future__ import annotations
import os, json, textwrap
from typing import Any, Dict

def _ollama_generate(prompt: str, model: str | None = None, host: str | None = None) -> str:
    import requests
    host = (host or os.environ.get("OLLAMA_HOST","http://127.0.0.1:11434")).rstrip("/")
    model = model or os.environ.get("OLLAMA_MODEL","mistral:7b-instruct")
    r = requests.post(f"{host}/api/generate", json={"model": model, "prompt": prompt, "stream": False}, timeout=60)
    r.raise_for_status()
    return (r.json().get("response") or "").strip()

def run(message: str = "") -> Dict[str, Any]:
    msg = (message or "").strip()

    # If enabled, let it "talk" via local Ollama (still offline/local)
    if os.environ.get("DEMO_HOST_USE_OLLAMA","0") == "1" and msg:
        try:
            prompt = (
                "You are a concise demo host for an internal AI Training Hub.\n"
                "Goal: propose the best next bot to run and a short command to run it.\n"
                "Return plain text with:\n"
                "- Recommended bot\n"
                "- Suggested input\n"
                "- 2 bullet rationale\n\n"
                f"USER REQUEST:\n{msg}\n"
            )
            out = _ollama_generate(prompt)
            return {"notes": out}
        except Exception as e:
            return {"notes": f"(ollama disabled/failing) {e}"}

    # Default deterministic guidance
    scripts = [
        ("List bots", "/list"),
        ("Use it_ticket_bot", "/use it_ticket_bot"),
        ("Run a ticket triage", '/run "User requests VPN access; deadline Friday; confirm manager approval."'),
        ("Describe current bot", "/describe"),
        ("Show help", "/help"),
    ]
    body = "\n".join([f"- {t}: `{c}`" for t,c in scripts])

    notes = textwrap.dedent(f"""
    Demo Host ready.

    Quick scripts:
    {body}

    Tip: In the Deployment Demo page, use the **Live CLI** tab:
    - pick a bot from the dropdown
    - type a message
    - click **Run Bot**
    or use slash-commands in the command bar.
    """).strip()

    if msg:
        notes += "\n\nYou asked:\n" + msg + "\n\nSuggested next:\n- Try `/list` then `/use <bot>` then `/run \"...\"`"

    return {"notes": notes}
