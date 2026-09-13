from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from bf.config.settings import ParametresBF
from bf.core.paths import chemin_ressource
from bf.core.state import EtatBF
from bf.ui.settings_page import PageParametres


class FenetrePrincipale(QMainWindow):
    fermeture_demandee = Signal()
    message_texte = Signal(str)
    ecoute_demandee = Signal()
    parametres_enregistres = Signal(object)
    memoire_effacee = Signal()

    def __init__(self, parametres: ParametresBF) -> None:
        super().__init__()
        self.parametres = parametres
        self.setWindowTitle("BF — Copilote")
        self.resize(1180, 740)
        self.setMinimumSize(900, 600)
        self.visualiseur_pret = False
        self._etat = EtatBF.IDLE
        self._construire()

    def closeEvent(self, event) -> None:  # noqa: N802
        self.fermeture_demandee.emit()
        event.ignore()

    def _construire(self) -> None:
        action = QAction("Activer l'écoute", self)
        action.setShortcut(self.parametres.raccourci_ecoute)
        action.triggered.connect(self.ecoute_demandee.emit)
        self.addAction(action)

        racine = QWidget()
        layout = QHBoxLayout(racine)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        nav = QFrame()
        nav.setObjectName("nav")
        nav_l = QVBoxLayout(nav)
        titre = QLabel("BF")
        titre.setObjectName("titre")
        sous = QLabel("Copilote")
        sous.setObjectName("sousTitre")
        nav_l.addWidget(titre)
        nav_l.addWidget(sous)
        self.menu = QListWidget()
        self.menu.addItems(["Copilote", "Paramètres", "Journal"])
        self.menu.setCurrentRow(0)
        self.menu.currentRowChanged.connect(self._changer_page)
        nav_l.addWidget(self.menu, 1)
        self.pastille = QLabel("●  En veille")
        self.pastille.setObjectName("pastille")
        nav_l.addWidget(self.pastille)
        layout.addWidget(nav, 0)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._page_copilote())
        self.page_parametres = PageParametres(self.parametres)
        self.page_parametres.sauvegarde.connect(self.parametres_enregistres.emit)
        self.page_parametres.memoire_effacee.connect(self.memoire_effacee.emit)
        self.pages.addWidget(self.page_parametres)
        self.journal_ui = QTextEdit()
        self.journal_ui.setReadOnly(True)
        self.journal_ui.setPlaceholderText("Journal des actions…")
        self.pages.addWidget(self.journal_ui)
        layout.addWidget(self.pages, 1)

        self.setCentralWidget(racine)
        self.setStyleSheet(_STYLES)

    def _page_copilote(self) -> QWidget:
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(0, 0, 0, 0)
        zone = QHBoxLayout()
        gauche = QVBoxLayout()
        self.tache = QLabel("En attente du mot d'activation.")
        self.tache.setObjectName("tache")
        self.etapes = QLabel("")
        self.etapes.setObjectName("etapes")
        self.etapes.setWordWrap(True)
        self.conversation = QTextEdit()
        self.conversation.setReadOnly(True)
        gauche.addWidget(self.tache)
        gauche.addWidget(self.etapes)
        gauche.addWidget(self.conversation, 1)
        zone.addLayout(gauche, 1)

        self.visualiseur = QWebEngineView()
        self.visualiseur.setMinimumWidth(420)
        self.visualiseur.loadFinished.connect(self._visualiseur_charge)
        html = chemin_ressource("assets/visualiseur_bf.html")
        self.visualiseur.setUrl(QUrl.fromLocalFile(str(html.resolve())))
        zone.addWidget(self.visualiseur, 2)
        col.addLayout(zone, 1)

        barre = QHBoxLayout()
        self.champ = QLineEdit()
        self.champ.setPlaceholderText("Écris à BF…")
        self.champ.returnPressed.connect(self._envoyer)
        envoyer = QPushButton("Envoyer")
        envoyer.clicked.connect(self._envoyer)
        self.bouton_ecoute = QPushButton("Écoute")
        self.bouton_ecoute.clicked.connect(self.ecoute_demandee.emit)
        barre.addWidget(self.champ, 1)
        barre.addWidget(envoyer)
        barre.addWidget(self.bouton_ecoute)
        col.addLayout(barre)
        return page

    def _changer_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)

    def _envoyer(self) -> None:
        texte = self.champ.text().strip()
        self.champ.clear()
        if texte:
            self.message_texte.emit(texte)

    def _visualiseur_charge(self, ok: bool) -> None:
        self.visualiseur_pret = bool(ok)
        if ok:
            self.appliquer_etat(self._etat)

    def appliquer_etat(self, etat: EtatBF, tache: str = "", etapes: list[str] | None = None) -> None:
        self._etat = etat
        self.pastille.setText(f"●  {etat.libelle}")
        if tache:
            self.tache.setText(tache)
        if etapes is not None:
            lignes = [f"{i + 1}. {titre}" for i, titre in enumerate(etapes)]
            self.etapes.setText("\n".join(lignes))
        if self.visualiseur_pret:
            self.visualiseur.page().runJavaScript(f"window.bfSetState({etat.etat_visuel!r});")

    def ajouter_message(self, auteur: str, texte: str) -> None:
        self.conversation.append(f"<b>{auteur}</b> : {texte}")
        barre = self.conversation.verticalScrollBar()
        barre.setValue(barre.maximum())

    def definir_journal(self, lignes: list[str]) -> None:
        self.journal_ui.setPlainText("\n".join(lignes))


_STYLES = """
QMainWindow, QWidget { background: #070b14; color: #e8f4ff; font-family: 'Segoe UI'; }
#nav { background: rgba(12, 18, 36, 0.92); border: 1px solid #1c2c4a; border-radius: 16px; min-width: 168px; padding: 8px; }
#titre { color: #d4b3ff; font-size: 28px; font-weight: 700; letter-spacing: 4px; }
#sousTitre { color: #6f8eae; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; }
#pastille { color: #7cf0ff; padding: 8px; }
#tache { color: #c9b6ff; font-size: 15px; }
#etapes { color: #7f9bb8; font-size: 12px; }
QListWidget { background: transparent; border: 0; color: #9fb6cc; }
QListWidget::item:selected { background: #1b2a4d; color: #7cf0ff; border-radius: 8px; }
QTextEdit, QLineEdit, QSpinBox, QComboBox, QPlainTextEdit {
    background: #10182a; border: 1px solid #243552; border-radius: 10px;
    padding: 10px; color: #e8f4ff;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5b4dff, stop:1 #c44dff);
    border: 0; border-radius: 8px; padding: 10px 16px; color: white; font-weight: 600;
}
QPushButton:hover { background: #7a6bff; }
QCheckBox { color: #c5d7ea; spacing: 8px; }
"""
