# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Shadow of the Demon Lord desktop app.

Build with:
    cd desktop-app
    pyinstaller build.spec
"""

import sys
from pathlib import Path

# Read version from source
_version_file = Path("app/__version__.py")
_version = "0.0.0"
for _line in _version_file.read_text().splitlines():
    if _line.startswith("__version__"):
        _version = _line.split('"')[1]
        break

block_cipher = None
# MUST use .resolve() so PyInstaller gets absolute paths —
# relative "." / ".." silently fail to locate root-level modules.
BASE = Path(".").resolve()
REPO_ROOT = BASE.parent

a = Analysis(
    ["main.py"],
    pathex=[str(BASE), str(REPO_ROOT)],
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
        # Root-level modules (repo root, outside desktop-app/)
        "recorder",
        "config",
        "processor",
        "transcriber",
        "merger",
        "summarizer",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # ── Heavy packages NOT used by the desktop app ──
        "torch", "torchvision", "torchaudio",
        "tensorflow", "tensorboard", "keras",
        "pandas", "pandas.io",
        "boto3", "botocore", "s3transfer",
        "sqlalchemy",
        "numba", "llvmlite",
        "matplotlib", "mpl_toolkits",
        "PIL", "Pillow",
        "uvicorn", "starlette", "fastapi",
        "opentelemetry",
        "gradio",                    # old web UI, not needed in .exe
        "IPython", "ipykernel", "ipywidgets", "jupyter",
        "pytest",
        "setuptools", "pip", "wheel",
        "tkinter", "_tkinter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name=f"SotDL-RPG-Recorder-v{_version}",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window — pure GUI
    icon=None,      # TODO: Add .ico file
)
