from __future__ import annotations

from pathlib import Path

from bf.core.paths import dossier_demarrage_windows, racine_application
import sys


def chemin_lancement() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    script = racine_application() / "assistant_bf.py"
    return f'"{sys.executable}" "{script}"'


def appliquer_demarrage_windows(actif: bool) -> Path:
    cible = dossier_demarrage_windows() / "BF.bat"
    if not actif:
        if cible.exists():
            cible.unlink()
        return cible
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_text(
        f"@echo off\nstart \"\" {chemin_lancement()}\n",
        encoding="utf-8",
    )
    return cible
