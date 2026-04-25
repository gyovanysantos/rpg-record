# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Shadow of the Demon Lord desktop app.

Build with:
    cd desktop-app
    pyinstaller build.spec
"""

import sys
from pathlib import Path

block_cipher = None
BASE = Path(".")

a = Analysis(
    ["main.py"],
    pathex=[str(BASE)],
    binaries=[],
    datas=[
        (str(BASE / "assets"), "assets"),
        (str(BASE / "data"), "data"),
    ],
    hiddenimports=[
        "PySide6.QtWidgets",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtMultimedia",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SotDL-RPG-Recorder",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window — pure GUI
    icon=None,      # TODO: Add .ico file in Phase 8
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SotDL-RPG-Recorder",
)
