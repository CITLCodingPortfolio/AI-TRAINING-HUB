from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json
import shutil
def export_project(repo_root: Path, spec: Dict[str, Any]) -> Path:
    """
    Export a runnable student project that loads bot.json and chats via Ollama.
    The goal: students can open the exported folder in VS Code and run it.
    """
    exports_dir = repo_root / "projects" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    name = (spec.get("name") or "bot").strip().replace(" ", "-").lower()
    out = exports_dir / name
    # overwrite existing export
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    # Save spec into project
    (out / "bot.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    # Requirements based on framework / RAG
    fw = spec.get("agent", {}).get("framework", "none")
    reqs = ["requests"]
    if fw == "langgraph":
        reqs += ["langgraph"]
    elif fw == "crewai":
        reqs += ["crewai"]
    elif fw == "autogen":
        reqs += ["pyautogen"]
    if spec.get("rag", {}).get("enabled"):
        reqs += ["chromadb", "sentence-transformers", "pypdf"]
    (out / "requirements.txt").write_text("\n".join(reqs) + "\n", encoding="utf-8")
    runner = r'''
import json
import requests
spec = json.load(open("bot.json","r",encoding="utf-8"))
base_url = spec["runtime"]["base_url"]
model = spec["runtime"]["model"]
def chat(messages, options):
    payload = {"model": model, "messages": messages, "stream": False, "options": options}
    r = requests.post(f"{base_url}/api/chat", json=payload, timeout=180)
    r.raise_for_status()
    return r.json()["message"]["content"]
opts = {
  "temperature": spec["generation"]["temperature"],
  "top_p": spec["generation"]["top_p"],
  "num_ctx": spec["generation"]["num_ctx"],
  "num_predict": spec["generation"]["max_tokens"]
}
history = [{"role":"system","content": spec["system"]["prompt"]}]
print("Loaded bot:", spec["name"])
print("Type 'exit' to quit.")
while True:
    q = input("\nYou: ").strip()
    if q.lower() in ["exit","quit"]:
        break
    history.append({"role":"user","content": q})
    a = chat(history, opts)
    history.append({"role":"assistant","content": a})
    print("\nBot:", a)
'''
    (out / "run_chat.py").write_text(runner.strip() + "\n", encoding="utf-8")
    readme = f"""# {spec.get('name','Bot')}
Exported from AI-Training-Hub.
## Setup
python -m venv .venv
# Windows:
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
## Run
python run_chat.py
## Notes
Framework selected: {fw}
RAG enabled: {spec.get('rag',{}).get('enabled')}
"""
    (out / "README.md").write_text(readme, encoding="utf-8")
    return out
