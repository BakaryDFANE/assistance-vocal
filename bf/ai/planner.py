from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from bf.ai.intent import Intention, RouteurIntentions


class StatutEtape(str, Enum):
    EN_ATTENTE = "pending"
    EN_COURS = "running"
    OK = "ok"
    ERREUR = "error"
    IGNORE = "skipped"


@dataclass
class EtapePlan:
    titre: str
    outil: str
    arguments: dict[str, Any]
    statut: StatutEtape = StatutEtape.EN_ATTENTE
    resultat: str = ""


@dataclass
class PlanTache:
    intention: str
    etapes: list[EtapePlan] = field(default_factory=list)

    def libelles(self) -> list[str]:
        return [etape.titre for etape in self.etapes]


class Planificateur:
    def __init__(self) -> None:
        self.routeur = RouteurIntentions()

    def construire(self, commande: str, langue: str = "fr") -> PlanTache:
        intention = self.routeur.interpreter(commande, langue)
        if intention.nom == "stop":
            return PlanTache("stop", [])
        if intention.nom in {"confirm_yes", "confirm_no"}:
            return PlanTache(intention.nom, [])
        if not intention.outil:
            return PlanTache(intention.nom, [])

        etapes = [
            EtapePlan("Compréhension de la demande", "", {}),
            EtapePlan(
                _titre(intention),
                intention.outil,
                intention.arguments,
            ),
            EtapePlan("Vérification du résultat", "", {}),
        ]
        if intention.outil == "project" and intention.arguments.get("action") == "structure":
            etapes.insert(
                2,
                EtapePlan("Analyse de la structure", "project", {"action": "structure"}),
            )
        return PlanTache(intention.nom, etapes)


def _titre(intention: Intention) -> str:
    titres = {
        "datetime": "Lecture de l'horloge",
        "search": "Recherche web",
        "image": "Recherche d'images",
        "app": "Ouverture d'application",
        "project": "Analyse du projet",
        "knowledge": "Raisonnement",
    }
    return titres.get(intention.nom, f"Exécution ({intention.outil})")
