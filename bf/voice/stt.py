from __future__ import annotations

import json

import speech_recognition as sr

from bf.config.settings import ParametresBF
from bf.core.logging import configurer_logging
from bf.core.paths import chemin_ressource

journal = configurer_logging()

try:
    from vosk import KaldiRecognizer
    from vosk import Model as ModeleVosk
except ImportError:
    ModeleVosk = None
    KaldiRecognizer = None

LANGUES_RECONNAISSANCE = [("fr-FR", "fr"), ("en-US", "en")]
MODELES_VOSK = {
    "fr": "vosk-model-small-fr-0.22",
    "en": "vosk-model-small-en-us-0.15",
}
FREQUENCE_VOSK = 16000


class ReconnaissanceVocale:
    def __init__(self, parametres: ParametresBF) -> None:
        self.parametres = parametres
        self.recognizer = sr.Recognizer()
        self.modeles_vosk: dict[str, object] = {}

    def _source(self) -> sr.Microphone:
        if self.parametres.microphone_index is None:
            return sr.Microphone()
        return sr.Microphone(device_index=self.parametres.microphone_index)

    def capturer(self, timeout: float, phrase: float) -> sr.AudioData | None:
        try:
            with self._source() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                return self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase)
        except sr.WaitTimeoutError:
            return None
        except OSError:
            journal.exception("Microphone indisponible.")
            raise
        except Exception:
            journal.exception("Erreur pendant la capture audio.")
            return None

    def transcrire(self, audio: sr.AudioData) -> tuple[str, str]:
        """Retourne (texte, langue). L'audio n'est jamais persisté."""
        resultats = self._reconnaitre_hors_ligne(audio) or self._reconnaitre_en_ligne(audio)
        if not resultats:
            return "", self.parametres.langue
        _, langue, texte = max(resultats, key=lambda item: item[0])
        return texte, langue

    def _charger_vosk(self, langue: str):
        if ModeleVosk is None:
            return None
        if langue in self.modeles_vosk:
            return self.modeles_vosk[langue]
        nom_dossier = MODELES_VOSK.get(langue)
        modele = None
        if nom_dossier:
            chemin = chemin_ressource(f"modeles_vosk/{nom_dossier}")
            if chemin.exists():
                try:
                    modele = ModeleVosk(str(chemin))
                    journal.info("Modele Vosk charge (%s) : %s", langue, chemin)
                except Exception:
                    journal.exception("Impossible de charger le modele Vosk %s", chemin)
            else:
                journal.info("Modele Vosk introuvable pour '%s' (%s).", langue, chemin)
        self.modeles_vosk[langue] = modele
        return modele

    def _reconnaitre_hors_ligne(self, audio) -> list[tuple[float, str, str]]:
        resultats: list[tuple[float, str, str]] = []
        for _, langue in LANGUES_RECONNAISSANCE:
            modele = self._charger_vosk(langue)
            if modele is None:
                continue
            try:
                donnees_wav = audio.get_wav_data(convert_rate=FREQUENCE_VOSK, convert_width=2)
                moteur_reco = KaldiRecognizer(modele, FREQUENCE_VOSK)
                moteur_reco.SetWords(True)
                moteur_reco.AcceptWaveform(donnees_wav[44:])
                resultat = json.loads(moteur_reco.FinalResult())
                texte = resultat.get("text", "").strip()
                mots = resultat.get("result", [])
                if not texte:
                    continue
                confiance = (
                    sum(mot.get("conf", 0.75) for mot in mots) / len(mots) if mots else 0.6
                )
                resultats.append((confiance, langue, texte))
            except Exception:
                journal.exception("Erreur de reconnaissance Vosk (%s).", langue)
        return resultats

    def _reconnaitre_en_ligne(self, audio) -> list[tuple[float, str, str]]:
        resultats: list[tuple[float, str, str]] = []
        for code_langue, langue in LANGUES_RECONNAISSANCE:
            try:
                resultat = self.recognizer.recognize_google(
                    audio, language=code_langue, show_all=True
                )
                if not resultat or not resultat.get("alternative"):
                    continue
                meilleure = resultat["alternative"][0]
                resultats.append(
                    (
                        meilleure.get("confidence", 0) or 0,
                        langue,
                        meilleure["transcript"].lower(),
                    )
                )
            except (sr.UnknownValueError, sr.RequestError):
                continue
        return resultats
