# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for hub_launcher.exe
# Intentionally SMALL — it only needs subprocess + webbrowser.
# Streamlit itself runs from the .venv, not bundled here.

from pathlib import Path
ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / "hub_launcher.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=["webbrowser", "threading", "subprocess"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "streamlit", "rich", "pandas", "numpy", "torch",
        "matplotlib", "PIL", "tkinter",
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
    name="Launch AI Training Hub",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,       # show status console so user can see server output / errors
    # NO uac_admin — runs as current user, no elevation needed
)
