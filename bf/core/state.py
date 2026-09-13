from __future__ import annotations

from enum import Enum


class EtatBF(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"
    SUCCESS = "success"
    ERROR = "error"
    CONFIRMATION_REQUIRED = "confirmation_required"

    @property
    def libelle(self) -> str:
        return {
            EtatBF.IDLE: "En veille",
            EtatBF.LISTENING: "Listening",
            EtatBF.THINKING: "Thinking",
            EtatBF.PLANNING: "Planning",
            EtatBF.EXECUTING: "Executing",
            EtatBF.WAITING: "Waiting",
            EtatBF.SUCCESS: "Completed",
            EtatBF.ERROR: "Error",
            EtatBF.CONFIRMATION_REQUIRED: "Confirmation required",
        }[self]

    @property
    def etat_visuel(self) -> str:
        """Identifiant transmis au visualiseur HTML."""
        mapping = {
            EtatBF.IDLE: "idle",
            EtatBF.LISTENING: "listening",
            EtatBF.THINKING: "thinking",
            EtatBF.PLANNING: "planning",
            EtatBF.EXECUTING: "executing",
            EtatBF.WAITING: "waiting",
            EtatBF.SUCCESS: "success",
            EtatBF.ERROR: "error",
            EtatBF.CONFIRMATION_REQUIRED: "confirmation",
        }
        return mapping[self]
