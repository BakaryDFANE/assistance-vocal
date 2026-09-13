from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from bf.security.permissions import NiveauPermission
from bf.tools.base import Outil, ResultatOutil

ALIAS_APPS = {
    "vscode": ["code", "Code"],
    "vs code": ["code", "Code"],
    "code": ["code"],
    "navigateur": ["msedge", "chrome", "firefox"],
    "browser": ["msedge", "chrome", "firefox"],
    "explorer": ["explorer"],
    "explorateur": ["explorer"],
    "notepad": ["notepad"],
    "bloc notes": ["notepad"],
    "terminal": ["wt", "cmd"],
    "calculatrice": ["calc"],
    "chrome": ["chrome"],
    "google chrome": ["chrome"],
    "edge": ["msedge"],
    "microsoft edge": ["msedge"],
    "firefox": ["firefox"],
    "word": ["winword"],
    "excel": ["excel"],
    "powerpoint": ["powerpnt"],
    "spotify": ["spotify"],
}


def _lancer(commande: str) -> bool:
    executable = shutil.which(commande)
    if executable:
        subprocess.Popen([executable], shell=False)
        return True
    if os.name == "nt":
        try:
            os.startfile(commande)  # type: ignore[attr-defined]
            return True
        except OSError:
            pass
        for raccourci in _raccourcis_menu(commande):
            try:
                os.startfile(raccourci)  # type: ignore[attr-defined]
                return True
            except OSError:
                continue
    return False


def _raccourcis_menu(nom: str) -> list[Path]:
    """Trouve une application installée par son nom dans le menu Démarrer."""
    racines = [
        Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
        Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
    ]
    cible = nom.casefold().replace(".exe", "").replace(".lnk", "").strip()
    trouves: list[Path] = []
    for racine in racines:
        if not racine.is_dir():
            continue
        try:
            candidats = racine.rglob("*.lnk")
        except OSError:
            continue
        for chemin in candidats:
            if chemin.stem.casefold() == cible:
                trouves.append(chemin)
    return trouves


def creer_outil_applications() -> Outil:
    def executer(application: str) -> ResultatOutil:
        nom = application.strip().lower()
        if not nom:
            return ResultatOutil(False, "Quelle application ouvrir ?", erreur="empty")
        candidats = ALIAS_APPS.get(nom, [application])
        for candidat in candidats:
            if _lancer(candidat):
                return ResultatOutil(True, f"J'ouvre {application}.")
        return ResultatOutil(False, f"Impossible d'ouvrir {application}.", erreur="launch")

    return Outil(
        nom="application",
        description="Ouvre une application Windows (VS Code, navigateur, Explorateur...).",
        permission=NiveauPermission.SAFE,
        parametres={"application": "nom ou alias"},
        executer=executer,
    )


def creer_outil_projet(racines: list[str], projet_actif: str) -> Outil:
    def executer(action: str = "structure", chemin: str = "") -> ResultatOutil:
        cible = Path(chemin or projet_actif or (racines[0] if racines else "")).expanduser()
        if not cible.exists() or not cible.is_dir():
            return ResultatOutil(
                False,
                "Aucun projet actif. Indique un dossier dans les paramètres.",
                erreur="no_project",
            )
        if action == "ouvrir":
            if os.name == "nt":
                os.startfile(cible)  # type: ignore[attr-defined]
            return ResultatOutil(True, f"J'ouvre le projet {cible.name}.", {"chemin": str(cible)})

        ignore = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}
        fichiers: list[str] = []
        for racine, dossiers, noms in os.walk(cible):
            dossiers[:] = [d for d in dossiers if d not in ignore]
            for nom in noms:
                relatif = Path(racine, nom).relative_to(cible)
                fichiers.append(str(relatif))
                if len(fichiers) >= 80:
                    break
            if len(fichiers) >= 80:
                break
        resume = f"Projet {cible.name}: {len(fichiers)} fichiers listés."
        return ResultatOutil(True, resume, {"chemin": str(cible), "fichiers": fichiers})

    return Outil(
        nom="project",
        description="Identifie et explore le projet de développement actif.",
        permission=NiveauPermission.SAFE,
        parametres={"action": "structure|ouvrir", "chemin": "optionnel"},
        executer=executer,
    )
