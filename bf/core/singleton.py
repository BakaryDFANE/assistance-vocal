from __future__ import annotations

import os

from bf.core.logging import configurer_logging
from bf.core.paths import dossier_donnees_utilisateur

journal = configurer_logging()


class InstanceUnique:
    """Empêche deux processus BF d'écouter le micro en même temps."""

    def __init__(self, nom: str = "BF_assistant_vocal_singleton") -> None:
        self.fichier_verrou = dossier_donnees_utilisateur() / f"{nom}.lock"
        self.handle = None

    def deja_lance(self) -> bool:
        try:
            if os.name == "nt":
                import msvcrt

                self.handle = open(self.fichier_verrou, "w", encoding="utf-8")
                try:
                    msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError:
                    self.handle.close()
                    self.handle = None
                    return True
                return False

            import fcntl

            self.handle = open(self.fichier_verrou, "w", encoding="utf-8")
            try:
                fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                self.handle.close()
                self.handle = None
                return True
            return False
        except Exception:
            journal.exception("Impossible de verifier l'instance unique, on continue.")
            return False
