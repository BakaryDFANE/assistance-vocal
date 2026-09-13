from __future__ import annotations

import re
import unicodedata


def normaliser_texte(texte: str) -> str:
    texte = texte.lower()
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(caractere for caractere in texte if unicodedata.category(caractere) != "Mn")
    texte = re.sub(r"[^a-z0-9]+", " ", texte)
    return re.sub(r"\s+", " ", texte).strip()


def retirer_motif(texte: str, motifs: list[str]) -> str:
    resultat = texte
    for motif in motifs:
        resultat = re.sub(re.escape(motif), " ", resultat, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", resultat).strip()
