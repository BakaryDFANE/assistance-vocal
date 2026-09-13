from __future__ import annotations

import queue
import sys
import threading
from typing import Any

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from bf.ai.ollama import ClientOllama
from bf.ai.planner import PlanTache, Planificateur, StatutEtape
from bf.computer.screen import creer_outil_ecran
from bf.computer.startup import appliquer_demarrage_windows
from bf.config.settings import ParametresBF, charger_parametres, enregistrer_parametres
from bf.core.events import BusEvenements
from bf.core.logging import configurer_logging
from bf.core.state import EtatBF
from bf.memory.store import MemoireBF
from bf.plugins import charger_plugins
from bf.security.audit import JournalActions
from bf.tools.application_tool import creer_outil_applications, creer_outil_projet
from bf.tools.base import ConfirmationRequise
from bf.tools.datetime_tool import creer_outil_datetime
from bf.tools.filesystem_tool import creer_outil_fichiers
from bf.tools.knowledge_tool import creer_outil_connaissance
from bf.tools.registry import RegistreOutils
from bf.tools.web_tool import creer_outil_images, creer_outil_web
from bf.ui.main_window import FenetrePrincipale
from bf.ui.overlay import OverlayBF
from bf.ui.tray import BarreSysteme
from bf.voice.stt import ReconnaissanceVocale
from bf.voice.tts import SyntheseVocale
from bf.wakeword.detector import DetecteurWakeWord

journal = configurer_logging()


class RuntimeBF:
    def __init__(self, application: QApplication, parametres: ParametresBF) -> None:
        self.application = application
        self.parametres = parametres
        self.bus = BusEvenements()
        self.etat = EtatBF.IDLE
        self.actions: queue.Queue[tuple] = queue.Queue()
        self.ecoute_active = False
        self.fermeture = False
        self.verrou_commande = threading.Lock()
        self.langue = parametres.langue
        self.plan_courant: PlanTache | None = None
        self.confirmation_en_attente: dict[str, Any] | None = None

        self.memoire = MemoireBF()
        self.memoire.charger()
        self.audit = JournalActions()
        self.stt = ReconnaissanceVocale(parametres)
        self.tts = SyntheseVocale(parametres)
        self.wake = DetecteurWakeWord(parametres)
        self.planificateur = Planificateur()
        self.ollama = ClientOllama(parametres)
        self.outils = self._construire_outils()

        self.fenetre = FenetrePrincipale(parametres)
        self.overlay = OverlayBF()
        self.fenetre.fermeture_demandee.connect(self.masquer)
        self.fenetre.message_texte.connect(self.recevoir_texte)
        self.fenetre.ecoute_demandee.connect(self.basculer_ecoute)
        self.fenetre.parametres_enregistres.connect(self.sauver_parametres)
        self.fenetre.memoire_effacee.connect(self.effacer_memoire)

        self.barre = BarreSysteme(
            ouvrir=lambda: self.actions.put(("afficher",)),
            ecoute=lambda: self.actions.put(("basculer_ecoute",)),
            quitter=lambda: self.actions.put(("quitter",)),
        )
        self._pomper_ui()
        QTimer.singleShot(400, self._demarrage)

    def _construire_outils(self) -> RegistreOutils:
        registre = RegistreOutils(self.audit, self.parametres.confirmer_actions_sensibles)
        registre.enregistrer(creer_outil_datetime())
        registre.enregistrer(creer_outil_web())
        registre.enregistrer(creer_outil_images())
        registre.enregistrer(creer_outil_connaissance(self.ollama))
        registre.enregistrer(creer_outil_applications())
        registre.enregistrer(
            creer_outil_projet(self.parametres.racines_autorisees, self.parametres.projet_actif)
        )
        registre.enregistrer(creer_outil_fichiers(self.parametres.racines_autorisees))
        registre.enregistrer(creer_outil_ecran())
        charger_plugins(registre)
        registre.activer(self.parametres.outils_actifs)
        return registre

    def _demarrage(self) -> None:
        if self.parametres.demarrer_en_arriere_plan:
            self.fenetre.hide()
            self.overlay.hide()
        else:
            self.fenetre.show()
        self.basculer_ecoute()
        self.parler("BF est lancé. Dis BF pour me parler.")

    def masquer(self) -> None:
        self.fenetre.hide()
        self.overlay.hide()

    def afficher(self, overlay: bool = True) -> None:
        if overlay:
            ecran = self.application.primaryScreen()
            if ecran is not None:
                self.overlay.placer_coin(ecran)
            self.overlay.show()
            self.overlay.raise_()
        self.fenetre.showNormal()
        self.fenetre.raise_()

    def changer_etat(self, etat: EtatBF, tache: str = "") -> None:
        self.etat = etat
        etapes = self.plan_courant.libelles() if self.plan_courant else None
        self.actions.put(("etat", etat, tache, etapes))

    def _pomper_ui(self) -> None:
        while not self.actions.empty():
            action = self.actions.get()
            nom = action[0]
            if nom == "message":
                self.afficher(overlay=True)
                self.fenetre.ajouter_message(action[1], action[2])
            elif nom == "etat":
                _, etat, tache, etapes = action
                self.fenetre.appliquer_etat(etat, tache, etapes)
                self.overlay.appliquer_etat(etat, tache, etapes)
                if etat is EtatBF.IDLE:
                    QTimer.singleShot(
                        int(self.parametres.masquer_overlay_apres_secondes * 1000),
                        self._masquer_overlay_si_idle,
                    )
            elif nom == "afficher":
                self.afficher(overlay=True)
            elif nom == "basculer_ecoute":
                self.basculer_ecoute()
            elif nom == "quitter":
                self.quitter()
            elif nom == "journal":
                self.fenetre.definir_journal(action[1])
        if not self.fermeture:
            QTimer.singleShot(80, self._pomper_ui)

    def _masquer_overlay_si_idle(self) -> None:
        if self.etat is EtatBF.IDLE:
            self.overlay.hide()

    def recevoir_texte(self, texte: str) -> None:
        self.actions.put(("message", "Vous", texte))
        threading.Thread(target=self.executer_protege, args=(texte,), daemon=True).start()

    def sauver_parametres(self, parametres: ParametresBF) -> None:
        self.parametres = parametres
        enregistrer_parametres(parametres)
        appliquer_demarrage_windows(parametres.demarrer_avec_windows)
        self.wake = DetecteurWakeWord(parametres)
        self.stt.parametres = parametres
        self.tts.parametres = parametres
        self.ollama.parametres = parametres
        self.outils = self._construire_outils()
        self.parler("Paramètres enregistrés.")

    def effacer_memoire(self) -> None:
        self.memoire.effacer(tout=True)
        self.parler("Mémoire effacée.")

    def parler(self, texte: str) -> None:
        self.actions.put(("message", "BF", texte))
        journal.info("BF : %s", texte)
        self.changer_etat(EtatBF.SUCCESS if self.etat is not EtatBF.ERROR else EtatBF.ERROR, texte)
        self.tts.dire(texte, self.langue)

    def basculer_ecoute(self) -> None:
        if self.ecoute_active:
            self.ecoute_active = False
            self.changer_etat(EtatBF.IDLE, "Écoute arrêtée")
            return
        self.ecoute_active = True
        threading.Thread(target=self._boucle_ecoute, daemon=True).start()

    def _boucle_ecoute(self) -> None:
        self.changer_etat(EtatBF.IDLE, "Veille — mot d'activation")
        while self.ecoute_active:
            try:
                mode = "commande" if self.etat is EtatBF.LISTENING else "veille"
                texte = self._entendre(mode)
                if not texte:
                    continue
                nom, reste = self.wake.extraire(texte)
                if self.confirmation_en_attente:
                    if self.wake.present(texte) or reste:
                        self._traiter_confirmation(texte)
                    continue
                if nom:
                    self.actions.put(("afficher",))
                    self.changer_etat(EtatBF.LISTENING, "Listening")
                    commande = reste
                    if not commande:
                        self.parler("Oui, je t'écoute.")
                        self.changer_etat(EtatBF.LISTENING, "Listening")
                        commande = self._entendre("commande")
                    if commande:
                        self.actions.put(("message", "Vous", commande))
                        if not self.executer_protege(commande):
                            self.ecoute_active = False
                    self.changer_etat(EtatBF.IDLE, "En veille")
                elif self.parametres.commandes_sans_mot_activation:
                    self.actions.put(("afficher",))
                    self.actions.put(("message", "Vous", texte))
                    if not self.executer_protege(texte):
                        self.ecoute_active = False
                    self.changer_etat(EtatBF.IDLE, "En veille")
            except OSError:
                self.ecoute_active = False
                self.parler("Je ne trouve pas de microphone. Vérifie qu'il est autorisé dans Windows.")
                self.changer_etat(EtatBF.ERROR, "Microphone indisponible")
            except Exception:
                journal.exception("Erreur dans la boucle d'écoute, on continue.")
                self.changer_etat(EtatBF.ERROR, "Nouvel essai…")

    def _entendre(self, mode: str) -> str:
        timeout, phrase = (3.0, 3.0) if mode == "veille" else (8.0, 8.0)
        if mode != "veille":
            self.changer_etat(EtatBF.LISTENING, "Listening")
        audio = self.stt.capturer(timeout=timeout, phrase=phrase)
        if audio is None:
            return ""
        texte, langue = self.stt.transcrire(audio)
        if texte:
            self.langue = langue
            journal.info("Vous (%s) : %s", langue, texte)
        return texte

    def _traiter_confirmation(self, texte: str) -> None:
        attente = self.confirmation_en_attente
        self.confirmation_en_attente = None
        if attente is None:
            return
        normalise = texte.lower()
        if any(mot in normalise for mot in ["non", "no", "annule"]):
            self.parler("D'accord, j'annule.")
            self.changer_etat(EtatBF.IDLE)
            return
        resultat = self.outils.executer(attente["outil"], confirmee=True, **attente["arguments"])
        self.parler(resultat.message)
        self.changer_etat(EtatBF.SUCCESS if resultat.succes else EtatBF.ERROR)

    def executer_protege(self, commande: str) -> bool:
        if not self.verrou_commande.acquire(blocking=False):
            self.parler("Je traite déjà une demande, une seconde.")
            return True
        try:
            return self.executer(commande)
        finally:
            self.verrou_commande.release()

    def executer(self, commande: str) -> bool:
        self.changer_etat(EtatBF.THINKING, "Thinking")
        if self.confirmation_en_attente:
            self._traiter_confirmation(commande)
            return True

        plan = self.planificateur.construire(commande, self.langue)
        self.plan_courant = plan
        if plan.intention == "stop":
            self.parler("D'accord, je m'arrête." if self.langue == "fr" else "Okay, I will stop listening.")
            return False

        self.changer_etat(EtatBF.PLANNING, "Planning")
        if self.parametres.memoire_active:
            self.memoire.noter("derniere_commande", commande)

        messages: list[str] = []
        for etape in plan.etapes:
            if not etape.outil:
                etape.statut = StatutEtape.OK
                continue
            self.changer_etat(EtatBF.EXECUTING, etape.titre)
            etape.statut = StatutEtape.EN_COURS
            try:
                resultat = self.outils.executer(etape.outil, **etape.arguments)
            except ConfirmationRequise as demande:
                etape.statut = StatutEtape.IGNORE
                self.confirmation_en_attente = {"outil": demande.action, "arguments": demande.arguments}
                self.changer_etat(EtatBF.CONFIRMATION_REQUIRED, demande.message)
                self.parler(f"{demande.message} Dis oui BF ou non BF.")
                return True
            except Exception as erreur:
                journal.exception("Étape échouée: %s", etape.titre)
                if self.parametres.memoire_active:
                    self.memoire.enregistrer_erreur(str(erreur))
                try:
                    resultat = self.outils.executer(etape.outil, **etape.arguments)
                except Exception:
                    etape.statut = StatutEtape.ERREUR
                    etape.resultat = str(erreur)
                    self.changer_etat(EtatBF.ERROR, f"Bloqué: {etape.titre}")
                    self.parler(f"Je n'ai pas pu terminer l'étape « {etape.titre} ». {erreur}")
                    return True
            if not resultat.succes and etape.outil == "knowledge":
                web = self.outils.executer("web_search", recherche=commande)
                messages.append(web.message)
                etape.statut = StatutEtape.OK
                continue
            etape.statut = StatutEtape.OK if resultat.succes else StatutEtape.ERREUR
            etape.resultat = resultat.message
            if resultat.message:
                messages.append(resultat.message)
            if not resultat.succes:
                self.changer_etat(EtatBF.ERROR, etape.titre)
                self.parler(resultat.message)
                return True

        texte = " ".join(messages).strip() or "C'est fait."
        self.changer_etat(EtatBF.SUCCESS, "Completed")
        self.parler(texte)
        self.changer_etat(EtatBF.IDLE, "En veille")
        self._rafraichir_journal()
        return True

    def _rafraichir_journal(self) -> None:
        lignes = [
            f"{item.get('timestamp', '')}  {item.get('outil')}  {item.get('resultat')}  {item.get('erreur', '')}"
            for item in self.audit.lire(80)
        ]
        self.actions.put(("journal", lignes))

    def quitter(self) -> None:
        self.fermeture = True
        self.ecoute_active = False
        self.barre.arreter()
        self.overlay.close()
        self.fenetre.close()
        self.application.quit()
