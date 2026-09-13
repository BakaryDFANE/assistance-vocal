from __future__ import annotations

from typing import Any

from bf.security.audit import JournalActions
from bf.security.permissions import NiveauPermission, action_autorisee
from bf.tools.base import ConfirmationRequise, Outil, ResultatOutil


class RegistreOutils:
    def __init__(self, journal: JournalActions, confirmer: bool = True) -> None:
        self._outils: dict[str, Outil] = {}
        self.journal = journal
        self.confirmer = confirmer

    def enregistrer(self, outil: Outil) -> None:
        self._outils[outil.nom] = outil

    def liste(self) -> list[Outil]:
        return list(self._outils.values())

    def obtenir(self, nom: str) -> Outil | None:
        return self._outils.get(nom)

    def executer(self, nom: str, confirmee: bool = False, **arguments: Any) -> ResultatOutil:
        outil = self._outils.get(nom)
        if outil is None:
            return ResultatOutil(False, f"Outil inconnu: {nom}", erreur="unknown_tool")
        if not outil.actif:
            return ResultatOutil(False, f"Outil désactivé: {nom}", erreur="disabled")
        if not action_autorisee(outil.permission, self.confirmer, confirmee):
            raise ConfirmationRequise(
                f"Cette opération ({nom}) nécessite une confirmation.",
                nom,
                arguments,
            )
        try:
            resultat = outil.executer(**arguments)
        except TypeError as erreur:
            resultat = ResultatOutil(False, "Paramètres invalides.", erreur=str(erreur))
        except Exception as erreur:  # noqa: BLE001 — journalisé, jamais silencieux
            resultat = ResultatOutil(False, "L'outil a échoué.", erreur=str(erreur))
        self.journal.enregistrer(
            action=nom,
            outil=nom,
            resultat="ok" if resultat.succes else "echec",
            erreur=resultat.erreur,
        )
        return resultat

    def activer(self, noms: list[str]) -> None:
        autorises = set(noms)
        for outil in self._outils.values():
            outil.actif = outil.nom in autorises or not autorises
