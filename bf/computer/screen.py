from __future__ import annotations

from io import BytesIO

from bf.security.permissions import NiveauPermission
from bf.tools.base import Outil, ResultatOutil


def capturer_ecran() -> bytes | None:
    try:
        from PIL import ImageGrab
    except ImportError:
        return None
    image = ImageGrab.grab()
    tampon = BytesIO()
    image.save(tampon, format="PNG")
    return tampon.getvalue()


def creer_outil_ecran() -> Outil:
    def executer(action: str = "capture") -> ResultatOutil:
        donnees = capturer_ecran()
        if not donnees:
            return ResultatOutil(False, "Capture d'écran indisponible.", erreur="grab")
        return ResultatOutil(
            True,
            "J'ai une capture de l'écran. L'analyse visuelle avancée sera branchée progressivement.",
            {"taille": len(donnees), "format": "png"},
        )

    return Outil(
        nom="screen",
        description="Capture l'écran pour analyse visuelle (sans enregistrement disque).",
        permission=NiveauPermission.CONFIRM,
        parametres={"action": "capture"},
        executer=executer,
    )
