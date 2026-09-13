from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from bf.core.paths import fichier_config


@dataclass
class ParametresBF:
    mot_activation: str = "bf"
    alias_activation: list[str] = field(default_factory=lambda: ["bf", "b f", "be ef", "bef"])
    microphone_index: int | None = None
    voix_debit: int = 170
    voix_volume: float = 1.0
    raccourci_ecoute: str = ""
    demarrer_avec_windows: bool = False
    demarrer_en_arriere_plan: bool = False
    commandes_sans_mot_activation: bool = False
    confirmer_actions_sensibles: bool = True
    memoire_active: bool = True
    apparence: str = "cyber"
    niveau_logs: str = "INFO"
    outils_actifs: list[str] = field(
        default_factory=lambda: [
            "datetime",
            "web_search",
            "image_search",
            "knowledge",
            "application",
            "project",
            "filesystem",
        ]
    )
    racines_autorisees: list[str] = field(default_factory=list)
    projet_actif: str = ""
    masquer_overlay_apres_secondes: float = 8.0
    langue: str = "fr"

    def noms_activation(self) -> list[str]:
        noms = [self.mot_activation, *self.alias_activation]
        vus: list[str] = []
        for nom in noms:
            nom = nom.strip().lower()
            if nom and nom not in vus:
                vus.append(nom)
        return vus


def _depuis_env(parametres: ParametresBF) -> ParametresBF:
    return parametres


def charger_parametres(chemin: Path | None = None) -> ParametresBF:
    cible = chemin or fichier_config()
    parametres = ParametresBF()
    if cible.exists():
        try:
            brut = json.loads(cible.read_text(encoding="utf-8"))
            connus = {item.name for item in fields(ParametresBF)}
            filtres = {cle: valeur for cle, valeur in brut.items() if cle in connus}
            parametres = ParametresBF(**{**asdict(parametres), **filtres})
        except (OSError, json.JSONDecodeError, TypeError):
            parametres = ParametresBF()
    return _depuis_env(parametres)


def enregistrer_parametres(parametres: ParametresBF, chemin: Path | None = None) -> None:
    cible = chemin or fichier_config()
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_text(json.dumps(asdict(parametres), indent=2, ensure_ascii=False), encoding="utf-8")
