from __future__ import annotations

import webbrowser

from bf.security.permissions import NiveauPermission
from bf.tools.base import Outil, ResultatOutil


def creer_outil_web() -> Outil:
    def executer(recherche: str) -> ResultatOutil:
        if not recherche:
            return ResultatOutil(False, "Indique ce que tu veux chercher.", erreur="empty")
        webbrowser.open(f"https://www.google.com/search?q={recherche}")
        return ResultatOutil(True, f"J'ouvre Google pour {recherche}.")

    return Outil(
        nom="web_search",
        description="Ouvre une recherche Google dans le navigateur.",
        permission=NiveauPermission.SAFE,
        parametres={"recherche": "texte"},
        executer=executer,
    )


def creer_outil_images() -> Outil:
    def executer(recherche: str) -> ResultatOutil:
        if not recherche:
            return ResultatOutil(False, "Indique quelle image tu veux voir.", erreur="empty")
        webbrowser.open(f"https://www.google.com/search?tbm=isch&q={recherche}")
        return ResultatOutil(True, f"J'ouvre Google Images pour {recherche}.")

    return Outil(
        nom="image_search",
        description="Ouvre une recherche d'images.",
        permission=NiveauPermission.SAFE,
        parametres={"recherche": "texte"},
        executer=executer,
    )
