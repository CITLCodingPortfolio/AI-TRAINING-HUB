# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for build_model.exe

from pathlib import Path
from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / "build_model_cmd.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(ROOT / "bots" / "Modelfile"), "bots")],
    hiddenimports=["subprocess", "pathlib", "argparse"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["streamlit", "pandas", "numpy", "torch", "rich"],
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
    name="build_model",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    # no uac_admin → no elevation required
)
