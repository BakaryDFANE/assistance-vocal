import io
import logging
import os
import queue
import re
import sys
import threading
import unicodedata
import webbrowser
from datetime import datetime
from pathlib import Path

# --- Correctif exe : en mode "fenetre" (console=False dans BF.spec), Windows/
# PyInstaller ne fournit pas de sys.stdout/sys.stderr valides. Le moindre
# print() fait alors planter l'appli (AttributeError: 'NoneType' object has no
# attribute 'write'). On redirige vers un fichier log AVANT tout print/import
# qui pourrait en emettre.
if getattr(sys, "frozen", False):
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")

    # --- Correctif SSL exe : PyInstaller n'embarque pas toujours les
    # certificats racine utilises par `requests`/`certifi`. Sans ca, les
    # appels a Wikipedia/Ollama/Google echouent en silence dans l'exe alors
    # qu'ils marchent en `python assistant_bf.py`.
    try:
        cacert = Path(sys._MEIPASS) / "certifi" / "cacert.pem"
        if cacert.exists():
            os.environ.setdefault("SSL_CERT_FILE", str(cacert))
            os.environ.setdefault("REQUESTS_CA_BUNDLE", str(cacert))
    except Exception:
        pass

import pyttsx3
import requests
import speech_recognition as sr
import wikipedia
from PySide6.QtCore import QTimer, Qt, Signal, QUrl
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

try:
    from PIL import Image, ImageDraw, ImageTk
except ImportError:
    Image = None
    ImageDraw = None
    ImageTk = None

try:
    import pystray
except ImportError:
    pystray = None


NOM_ASSISTANT = "bf"
NOMS_ACTIVATION = ["bf", "b f", "be ef", "bef"]
MODELE_OLLAMA = "llama3.2"
OLLAMA_URL = "http://localhost:11434"
DEMARRER_EN_ARRIERE_PLAN = True
LANGUES_RECONNAISSANCE = [("fr-FR", "fr"), ("en-US", "en")]


class InstanceUnique:
    """Empeche de lancer BF deux fois en meme temps (ce qui arrivait via le
    lanceur Ctrl+Shift+B qui demarrait un 2e processus par-dessus celui deja
    ouvert en arriere-plan : deux ecoutes micro simultanees, comportement
    imprevisible)."""

    def __init__(self, nom="BF_assistant_vocal_singleton"):
        self.fichier_verrou = dossier_donnees_utilisateur() / f"{nom}.lock"
        self.handle = None

    def deja_lance(self):
        try:
            if os.name == "nt":
                import msvcrt

                self.handle = open(self.fichier_verrou, "w")
                try:
                    msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError:
                    self.handle.close()
                    self.handle = None
                    return True
                return False
            else:
                import fcntl

                self.handle = open(self.fichier_verrou, "w")
                try:
                    fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    self.handle.close()
                    self.handle = None
                    return True
                return False
        except Exception:
            journal.exception("Impossible de verifier l'instance unique, on continue quand meme.")
            return False


class FenetreBF(QMainWindow):
    fermeture_demandee = Signal()

    def closeEvent(self, event):
        self.fermeture_demandee.emit()
        event.ignore()

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
JOURS_ANGLAIS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MOIS = [
    "janvier",
    "fevrier",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "aout",
    "septembre",
    "octobre",
    "novembre",
    "decembre",
]
MOIS_ANGLAIS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

wikipedia.set_lang("fr")


def dossier_donnees_utilisateur():
    """Dossier ecrivable pour les logs/verrous, meme si BF est installe dans
    Program Files (lecture seule) ou lance en .exe."""
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "BF"
    base.mkdir(parents=True, exist_ok=True)
    return base


def configurer_logging():
    dossier = dossier_donnees_utilisateur()
    fichier_log = dossier / "bf.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(fichier_log, encoding="utf-8"),
        ],
    )
    return logging.getLogger("BF")


journal = configurer_logging()


def chemin_ressource(chemin_relatif):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / chemin_relatif


def normaliser_texte(texte):
    texte = texte.lower()
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(caractere for caractere in texte if unicodedata.category(caractere) != "Mn")
    texte = re.sub(r"[^a-z0-9]+", " ", texte)
    return re.sub(r"\s+", " ", texte).strip()


class AssistantBF:
    def __init__(self, fenetre):
        self.fenetre = fenetre
        self.application = QApplication.instance()
        self.fenetre.setWindowTitle("BF - Assistant vocal")
        self.fenetre.resize(1080, 700)
        self.fenetre.setMinimumSize(820, 560)
        self.fenetre.fermeture_demandee.connect(self.masquer_fenetre)

        self.moteur = pyttsx3.init()
        self.verrou_voix = threading.Lock()
        self.recognizer = sr.Recognizer()
        self.actions_interface = queue.Queue()
        self.ecoute_active = False
        self.verrou_commande = threading.Lock()
        self.commande_en_cours = False
        self.thread_ecoute = None
        self.image_actuelle = None
        self.icone_barre_systeme = None
        self.thread_barre_systeme = None
        self.application_en_fermeture = False
        self.langue = "fr"
        self.visualiseur_pret = False
        self.visualiseur_etat = "idle"

        self.choisir_voix_masculine()
        self.creer_interface()
        self.traiter_actions_interface()
        self.creer_icone_barre_systeme()
        self.parler("BF est lance. Dis BF pour me parler.")
        QTimer.singleShot(500, self.demarrer_automatiquement)

    def demarrer_automatiquement(self):
        if DEMARRER_EN_ARRIERE_PLAN:
            self.fenetre.hide()

        if not self.ecoute_active:
            self.basculer_ecoute()

    def creer_interface(self):
        self.action_ctrl_b = QAction(
            self.fenetre.style().standardIcon(QStyle.SP_MediaPlay),
            "Activer l'ecoute",
            self.fenetre,
        )
        self.fenetre.addAction(self.action_ctrl_b)
        self.action_ctrl_b.setShortcut("Ctrl+B")
        self.action_ctrl_b.triggered.connect(self.raccourci_ctrl_b)

        contenu = QWidget()
        principal = QVBoxLayout(contenu)
        principal.setContentsMargins(24, 22, 24, 18)
        principal.setSpacing(16)

        entete = QHBoxLayout()
        titre = QLabel("BF")
        titre.setObjectName("titre")
        sous_titre = QLabel("Assistant vocal personnel")
        sous_titre.setObjectName("sousTitre")
        entete.addWidget(titre)
        entete.addWidget(sous_titre)
        entete.addStretch()
        principal.addLayout(entete)

        zone = QHBoxLayout()
        zone.setSpacing(16)
        self.conversation = QTextEdit()
        self.conversation.setReadOnly(True)
        self.conversation.setPlaceholderText("La conversation apparaitra ici...")
        zone.addWidget(self.conversation, 1)

        self.visualiseur = QWebEngineView()
        self.visualiseur.setMinimumWidth(440)
        self.visualiseur.loadFinished.connect(self.visualiseur_charge)
        self.visualiseur.setUrl(QUrl.fromLocalFile(str(chemin_ressource("assets/visualiseur_bf.html"))))
        zone.addWidget(self.visualiseur, 2)

        panneau_image = QFrame()
        panneau_image.setObjectName("panneauImage")
        panneau_layout = QVBoxLayout(panneau_image)
        panneau_layout.setContentsMargins(18, 18, 18, 18)
        etiquette_image = QLabel("APERÇU")
        etiquette_image.setObjectName("etiquetteSection")
        self.image_label = QLabel("Les images apparaitront ici")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setWordWrap(True)
        panneau_layout.addWidget(etiquette_image)
        panneau_layout.addWidget(self.image_label, 1)
        zone.addWidget(panneau_image, 1)
        principal.addLayout(zone, 1)

        barre_bas = QHBoxLayout()
        self.champ_texte = QLineEdit()
        self.champ_texte.setPlaceholderText("Ecris une commande a BF...")
        self.champ_texte.returnPressed.connect(self.envoyer_message_texte)
        barre_bas.addWidget(self.champ_texte, 1)

        bouton_envoyer = QPushButton("Envoyer")
        bouton_envoyer.setIcon(self.fenetre.style().standardIcon(QStyle.SP_ArrowRight))
        bouton_envoyer.clicked.connect(self.envoyer_message_texte)
        barre_bas.addWidget(bouton_envoyer)

        self.bouton_ecoute = QPushButton("Demarrer l'ecoute")
        self.bouton_ecoute.clicked.connect(self.basculer_ecoute)
        barre_bas.addWidget(self.bouton_ecoute)
        principal.addLayout(barre_bas)

        self.statut = QLabel("Pret - Ctrl+B pour parler")
        self.statut.setObjectName("statut")
        principal.addWidget(self.statut)

        self.fenetre.setCentralWidget(contenu)
        self.fenetre.setStyleSheet(
            """
            QMainWindow, QWidget { background: #101820; color: #f7f1df; }
            #titre { color: #f7f1df; font-size: 30px; font-weight: 700; }
            #sousTitre { color: #a8b3b8; font-size: 15px; padding-top: 8px; }
            QTextEdit, QLineEdit { background: #17242b; border: 1px solid #2c4149; border-radius: 10px; padding: 12px; color: #f7f1df; font-size: 14px; }
            #panneauImage { background: #17242b; border: 1px solid #2c4149; border-radius: 10px; }
            #etiquetteSection { color: #d8b15f; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
            QPushButton { background: #0f766e; border: 0; border-radius: 8px; padding: 11px 16px; color: white; font-weight: 600; }
            QPushButton:hover { background: #14b8a6; }
            #statut { background: #17242b; border-radius: 6px; padding: 8px 12px; color: #a8b3b8; }
            """
        )

    def choisir_voix_masculine(self):
        self.configurer_voix("fr")

    def configurer_voix(self, langue):
        voix_disponibles = self.moteur.getProperty("voices")
        mots_voix = {
            "fr": ["david", "paul", "homme", "français", "french"],
            "en": ["david", "mark", "male", "english", "anglais"],
        }

        for voix in voix_disponibles:
            nom_voix = f"{voix.name} {voix.id}".lower()

            for mot in mots_voix.get(langue, mots_voix["fr"]):
                if mot in nom_voix:
                    self.moteur.setProperty("voice", voix.id)
                    self.moteur.setProperty("rate", 170)
                    self.moteur.setProperty("volume", 1.0)
                    return

        self.moteur.setProperty("rate", 170)
        self.moteur.setProperty("volume", 1.0)

    def raccourci_ctrl_b(self, event=None):
        self.basculer_ecoute()

    def basculer_ecoute(self):
        if self.ecoute_active:
            self.ecoute_active = False
            self.bouton_ecoute.setText("Demarrer l'ecoute")
            self.statut.setText("Ecoute arretee - Ctrl+B pour parler")
            return

        self.ecoute_active = True
        self.bouton_ecoute.setText("Arreter l'ecoute")
        self.thread_ecoute = threading.Thread(target=self.boucle_ecoute, daemon=True)
        self.thread_ecoute.start()

    def ajouter_message(self, auteur, texte):
        self.afficher_fenetre()
        self.conversation.append(f"<b>{auteur}</b> : {texte}")
        self.conversation.verticalScrollBar().setValue(
            self.conversation.verticalScrollBar().maximum()
        )

    def afficher_fenetre(self):
        self.fenetre.showNormal()
        self.fenetre.raise_()
        self.fenetre.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.fenetre.show()
        QTimer.singleShot(
            500,
            self.retirer_fenetre_au_premier_plan,
        )

    def retirer_fenetre_au_premier_plan(self):
        self.fenetre.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.fenetre.show()

    def parler(self, texte):
        self.actions_interface.put(("message", "BF", texte))
        self.actions_interface.put(("visualiseur", "responding"))
        journal.info("BF : %s", texte)
        # Verrou indispensable : pyttsx3 n'est pas reentrant. Sans lui, deux
        # threads qui appellent parler() en meme temps (ex: une commande
        # tapee au clavier pendant que l'ecoute vocale repond) font planter
        # le moteur ("run loop already started") - un des plantages les plus
        # frequents une fois compile en .exe.
        with self.verrou_voix:
            try:
                self.configurer_voix(self.langue)
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
                    self.configurer_voix(self.langue)
                except Exception:
                    journal.exception("Impossible de reinitialiser le moteur vocal.")

    def changer_statut(self, texte):
        self.actions_interface.put(("statut", texte))
        if "ecoute" in texte.lower() or "ecoute" in normaliser_texte(texte):
            etat = "listening"
        elif "traite" in texte.lower() or "traitement" in normaliser_texte(texte):
            etat = "processing"
        else:
            etat = "idle"
        self.actions_interface.put(("visualiseur", etat))

    def mettre_a_jour_visualiseur(self, etat):
        self.visualiseur_etat = etat
        if not self.visualiseur_pret:
            return
        self.visualiseur.page().runJavaScript(
            "typeof window.bfSetState === 'function'",
            lambda pret: self.envoyer_etat_visualiseur(etat) if pret else QTimer.singleShot(
                100,
                lambda: self.mettre_a_jour_visualiseur(self.visualiseur_etat),
            ),
        )

    def envoyer_etat_visualiseur(self, etat):
        self.visualiseur.page().runJavaScript(f"window.bfSetState({etat!r});")

    def visualiseur_charge(self, succes):
        self.visualiseur_pret = succes
        if succes:
            self.mettre_a_jour_visualiseur(self.visualiseur_etat)

    def traiter_actions_interface(self):
        while not self.actions_interface.empty():
            action = self.actions_interface.get()

            if action[0] == "message":
                self.ajouter_message(action[1], action[2])

            elif action[0] == "statut":
                self.statut.setText(action[1])

            elif action[0] == "visualiseur":
                self.mettre_a_jour_visualiseur(action[1])

            elif action[0] == "afficher":
                self.afficher_fenetre()

            elif action[0] == "bouton":
                self.bouton_ecoute.setText(action[1])

            elif action[0] == "image":
                self.afficher_image(action[1])

            elif action[0] == "basculer_ecoute":
                self.basculer_ecoute()

            elif action[0] == "quitter":
                self.quitter_application()

        if not self.application_en_fermeture:
            QTimer.singleShot(100, self.traiter_actions_interface)

    def creer_image_icone(self):
        logo = chemin_ressource("assets/bf.png")
        if logo.exists():
            return Image.open(logo).convert("RGBA")

        image = Image.new("RGBA", (256, 256), "#101820")
        dessin = ImageDraw.Draw(image)
        dessin.ellipse((28, 28, 228, 228), fill="#0f766e")
        dessin.ellipse((52, 52, 204, 204), fill="#14b8a6")
        dessin.text((78, 83), "BF", fill="white")
        return image

    def creer_icone_barre_systeme(self):
        if pystray is None or Image is None or ImageDraw is None:
            return

        menu = pystray.Menu(
            pystray.MenuItem("Ouvrir BF", self.ouvrir_depuis_barre_systeme, default=True),
            pystray.MenuItem(
                "Activer / arreter l'ecoute",
                self.basculer_ecoute_depuis_barre_systeme,
            ),
            pystray.MenuItem("Quitter BF", self.quitter_depuis_barre_systeme),
        )
        self.icone_barre_systeme = pystray.Icon(
            "BF",
            self.creer_image_icone(),
            "BF - Assistant vocal",
            menu,
        )
        self.thread_barre_systeme = threading.Thread(
            target=self.icone_barre_systeme.run,
            daemon=True,
        )
        self.thread_barre_systeme.start()

    def ouvrir_depuis_barre_systeme(self, icon=None, item=None):
        self.actions_interface.put(("afficher",))

    def basculer_ecoute_depuis_barre_systeme(self, icon=None, item=None):
        self.actions_interface.put(("basculer_ecoute",))

    def masquer_fenetre(self):
        self.fenetre.hide()

    def quitter_depuis_barre_systeme(self, icon=None, item=None):
        self.actions_interface.put(("quitter",))

    def quitter_application(self):
        self.application_en_fermeture = True
        self.ecoute_active = False

        if self.icone_barre_systeme is not None:
            self.icone_barre_systeme.stop()

        self.fenetre.close()
        self.application.quit()

    def afficher_image(self, image_bytes):
        pixmap = QPixmap()
        if not pixmap.loadFromData(image_bytes):
            self.image_label.setText("Impossible d'afficher cette image.")
            return

        self.image_actuelle = pixmap.scaled(
            360,
            420,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(self.image_actuelle)

    def envoyer_message_texte(self, event=None):
        commande = self.champ_texte.text().strip().lower()
        self.champ_texte.clear()

        if not commande:
            return

        self.ajouter_message("Vous", commande)
        threading.Thread(target=self.executer_commande_protegee, args=(commande,), daemon=True).start()

    def executer_commande_protegee(self, commande):
        """Empeche deux commandes de tourner en meme temps (ex: on tape au
        clavier pendant que BF traite deja une commande vocale)."""
        if not self.verrou_commande.acquire(blocking=False):
            self.parler(
                "Je traite deja une demande, une seconde."
                if self.langue == "fr"
                else "I'm already handling a request, one second."
            )
            return True
        try:
            return self.executer_commande(commande)
        finally:
            self.verrou_commande.release()

    def ecouter(self):
        try:
            with sr.Microphone() as source:
                self.changer_statut("J'ecoute...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # timeout= : sans micro qui capte du son, listen() attendait
                # indefiniment -> le thread d'ecoute restait bloque "pour
                # toujours" sans jamais planter ni reagir a Ctrl+B/tray.
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=7)
        except sr.WaitTimeoutError:
            self.changer_statut("Pret - Ctrl+B pour parler")
            return ""
        except OSError:
            # Aucun microphone detecte / peripherique deconnecte.
            journal.exception("Microphone indisponible.")
            self.ecoute_active = False
            self.actions_interface.put(
                (
                    "message",
                    "BF",
                    "Je ne trouve pas de microphone. Verifie qu'il est branche et autorise dans Windows.",
                )
            )
            self.actions_interface.put(("statut", "Aucun microphone - Ctrl+B pour reessayer"))
            self.actions_interface.put(("bouton", "Demarrer l'ecoute"))
            return ""
        except Exception:
            journal.exception("Erreur inattendue pendant l'ecoute.")
            self.changer_statut("Pret - Ctrl+B pour parler")
            return ""

        resultats = []
        for code_langue, langue in LANGUES_RECONNAISSANCE:
            try:
                resultat = self.recognizer.recognize_google(
                    audio,
                    language=code_langue,
                    show_all=True,
                )
                if not resultat or not resultat.get("alternative"):
                    continue

                meilleure_alternative = resultat["alternative"][0]
                confiance = meilleure_alternative.get("confidence", 0)
                resultats.append(
                    (
                        confiance,
                        langue,
                        meilleure_alternative["transcript"].lower(),
                    )
                )
            except (sr.UnknownValueError, sr.RequestError):
                continue

        if resultats:
            _, self.langue, texte = max(resultats, key=lambda resultat: resultat[0])
            self.configurer_voix(self.langue)
            wikipedia.set_lang(self.langue)
            journal.info("Vous (%s) : %s", self.langue, texte)
            return texte

        if not resultats:
            self.changer_statut("Je n'ai pas compris")
        return ""

    def boucle_ecoute(self):
        self.changer_statut("Ecoute active")

        while self.ecoute_active:
            try:
                texte = self.ecouter()

                if not texte:
                    continue

                nom_detecte = self.detecter_nom(texte)

                if nom_detecte:
                    self.actions_interface.put(("afficher",))
                    commande = texte.replace(nom_detecte, "").strip()

                    if commande == "":
                        self.parler("Oui, je t'ecoute.")
                        commande = self.ecouter()

                    if commande:
                        self.actions_interface.put(("message", "Vous", commande))
                        continuer = self.executer_commande_protegee(commande)
                        self.arreter_si_termine(continuer)

                elif self.est_commande_directe(texte):
                    self.actions_interface.put(("afficher",))
                    self.actions_interface.put(("message", "Vous", texte))
                    continuer = self.executer_commande_protegee(texte)
                    self.arreter_si_termine(continuer)
            except Exception:
                # Avant ce correctif, une exception ici tuait le thread
                # d'ecoute en silence : le bouton restait sur "Arreter
                # l'ecoute" mais BF ne repondait plus jamais, sans aucun
                # message d'erreur visible.
                journal.exception("Erreur dans la boucle d'ecoute, on continue.")
                self.actions_interface.put(("statut", "Petit souci, je reessaie..."))

    def arreter_si_termine(self, continuer):
        if continuer:
            return

        self.ecoute_active = False
        self.actions_interface.put(("statut", "Ecoute arretee - Ctrl+B pour parler"))
        self.actions_interface.put(("bouton", "Demarrer l'ecoute"))

    def detecter_nom(self, texte):
        texte_normalise = normaliser_texte(texte)

        for nom in NOMS_ACTIVATION:
            if normaliser_texte(nom) in texte_normalise:
                return nom

        return ""

    def est_commande_directe(self, texte):
        texte = normaliser_texte(texte)
        mots_commandes = [
            "heure",
            "date",
            "jour",
            "aujourd hui",
            "cherche",
            "recherche",
            "image",
            "photo",
            "montre",
            "explique",
            "c est quoi",
            "qui est",
            "stop",
            "arrete",
            "time",
            "day",
            "today",
            "search",
            "look up",
            "picture",
            "photo",
            "show me",
            "explain",
            "what is",
            "who is",
            "stop",
            "quit",
        ]

        for mot in mots_commandes:
            if mot in texte:
                return True

        return False

    def nettoyer_commande(self, commande, mots):
        resultat = commande

        for mot in mots:
            resultat = resultat.replace(mot, "")

        return resultat.strip()

    def commande_demande_heure(self, commande):
        commande = normaliser_texte(commande)
        expressions = [
            "heure",
            "quelle heure est il",
            "il est quelle heure",
            "tu as l heure",
            "donne moi l heure",
        ]
        return any(expression in commande for expression in expressions)

    def commande_demande_jour(self, commande):
        commande = normaliser_texte(commande)
        expressions = [
            "quel jour",
            "quelle journee",
            "on est quel jour",
            "nous sommes quel jour",
            "jour sommes nous",
            "aujourd hui",
        ]
        return any(expression in commande for expression in expressions)

    def commande_demande_date(self, commande):
        commande = normaliser_texte(commande)
        expressions = [
            "date",
            "quelle date",
            "on est le combien",
            "nous sommes le combien",
        ]
        return any(expression in commande for expression in expressions)

    def executer_commande(self, commande):
        self.changer_statut("Je traite la demande...")
        commande_normalisee = normaliser_texte(commande)

        if self.commande_demande_heure(commande) or any(
            expression in commande_normalisee
            for expression in ["what time is it", "whats the time", "tell me the time"]
        ):
            heure = datetime.now().strftime("%H:%M")
            self.parler(
                f"Il est {heure}" if self.langue == "fr" else f"It is {heure}"
            )

        elif self.commande_demande_jour(commande) or any(
            expression in commande_normalisee
            for expression in ["what day is it", "which day is it", "what day"]
        ):
            maintenant = datetime.now()
            jour_semaine = JOURS[maintenant.weekday()]
            mois_annee = MOIS[maintenant.month - 1]
            if self.langue == "fr":
                self.parler(
                    f"Nous sommes {jour_semaine} {maintenant.day} {mois_annee} {maintenant.year}."
                )
            else:
                self.parler(
                    f"Today is {JOURS_ANGLAIS[maintenant.weekday()]}, "
                    f"{MOIS_ANGLAIS[maintenant.month - 1]} {maintenant.day}, "
                    f"{maintenant.year}."
                )

        elif self.commande_demande_date(commande) or "what is the date" in commande_normalisee:
            date = datetime.now().strftime("%d/%m/%Y")
            self.parler(
                f"Nous sommes le {date}" if self.langue == "fr" else f"The date is {date}"
            )

        elif any(mot in commande_normalisee for mot in ["image", "photo", "picture", "show me"]):
            recherche = self.nettoyer_commande(
                commande,
                [
                    "cherche", "recherche", "image", "photo", "montre", "de", "d'",
                    "search", "look up", "picture", "show me", "of", "a", "an",
                ],
            )
            self.chercher_image(recherche)

        elif any(mot in commande_normalisee for mot in ["cherche", "recherche", "search", "look up"]):
            recherche = self.nettoyer_commande(
                commande,
                ["cherche", "recherche", "search", "look up"],
            )
            self.chercher_google(recherche)

        elif any(
            expression in commande_normalisee
            for expression in ["explique", "c est quoi", "qui est", "explain", "what is", "who is"]
        ):
            question = self.nettoyer_commande(
                commande,
                ["explique", "c'est quoi", "qui est", "explain", "what is", "who is"],
            )
            self.repondre_question(question)

        elif any(mot in commande_normalisee for mot in ["stop", "arrete", "quit"]):
            self.parler(
                "D'accord, je m'arrete." if self.langue == "fr" else "Okay, I will stop listening."
            )
            return False

        else:
            self.repondre_question(commande)

        self.changer_statut("Pret - Ctrl+B pour parler")
        return True

    def repondre_question(self, question):
        if not question:
            self.parler("Pose-moi ta question.")
            return

        self.parler("Je reflechis avec l'IA locale.")
        reponse_ia = self.demander_ollama(question)

        if reponse_ia:
            self.parler(reponse_ia)
            return

        self.parler("Ollama n'est pas disponible. J'essaie avec Wikipedia.")
        trouve = self.chercher_wikipedia(question)

        if not trouve:
            self.parler("Je n'ai pas trouve de reponse directe. J'ouvre Google.")
            self.chercher_google(question)

    def chercher_google(self, recherche):
        if not recherche:
            self.parler("Dis-moi ce que tu veux chercher.")
            return

        self.parler(f"Je cherche {recherche} sur Google.")
        webbrowser.open(f"https://www.google.com/search?q={recherche}")

    def chercher_image(self, recherche):
        if not recherche:
            self.parler("Dis-moi quelle image tu veux voir.")
            return

        self.parler(f"Je cherche une image de {recherche}.")
        image_trouvee = self.afficher_image_wikipedia(recherche)

        if not image_trouvee:
            self.parler("Je n'ai pas trouve d'image directe. J'ouvre Google Images.")
            webbrowser.open(f"https://www.google.com/search?tbm=isch&q={recherche}")

    def afficher_image_wikipedia(self, recherche):
        if Image is None:
            self.actions_interface.put(
                ("message", "BF", "Installe Pillow pour afficher les images dans la fenetre.")
            )
            return False

        try:
            resultats = wikipedia.search(recherche, results=1)

            if not resultats:
                return False

            page = wikipedia.page(resultats[0], auto_suggest=False)
            extensions = (".jpg", ".jpeg", ".png", ".webp")
            images = [
                image_url
                for image_url in page.images
                if image_url.lower().split("?")[0].endswith(extensions)
            ]

            if not images:
                return False

            reponse = requests.get(
                images[0],
                headers={"User-Agent": "BF Assistant Vocal"},
                timeout=15,
            )
            reponse.raise_for_status()
            self.actions_interface.put(("image", reponse.content))
            return True

        except Exception:
            return False

    def chercher_wikipedia(self, question):
        if not question:
            self.parler("Dis-moi ce que tu veux que j'explique.")
            return False

        try:
            resultat = wikipedia.summary(question, sentences=3)
            self.parler(resultat)
            return True

        except wikipedia.exceptions.DisambiguationError:
            self.parler("J'ai trouve plusieurs resultats. Essaie d'etre plus precis.")
            return False

        except wikipedia.exceptions.PageError:
            self.parler("Je n'ai pas trouve de reponse precise sur Wikipedia.")
            return False

    def demander_ollama(self, question):
        try:
            langue_reponse = "francais" if self.langue == "fr" else "anglais"
            reponse = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODELE_OLLAMA,
                    "prompt": (
                        "Tu es BF, un assistant vocal personnel. "
                        f"Reponds en {langue_reponse}, clairement, avec un style naturel. "
                        "Si la question demande une explication, donne une reponse detaillee mais facile a comprendre.\n"
                        f"Question: {question}"
                    ),
                    "stream": False,
                },
                timeout=60,
            )
            reponse.raise_for_status()
            return reponse.json()["response"].strip()

        except requests.RequestException:
            return ""


def gerer_exception_non_capturee(type_exception, valeur, traceback_):
    journal.critical(
        "Exception non capturee, BF va se fermer :",
        exc_info=(type_exception, valeur, traceback_),
    )


if __name__ == "__main__":
    sys.excepthook = gerer_exception_non_capturee
    journal.info("Demarrage de BF (frozen=%s)", getattr(sys, "frozen", False))

    verrou = InstanceUnique()
    if verrou.deja_lance():
        journal.info("BF est deja en cours d'execution, arret de cette instance.")
        sys.exit(0)

    application = QApplication(sys.argv)
    application.setApplicationName("BF")
    racine = FenetreBF()
    app = AssistantBF(racine)
    racine.show()
    sys.exit(application.exec())