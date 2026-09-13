from __future__ import annotations

import threading

import pyttsx3

from bf.config.settings import ParametresBF
from bf.core.logging import configurer_logging

journal = configurer_logging()


class SyntheseVocale:
    def __init__(self, parametres: ParametresBF) -> None:
        self.parametres = parametres
        self.verrou = threading.Lock()
        self.moteur = pyttsx3.init()
        self.configurer("fr")

    def configurer(self, langue: str) -> None:
        voix_disponibles = self.moteur.getProperty("voices")
        mots_voix = {
            "fr": ["david", "paul", "homme", "français", "french"],
            "en": ["david", "mark", "male", "english", "anglais"],
        }
        for voix in voix_disponibles:
            nom_voix = f"{voix.name} {voix.id}".lower()
            if any(mot in nom_voix for mot in mots_voix.get(langue, mots_voix["fr"])):
                self.moteur.setProperty("voice", voix.id)
                break
        self.moteur.setProperty("rate", self.parametres.voix_debit)
        self.moteur.setProperty("volume", self.parametres.voix_volume)

    def dire(self, texte: str, langue: str = "fr") -> None:
        with self.verrou:
            try:
                self.configurer(langue)
                self.moteur.say(texte)
                self.moteur.runAndWait()
            except RuntimeError:
                journal.exception("Erreur moteur vocal, reinitialisation.")
                try:
                    self.moteur.stop()
                except Exception:
                    pass
                try:
                    self.moteur = pyttsx3.init()
                    self.configurer(langue)
                except Exception:
                    journal.exception("Impossible de reinitialiser le moteur vocal.")
