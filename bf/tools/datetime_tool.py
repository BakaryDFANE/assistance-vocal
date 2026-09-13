from __future__ import annotations

from datetime import datetime

from bf.security.permissions import NiveauPermission
from bf.tools.base import Outil, ResultatOutil

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = [
    "janvier", "fevrier", "mars", "avril", "mai", "juin",
    "juillet", "aout", "septembre", "octobre", "novembre", "decembre",
]
JOURS_ANGLAIS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MOIS_ANGLAIS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def creer_outil_datetime() -> Outil:
    def executer(sujet: str = "heure", langue: str = "fr") -> ResultatOutil:
        maintenant = datetime.now()
        if sujet == "heure":
            texte = f"Il est {maintenant.strftime('%H:%M')}" if langue == "fr" else f"It is {maintenant.strftime('%H:%M')}"
        elif sujet == "jour":
            if langue == "fr":
                texte = (
                    f"Nous sommes {JOURS[maintenant.weekday()]} {maintenant.day} "
                    f"{MOIS[maintenant.month - 1]} {maintenant.year}."
                )
            else:
                texte = (
                    f"Today is {JOURS_ANGLAIS[maintenant.weekday()]}, "
                    f"{MOIS_ANGLAIS[maintenant.month - 1]} {maintenant.day}, {maintenant.year}."
                )
        else:
            date = maintenant.strftime("%d/%m/%Y")
            texte = f"Nous sommes le {date}" if langue == "fr" else f"The date is {date}"
        return ResultatOutil(True, texte, {"iso": maintenant.isoformat()})

    return Outil(
        nom="datetime",
        description="Donne l'heure, le jour ou la date.",
        permission=NiveauPermission.SAFE,
        parametres={"sujet": "heure|jour|date", "langue": "fr|en"},
        executer=executer,
    )
