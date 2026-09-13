from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from bf.core.paths import dossier_donnees_utilisateur


def configurer_logging(niveau: str = "INFO") -> logging.Logger:
    journal = logging.getLogger("BF")
    if journal.handlers:
        journal.setLevel(getattr(logging, niveau.upper(), logging.INFO))
        return journal

    fichier_log = dossier_donnees_utilisateur() / "bf.log"
    journal.setLevel(getattr(logging, niveau.upper(), logging.INFO))
    handler = RotatingFileHandler(
        fichier_log,
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s %(message)s"))
    journal.addHandler(handler)
    journal.propagate = False
    return journal
