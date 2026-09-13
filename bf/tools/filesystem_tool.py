from __future__ import annotations

from pathlib import Path

from bf.files.operations import lister, lire, ecrire, supprimer, chemin_autorise
from bf.security.permissions import NiveauPermission
from bf.tools.base import Outil, ResultatOutil


def creer_outil_fichiers(racines: list[str]) -> Outil:
    def executer(action: str, chemin: str, contenu: str = "") -> ResultatOutil:
        cible = Path(chemin).expanduser()
        if not chemin_autorise(cible, racines):
            return ResultatOutil(
                False,
                "Ce chemin n'est pas dans les dossiers autorisés.",
                erreur="forbidden_path",
            )
        if action == "list":
            return lister(cible)
        if action == "read":
            return lire(cible)
        if action == "write":
            return ecrire(cible, contenu)
        if action == "delete":
            return supprimer(cible)
        return ResultatOutil(False, f"Action fichier inconnue: {action}", erreur="unknown_action")

    return Outil(
        nom="filesystem",
        description="Liste, lit, écrit ou supprime un fichier dans les racines autorisées.",
        permission=NiveauPermission.CONFIRM,
        parametres={"action": "list|read|write|delete", "chemin": "chemin", "contenu": "optionnel"},
        executer=executer,
    )
