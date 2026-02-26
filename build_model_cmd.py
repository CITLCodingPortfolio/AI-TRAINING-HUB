#!/usr/bin/env python3
"""
build_model_cmd.py — Build the hub-assistant Ollama model from bots/Modelfile.
Compiled to build_model.exe via build_exe.ps1.

Usage:
    build_model.exe
    build_model.exe --name my-custom-bot
    build_model.exe --modelfile path/to/Modelfile
"""
import argparse
import os
import subprocess
import sys
import traceback
from pathlib import Path


def _pause():
    """Always keep the window open so the user can read the output."""
    try:
        input("\n  Press Enter to close...")
    except Exception:
        pass


def find_modelfile() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent
    for candidate in [base / "bots" / "Modelfile", base / "Modelfile"]:
        if candidate.exists():
            return candidate
    return base / "bots" / "Modelfile"


def main():
    # UTF-8 so output renders correctly on Windows
    if sys.platform == "win32":
        os.system("chcp 65001 >nul 2>&1")

    ap = argparse.ArgumentParser(description="Build an Ollama model from bots/Modelfile")
    ap.add_argument("--name",      default="hub-assistant", help="Model name (default: hub-assistant)")
    ap.add_argument("--modelfile", default="",              help="Path to Modelfile (auto-detected if omitted)")
    args = ap.parse_args()

    mf = Path(args.modelfile) if args.modelfile else find_modelfile()

    print()
    print("  ══════════════════════════════════════════════════")
    print("   AI Training Hub — Build Ollama Model")
    print("  ══════════════════════════════════════════════════")
    print(f"  Model name : {args.name}")
    print(f"  Modelfile  : {mf}")
    print()

    if not mf.exists():
        print(f"  ERROR: Modelfile not found at: {mf}")
        print("  Place build_model.exe next to bots/Modelfile, or use --modelfile <path>")
        _pause()
        sys.exit(1)

    # Check ollama is reachable
    which = subprocess.run(
        ["ollama", "--version"], capture_output=True, text=True
    )
    if which.returncode != 0:
        print("  ERROR: 'ollama' command not found.")
        print("  Install Ollama from https://ollama.com and make sure it is in PATH.")
        _pause()
        sys.exit(1)

    print(f"  Running: ollama create {args.name} -f {mf}")
    print()

    result = subprocess.run(["ollama", "create", args.name, "-f", str(mf)])

    print()
    if result.returncode == 0:
        print("  ✓ Done! Model built successfully.")
        print()
        print("  Launch the sandbox:")
        print(f"    sandbox.exe --bot ollama_bot")
        print(f"    python sandbox.py --bot ollama_bot")
    else:
        print("  ERROR: ollama exited with an error (see output above).")
        print("  Make sure Ollama is running before building a model.")

    _pause()
    sys.exit(result.returncode)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print()
        print("  ══ UNEXPECTED ERROR ══════════════════════════")
        traceback.print_exc()
        _pause()
        sys.exit(1)
