from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bf.core.paths import fichier_memoire


@dataclass
class MemoireBF:
    """Court terme en RAM, préférences et contexte projet sur disque (sans secrets)."""

    chemin: Path = field(default_factory=fichier_memoire)
    court_terme: dict[str, Any] = field(default_factory=dict)
    long_terme: dict[str, Any] = field(default_factory=dict)

    def charger(self) -> None:
        if not self.chemin.exists():
            self.long_terme = {"preferences": {}, "projet": {}, "taches": []}
            return
        try:
            self.long_terme = json.loads(self.chemin.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.long_terme = {"preferences": {}, "projet": {}, "taches": []}

    def sauvegarder(self) -> None:
        self.chemin.parent.mkdir(parents=True, exist_ok=True)
        self.chemin.write_text(json.dumps(self.long_terme, indent=2, ensure_ascii=False), encoding="utf-8")

    def noter(self, cle: str, valeur: Any) -> None:
        self.court_terme[cle] = valeur

    def projet(self) -> dict[str, Any]:
        return dict(self.long_terme.get("projet") or {})

    def definir_projet(self, chemin: str, extra: dict[str, Any] | None = None) -> None:
        self.long_terme["projet"] = {"chemin": chemin, **(extra or {})}
        self.sauvegarder()

    def enregistrer_erreur(self, message: str) -> None:
        erreurs = list(self.court_terme.get("erreurs") or [])
        erreurs.append(message)
        self.court_terme["erreurs"] = erreurs[-20:]

    def effacer(self, tout: bool = False) -> None:
        self.court_terme.clear()
        if tout:
            self.long_terme = {"preferences": {}, "projet": {}, "taches": []}
            self.sauvegarder()
