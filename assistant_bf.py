import io
import queue
import re
import sys
import threading
import tkinter as tk
import unicodedata
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import scrolledtext

import pyttsx3
import requests
import speech_recognition as sr
import wikipedia

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

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
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

wikipedia.set_lang("fr")


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
        self.fenetre.title("BF - Assistant vocal")
        self.fenetre.geometry("900x600")
        self.fenetre.minsize(750, 500)

        self.moteur = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        self.actions_interface = queue.Queue()
        self.ecoute_active = False
        self.thread_ecoute = None
        self.image_actuelle = None
        self.icone_barre_systeme = None
        self.thread_barre_systeme = None
        self.application_en_fermeture = False

        self.choisir_voix_masculine()
        self.creer_interface()
        self.fenetre.protocol("WM_DELETE_WINDOW", self.masquer_fenetre)
        self.fenetre.bind("<Control-b>", self.raccourci_ctrl_b)
        self.fenetre.bind("<Control-B>", self.raccourci_ctrl_b)
        self.traiter_actions_interface()
        self.creer_icone_barre_systeme()
        self.parler("BF est lance. Dis BF pour me parler.")
        self.fenetre.after(500, self.demarrer_automatiquement)

    def demarrer_automatiquement(self):
        if DEMARRER_EN_ARRIERE_PLAN:
            self.fenetre.withdraw()

        if not self.ecoute_active:
            self.basculer_ecoute()

    def creer_interface(self):
        self.fenetre.columnconfigure(0, weight=2)
        self.fenetre.columnconfigure(1, weight=1)
        self.fenetre.rowconfigure(1, weight=1)

        titre = tk.Label(
            self.fenetre,
            text="BF - Assistant vocal",
            font=("Segoe UI", 20, "bold"),
            bg="#101820",
            fg="white",
            pady=12,
        )
        titre.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.conversation = scrolledtext.ScrolledText(
            self.fenetre,
            font=("Segoe UI", 11),
            wrap=tk.WORD,
            state="disabled",
        )
        self.conversation.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)

        panneau_image = tk.Frame(self.fenetre, bg="#f2f2f2")
        panneau_image.grid(row=1, column=1, sticky="nsew", padx=(0, 12), pady=12)
        panneau_image.rowconfigure(0, weight=1)
        panneau_image.columnconfigure(0, weight=1)

        self.image_label = tk.Label(
            panneau_image,
            text="Les images apparaitront ici",
            font=("Segoe UI", 12),
            bg="#f2f2f2",
            fg="#333333",
            wraplength=250,
        )
        self.image_label.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        barre_bas = tk.Frame(self.fenetre)
        barre_bas.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))
        barre_bas.columnconfigure(0, weight=1)

        self.champ_texte = tk.Entry(barre_bas, font=("Segoe UI", 12))
        self.champ_texte.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.champ_texte.bind("<Return>", self.envoyer_message_texte)

        bouton_envoyer = tk.Button(
            barre_bas,
            text="Envoyer",
            command=self.envoyer_message_texte,
            font=("Segoe UI", 11),
        )
        bouton_envoyer.grid(row=0, column=1, padx=(0, 8))

        self.bouton_ecoute = tk.Button(
            barre_bas,
            text="Demarrer l'ecoute",
            command=self.basculer_ecoute,
            font=("Segoe UI", 11),
        )
        self.bouton_ecoute.grid(row=0, column=2)

        self.statut = tk.Label(
            self.fenetre,
            text="Pret - Ctrl+B pour parler",
            anchor="w",
            font=("Segoe UI", 10),
            bg="#e8e8e8",
        )
        self.statut.grid(row=3, column=0, columnspan=2, sticky="ew")

    def choisir_voix_masculine(self):
        voix_disponibles = self.moteur.getProperty("voices")
        mots_voix_masculine = ["david", "mark", "male", "homme", "paul"]

        for voix in voix_disponibles:
            nom_voix = f"{voix.name} {voix.id}".lower()

            for mot in mots_voix_masculine:
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
            self.bouton_ecoute.config(text="Demarrer l'ecoute")
            self.statut.config(text="Ecoute arretee - Ctrl+B pour parler")
            return

        self.ecoute_active = True
        self.bouton_ecoute.config(text="Arreter l'ecoute")
        self.thread_ecoute = threading.Thread(target=self.boucle_ecoute, daemon=True)
        self.thread_ecoute.start()

    def ajouter_message(self, auteur, texte):
        self.afficher_fenetre()
        self.conversation.config(state="normal")
        self.conversation.insert(tk.END, f"{auteur} : {texte}\n\n")
        self.conversation.config(state="disabled")
        self.conversation.see(tk.END)

    def afficher_fenetre(self):
        self.fenetre.deiconify()
        self.fenetre.lift()
        self.fenetre.attributes("-topmost", True)
        self.fenetre.after(500, lambda: self.fenetre.attributes("-topmost", False))

    def parler(self, texte):
        self.actions_interface.put(("message", "BF", texte))
        print("BF :", texte)
        self.moteur.say(texte)
        self.moteur.runAndWait()

    def changer_statut(self, texte):
        self.actions_interface.put(("statut", texte))

    def traiter_actions_interface(self):
        while not self.actions_interface.empty():
            action = self.actions_interface.get()

            if action[0] == "message":
                self.ajouter_message(action[1], action[2])

            elif action[0] == "statut":
                self.statut.config(text=action[1])

            elif action[0] == "afficher":
                self.afficher_fenetre()

            elif action[0] == "bouton":
                self.bouton_ecoute.config(text=action[1])

            elif action[0] == "image":
                self.afficher_image(action[1])

            elif action[0] == "basculer_ecoute":
                self.basculer_ecoute()

            elif action[0] == "quitter":
                self.quitter_application()

        if not self.application_en_fermeture:
            self.fenetre.after(100, self.traiter_actions_interface)

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
        self.fenetre.withdraw()

    def quitter_depuis_barre_systeme(self, icon=None, item=None):
        self.actions_interface.put(("quitter",))

    def quitter_application(self):
        self.application_en_fermeture = True
        self.ecoute_active = False

        if self.icone_barre_systeme is not None:
            self.icone_barre_systeme.stop()

        self.fenetre.destroy()

    def afficher_image(self, image_bytes):
        if Image is None or ImageTk is None:
            self.image_label.config(
                text="Installe Pillow pour afficher les images:\npip install pillow",
                image="",
            )
            return

        image = Image.open(io.BytesIO(image_bytes))
        image.thumbnail((300, 380))
        self.image_actuelle = ImageTk.PhotoImage(image)
        self.image_label.config(image=self.image_actuelle, text="")

    def envoyer_message_texte(self, event=None):
        commande = self.champ_texte.get().strip().lower()
        self.champ_texte.delete(0, tk.END)

        if not commande:
            return

        self.ajouter_message("Vous", commande)
        threading.Thread(target=self.executer_commande, args=(commande,), daemon=True).start()

    def ecouter(self):
        with sr.Microphone() as source:
            self.changer_statut("J'ecoute...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = self.recognizer.listen(source, phrase_time_limit=7)

        try:
            texte = self.recognizer.recognize_google(audio, language="fr-FR")
            texte = texte.lower()
            print("Vous :", texte)
            return texte

        except sr.UnknownValueError:
            self.changer_statut("Je n'ai pas compris")
            return ""

        except sr.RequestError:
            self.parler("Je n'arrive pas a utiliser la reconnaissance vocale.")
            return ""

    def boucle_ecoute(self):
        self.changer_statut("Ecoute active")

        while self.ecoute_active:
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
                    continuer = self.executer_commande(commande)
                    self.arreter_si_termine(continuer)

            elif self.est_commande_directe(texte):
                self.actions_interface.put(("afficher",))
                self.actions_interface.put(("message", "Vous", texte))
                continuer = self.executer_commande(texte)
                self.arreter_si_termine(continuer)

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

        if self.commande_demande_heure(commande):
            heure = datetime.now().strftime("%H:%M")
            self.parler(f"Il est {heure}")

        elif self.commande_demande_jour(commande):
            maintenant = datetime.now()
            jour_semaine = JOURS[maintenant.weekday()]
            mois_annee = MOIS[maintenant.month - 1]
            self.parler(
                f"Nous sommes {jour_semaine} {maintenant.day} {mois_annee} {maintenant.year}."
            )

        elif self.commande_demande_date(commande):
            date = datetime.now().strftime("%d/%m/%Y")
            self.parler(f"Nous sommes le {date}")

        elif "image" in commande or "photo" in commande or "montre" in commande:
            recherche = self.nettoyer_commande(
                commande,
                ["cherche", "recherche", "image", "photo", "montre", "de", "d'"],
            )
            self.chercher_image(recherche)

        elif "cherche" in commande or "recherche" in commande:
            recherche = self.nettoyer_commande(commande, ["cherche", "recherche"])
            self.chercher_google(recherche)

        elif "explique" in commande or "c'est quoi" in commande or "qui est" in commande:
            question = self.nettoyer_commande(commande, ["explique", "c'est quoi", "qui est"])
            self.repondre_question(question)

        elif "stop" in commande or "arrete" in commande or "arrête" in commande:
            self.parler("D'accord, je m'arrete.")
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
        if Image is None or ImageTk is None:
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
            reponse = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODELE_OLLAMA,
                    "prompt": (
                        "Tu es BF, un assistant vocal personnel. "
                        "Reponds en francais, clairement, avec un style naturel. "
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


if __name__ == "__main__":
    racine = tk.Tk()
    app = AssistantBF(racine)
    racine.mainloop()
