# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

import certifi


block_cipher = None
racine = Path.cwd()
icone = racine / "assets" / "bf.ico"

donnees = []
if (racine / "assets").exists():
    donnees.append((str(racine / "assets"), "assets"))
# Corrige les erreurs SSL ("CERTIFICATE_VERIFY_FAILED") frequentes une fois
# l'app compilee : PyInstaller n'embarque pas le magasin de certificats de
# `certifi` automatiquement, ce qui casse les requetes https (Wikipedia,
# Ollama, Google) uniquement dans le .exe, pas en `python assistant_bf.py`.
donnees.append((certifi.where(), "certifi"))

a = Analysis(
    ["assistant_bf.py"],
    pathex=[str(racine)],
    binaries=[],
    datas=donnees,
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtWebEngineWidgets",
        "pystray",
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageTk",
        "speech_recognition",
        "pyttsx3",
        "pyttsx3.drivers",
        "pyttsx3.drivers.sapi5",
        "wikipedia",
        "requests",
        "certifi",
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
    name="BF",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icone) if icone.exists() else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="BF",
)
