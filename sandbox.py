#!/usr/bin/env python3
"""
sandbox.py — Entry point for sandbox.exe and `python sandbox.py`

Run from the repo root:
    python sandbox.py
    python sandbox.py --bot student_bot
    python sandbox.py --bot ollama_bot --color "#FF6B6B"
    python sandbox.py --model llama3.2
    python sandbox.py --no-stream

Or as a compiled EXE (built with build_exe.ps1):
    sandbox.exe
    sandbox.exe --bot student_bot
"""
import sys
import os
import traceback


def _pause(msg: str = "  Press Enter to close..."):
    """Keep the window open so the user can read any error message."""
    try:
        input(msg)
    except Exception:
        pass


# Set Windows console to UTF-8 so rich box-drawing / arrows render correctly.
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    # Also tell Python's stdout to use utf-8 regardless of PYTHONIOENCODING
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# When running as a plain script add repo root to path.
# When frozen by PyInstaller, bots is bundled — no manipulation needed.
if not getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Import with visible error ─────────────────────────────────────────────────
try:
    from bots.ollama_sandbox import main
except Exception as exc:
    print()
    print("  ══ STARTUP ERROR ══════════════════════════════════════════")
    print(f"  {exc}")
    print()
    traceback.print_exc()
    print()
    print("  Possible causes:")
    print("  • Run build_exe.ps1 again to rebuild (a dep may be missing)")
    print("  • Or run:  python sandbox.py  directly to see full traceback")
    print()
    _pause()
    sys.exit(1)

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print()
        print("  ══ RUNTIME ERROR ══════════════════════════════════════════")
        print(f"  {exc}")
        print()
        traceback.print_exc()
        print()
        _pause()
        sys.exit(1)
