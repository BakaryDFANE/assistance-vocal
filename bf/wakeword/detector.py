from __future__ import annotations

from bf.config.settings import ParametresBF
from bf.core.text import normaliser_texte


class DetecteurWakeWord:
    def __init__(self, parametres: ParametresBF) -> None:
        self.parametres = parametres

    def extraire(self, texte: str) -> tuple[str, str]:
        """Retourne (nom_détecté, reste_de_la_commande)."""
        normalise = normaliser_texte(texte)
        for nom in self.parametres.noms_activation():
            motif = normaliser_texte(nom)
            if motif and motif in normalise:
                reste = normalise.replace(motif, " ", 1).strip()
                return nom, reste
        return "", texte.strip()

    def present(self, texte: str) -> bool:
        return bool(self.extraire(texte)[0])
