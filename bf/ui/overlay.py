from __future__ import annotations

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView

from bf.core.paths import chemin_ressource
from bf.core.state import EtatBF


class OverlayBF(QWidget):
    """Fenêtre flottante compacte, visible surtout après le wake word."""

    fermeture_demandee = Signal()

    def __init__(self) -> None:
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("BF")
        self.resize(380, 460)
        self.visualiseur_pret = False
        self._etat = EtatBF.IDLE

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.statut = QLabel("BF  ·  En veille")
        self.statut.setAlignment(Qt.AlignCenter)
        self.statut.setStyleSheet(
            "color:#d8c6ff; letter-spacing:3px; font-size:11px; "
            "background:rgba(8,10,22,180); border-radius:10px; padding:8px;"
        )
        self.visualiseur = QWebEngineView()
        self.visualiseur.setStyleSheet("background: transparent;")
        self.visualiseur.loadFinished.connect(self._charge)
        html = chemin_ressource("assets/visualiseur_bf.html")
        self.visualiseur.setUrl(QUrl.fromLocalFile(str(html.resolve())))
        self.detail = QLabel("")
        self.detail.setWordWrap(True)
        self.detail.setStyleSheet("color:#8eb0c8; font-size:11px; padding:6px 10px;")
        layout.addWidget(self.statut)
        layout.addWidget(self.visualiseur, 1)
        layout.addWidget(self.detail)

    def _charge(self, ok: bool) -> None:
        self.visualiseur_pret = bool(ok)
        if ok:
            self.appliquer_etat(self._etat)

    def placer_coin(self, ecran) -> None:
        geo = ecran.availableGeometry()
        self.move(geo.right() - self.width() - 28, geo.bottom() - self.height() - 48)

    def appliquer_etat(self, etat: EtatBF, tache: str = "", etapes: list[str] | None = None) -> None:
        self._etat = etat
        self.statut.setText(f"BF  ·  {etat.libelle}")
        if tache or etapes:
            lignes = [tache] if tache else []
            if etapes:
                lignes.extend(f"{i + 1}. {item}" for i, item in enumerate(etapes))
            self.detail.setText("\n".join(lignes))
        if self.visualiseur_pret:
            self.visualiseur.page().runJavaScript(f"window.bfSetState({etat.etat_visuel!r});")
