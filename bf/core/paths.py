from __future__ import annotations

import os
import sys
from pathlib import Path


def dossier_donnees_utilisateur() -> Path:
    """Dossier écrivable (logs, config), y compris sous Program Files."""
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "BF"
    base.mkdir(parents=True, exist_ok=True)
    (base / "logs").mkdir(exist_ok=True)
    return base


def racine_application() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parents[2]


def chemin_ressource(chemin_relatif: str | Path) -> Path:
    return racine_application() / chemin_relatif


def fichier_config() -> Path:
    return dossier_donnees_utilisateur() / "config.json"


def fichier_memoire() -> Path:
    return dossier_donnees_utilisateur() / "memory.json"


def fichier_journal_actions() -> Path:
    return dossier_donnees_utilisateur() / "logs" / "actions.jsonl"


def dossier_demarrage_windows() -> Path:
    appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    return appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
