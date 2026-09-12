# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


block_cipher = None
racine = Path.cwd()
icone = racine / "assets" / "bf.ico"


a = Analysis(
    ["assistant_bf.py"],
    pathex=[str(racine)],
    binaries=[],
    datas=[(str(racine / "assets"), "assets")] if (racine / "assets").exists() else [],
    hiddenimports=[
        "pystray",
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageTk",
        "speech_recognition",
        "pyttsx3",
        "wikipedia",
        "requests",
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
