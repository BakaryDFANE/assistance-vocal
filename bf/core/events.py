from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable


@dataclass(frozen=True)
class Evenement:
    type: str
    payload: dict[str, Any] = field(default_factory=dict)


class BusEvenements:
    def __init__(self) -> None:
        self._abonnements: dict[str, list[Callable[[Evenement], None]]] = defaultdict(list)
        self._verrou = Lock()

    def souscrire(self, type_evenement: str, callback: Callable[[Evenement], None]) -> None:
        with self._verrou:
            self._abonnements[type_evenement].append(callback)

    def emettre(self, type_evenement: str, **payload: Any) -> None:
        evenement = Evenement(type_evenement, payload)
        with self._verrou:
            callbacks = list(self._abonnements.get(type_evenement, ()))
            callbacks.extend(self._abonnements.get("*", ()))
        for callback in callbacks:
            callback(evenement)
