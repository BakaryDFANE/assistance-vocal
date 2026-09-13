from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bf.core.paths import fichier_journal_actions


class JournalActions:
    def __init__(self, chemin: Path | None = None) -> None:
        self.chemin = chemin or fichier_journal_actions()
        self.chemin.parent.mkdir(parents=True, exist_ok=True)

    def enregistrer(
        self,
        action: str,
        outil: str,
        resultat: str,
        erreur: str = "",
        extra: dict[str, Any] | None = None,
    ) -> None:
        ligne = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "outil": outil,
            "resultat": resultat,
            "erreur": erreur,
        }
        if extra:
            ligne["extra"] = extra
        with self.chemin.open("a", encoding="utf-8") as flux:
            flux.write(json.dumps(ligne, ensure_ascii=False) + "\n")

    def lire(self, limite: int = 200) -> list[dict[str, Any]]:
        if not self.chemin.exists():
            return []
        lignes = self.chemin.read_text(encoding="utf-8").splitlines()
        selection = lignes[-limite:]
        resultats: list[dict[str, Any]] = []
        for ligne in selection:
            try:
                resultats.append(json.loads(ligne))
            except json.JSONDecodeError:
                continue
        return resultats
