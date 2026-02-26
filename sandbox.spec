# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for sandbox.exe
# Build with:  pyinstaller sandbox.spec

from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

ROOT = Path(SPECPATH)

# ── Collect entire packages (catches dynamic sub-imports) ─────────────────────
rich_datas,     rich_bins,     rich_hidden     = collect_all('rich')
requests_datas, requests_bins, requests_hidden = collect_all('requests')
urllib3_datas,  urllib3_bins,  urllib3_hidden  = collect_all('urllib3')
certifi_datas,  certifi_bins,  certifi_hidden  = collect_all('certifi')
bots_hidden = collect_submodules('bots')

all_datas = (
    rich_datas + requests_datas + urllib3_datas + certifi_datas
    + [(str(ROOT / "bots" / "Modelfile"), "bots")]
)
all_bins     = rich_bins + requests_bins + urllib3_bins + certifi_bins
all_hidden   = (
    rich_hidden + requests_hidden + urllib3_hidden + certifi_hidden
    + bots_hidden
    + [
        "bots",
        "bots.registry",
        "bots.ollama_bot",
        "bots.ollama_sandbox",
    ]
)

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [str(ROOT / "sandbox.py")],
    pathex=[str(ROOT)],
    binaries=all_bins,
    datas=all_datas,
    hiddenimports=all_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "streamlit", "pandas", "numpy", "matplotlib",
        "torch", "PIL", "cv2", "sklearn", "scipy", "altair",
        "tkinter", "PyQt5", "PyQt6", "wx",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="sandbox",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX can trigger AV false positives
    console=True,       # keep console — this is a CLI REPL
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # uac_admin NOT set → asInvoker manifest → no elevation prompt ever
)
