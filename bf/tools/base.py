from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from bf.security.permissions import NiveauPermission


@dataclass
class ResultatOutil:
    succes: bool
    message: str
    donnees: dict[str, Any] = field(default_factory=dict)
    erreur: str = ""


@dataclass
class Outil:
    nom: str
    description: str
    permission: NiveauPermission
    parametres: dict[str, str]
    executer: Callable[..., ResultatOutil]
    actif: bool = True


class ConfirmationRequise(Exception):
    def __init__(self, message: str, action: str, arguments: dict[str, Any]) -> None:
        super().__init__(message)
        self.message = message
        self.action = action
        self.arguments = arguments
