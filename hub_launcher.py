#!/usr/bin/env python3
"""
hub_launcher.py - Double-click launcher for the AI Training Hub GUI.

What it does:
  1. Finds the .venv Python (which has Streamlit + all deps installed)
  2. Starts the full Streamlit GUI (app/hub.py) - all tabs, all features
  3. Opens your browser automatically to http://localhost:8502
  4. This window shows server status; close it to stop the server.

Build to EXE with:  .\build_exe.ps1
"""
import os
import sys
import subprocess
import webbrowser
import time
import threading
import traceback
from pathlib import Path


def _pause(msg="\n  Press Enter to close..."):
    try:
        input(msg)
    except Exception:
        pass


def find_repo_root() -> Path:
    """Repo root = directory containing this EXE (or script)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def find_venv_python(repo_root: Path) -> Path:
    candidates = [
        repo_root / ".venv" / "Scripts" / "python.exe",   # Windows venv
        repo_root / ".venv" / "bin" / "python",            # Linux/Mac venv
        repo_root / "venv"  / "Scripts" / "python.exe",
        repo_root / "venv"  / "bin" / "python",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]  # return expected path so error message is helpful


def main():
    if sys.platform == "win32":
        os.system("chcp 65001 >nul 2>&1")

    repo_root  = find_repo_root()
    venv_py    = find_venv_python(repo_root)
    hub_script = repo_root / "app" / "hub.py"
    port       = int(os.environ.get("AI_TRAINING_HUB_PORT", "8502"))
    url        = f"http://localhost:{port}"

    print()
    print("  ======================================================")
    print("   AI Training Hub  -  Launching GUI")
    print("  ======================================================")
    print(f"  Repo    : {repo_root}")
    print(f"  Python  : {venv_py}")
    print(f"  Hub     : {hub_script}")
    print(f"  URL     : {url}")
    print()

    if not venv_py.exists():
        print("  ERROR: Virtual environment not found.")
        print(f"  Expected: {venv_py}")
        print()
        print("  Fix:  run  scripts\\windows\\setup.ps1  first to create the venv.")
        _pause()
        sys.exit(1)

    if not hub_script.exists():
        print("  ERROR: app/hub.py not found.")
        print(f"  Expected: {hub_script}")
        print("  Make sure this EXE is in the AI-Training-Hub repo root folder.")
        _pause()
        sys.exit(1)

    # -- Start Streamlit -------------------------------------------------------
    cmd = [
        str(venv_py), "-m", "streamlit", "run",
        str(hub_script),
        "--server.port",             str(port),
        "--server.headless",         "true",
        "--browser.gatherUsageStats","false",
        "--server.fileWatcherType",  "none",     # faster start, no hot-reload needed
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root)

    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NO_WINDOW   # hide the Streamlit console spam

    proc = subprocess.Popen(cmd, env=env, cwd=str(repo_root), creationflags=flags)
    print("  Server starting...")

    # -- Open browser after a short delay -------------------------------------
    def _open():
        time.sleep(3)
        webbrowser.open(url)
        print(f"  Browser opened: {url}")
        print()
        print("  -- The full GUI is now running in your browser --------------")
        print("  Tabs: Environment . Install . Ollama . Scaffold . Bot Builder")
        print("              Chat . Tests . Deployment Demo")
        print("  -------------------------------------------------------------")
        print()
        print("  Keep this window open to keep the server running.")
        print("  Press Ctrl+C here (or close this window) to stop.")
        print()

    threading.Thread(target=_open, daemon=True).start()

    # -- Wait for server to exit -----------------------------------------------
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n  Stopping server...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("  Server stopped.")

    _pause()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print()
        print("  == UNEXPECTED ERROR ======================================")
        traceback.print_exc()
        _pause()
        sys.exit(1)
