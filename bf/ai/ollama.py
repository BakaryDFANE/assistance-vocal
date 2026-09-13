from __future__ import annotations

import requests

from bf.config.settings import ParametresBF
from bf.core.logging import configurer_logging

journal = configurer_logging()

PERSONNALITE = (
    "Tu es BF, copilote desktop calme, précis, rapide et professionnel. "
    "Réponds brièvement pour une action simple, plus en détail seulement si c'est utile. "
    "Ne invente pas d'actions système que tu n'as pas réellement exécutées."
)


class ClientOllama:
    def __init__(self, parametres: ParametresBF) -> None:
        self.parametres = parametres

    def demander(self, question: str, langue: str = "fr") -> str:
        langue_reponse = "francais" if langue == "fr" else "anglais"
        try:
            reponse = requests.post(
                f"{self.parametres.ollama_url.rstrip('/')}/api/generate",
                json={
                    "model": self.parametres.modele_ia,
                    "prompt": (
                        f"{PERSONNALITE} Réponds en {langue_reponse}.\n"
                        f"Question: {question}"
                    ),
                    "stream": False,
                },
                timeout=60,
            )
            reponse.raise_for_status()
            return str(reponse.json().get("response", "")).strip()
        except requests.RequestException:
            journal.info("Ollama indisponible (%s).", self.parametres.ollama_url)
            return ""
