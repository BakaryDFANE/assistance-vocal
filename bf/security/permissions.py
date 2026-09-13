from __future__ import annotations

from enum import Enum


class NiveauPermission(str, Enum):
    SAFE = "safe"
    CONFIRM = "confirm"
    RESTRICTED = "restricted"


ACTIONS_INTERDITES = (
    "voler des identifiants",
    "contourner une protection",
    "desactiver la securite",
)


def action_autorisee(niveau: NiveauPermission, confirmation: bool, confirmee: bool) -> bool:
    if niveau is NiveauPermission.SAFE:
        return True
    if niveau is NiveauPermission.CONFIRM:
        return (not confirmation) or confirmee
    return confirmee
