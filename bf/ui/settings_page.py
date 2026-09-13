from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from bf.config.settings import ParametresBF


class PageParametres(QWidget):
    sauvegarde = Signal(object)
    memoire_effacee = Signal()

    def __init__(self, parametres: ParametresBF) -> None:
        super().__init__()
        self.parametres = parametres
        form = QFormLayout()
        self.mot = QLineEdit(parametres.mot_activation)
        self.alias = QLineEdit(", ".join(parametres.alias_activation))
        self.micro = QSpinBox()
        self.micro.setMinimum(-1)
        self.micro.setMaximum(64)
        self.micro.setValue(-1 if parametres.microphone_index is None else parametres.microphone_index)
        self.debit = QSpinBox()
        self.debit.setRange(80, 300)
        self.debit.setValue(parametres.voix_debit)
        self.volume = QDoubleSpinBox()
        self.volume.setRange(0, 1)
        self.volume.setSingleStep(0.05)
        self.volume.setValue(parametres.voix_volume)
        self.raccourci = QLineEdit(parametres.raccourci_ecoute)
        self.autostart = QCheckBox("Démarrer avec Windows")
        self.autostart.setChecked(parametres.demarrer_avec_windows)
        self.arriere = QCheckBox("Démarrer en arrière-plan (overlay masqué)")
        self.arriere.setChecked(parametres.demarrer_en_arriere_plan)
        self.sans_wake = QCheckBox("Accepter des commandes sans mot d'activation")
        self.sans_wake.setChecked(parametres.commandes_sans_mot_activation)
        self.confirmer = QCheckBox("Demander confirmation pour les actions sensibles")
        self.confirmer.setChecked(parametres.confirmer_actions_sensibles)
        self.memoire = QCheckBox("Mémoire de contexte activée")
        self.memoire.setChecked(parametres.memoire_active)
        self.apparence = QComboBox()
        self.apparence.addItems(["cyber", "minimal"])
        self.apparence.setCurrentText(parametres.apparence)
        self.logs = QComboBox()
        self.logs.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.logs.setCurrentText(parametres.niveau_logs)
        self.outils = QLineEdit(", ".join(parametres.outils_actifs))
        self.racines = QLineEdit("; ".join(parametres.racines_autorisees))
        self.projet = QLineEdit(parametres.projet_actif)
        self.overlay_s = QDoubleSpinBox()
        self.overlay_s.setRange(2, 60)
        self.overlay_s.setValue(parametres.masquer_overlay_apres_secondes)

        form.addRow("Wake word", self.mot)
        form.addRow("Alias", self.alias)
        form.addRow("Index microphone (-1 = défaut)", self.micro)
        form.addRow("Débit voix", self.debit)
        form.addRow("Volume", self.volume)
        form.addRow("Raccourci (vide = désactivé)", self.raccourci)
        form.addRow(self.autostart)
        form.addRow(self.arriere)
        form.addRow(self.sans_wake)
        form.addRow(self.confirmer)
        form.addRow(self.memoire)
        form.addRow("Apparence", self.apparence)
        form.addRow("Logs", self.logs)
        form.addRow("Outils actifs", self.outils)
        form.addRow("Dossiers autorisés", self.racines)
        form.addRow("Projet actif", self.projet)
        form.addRow("Masquer overlay (s)", self.overlay_s)

        enregistrer = QPushButton("Enregistrer")
        enregistrer.clicked.connect(self._sauver)
        effacer = QPushButton("Effacer la mémoire")
        effacer.clicked.connect(self.memoire_effacee.emit)

        racine = QVBoxLayout(self)
        racine.addLayout(form)
        racine.addWidget(enregistrer)
        racine.addWidget(effacer)
        racine.addStretch()

    def _sauver(self) -> None:
        p = self.parametres
        p.mot_activation = self.mot.text().strip() or "bf"
        p.alias_activation = [a.strip() for a in self.alias.text().split(",") if a.strip()]
        p.microphone_index = None if self.micro.value() < 0 else self.micro.value()
        p.voix_debit = self.debit.value()
        p.voix_volume = self.volume.value()
        p.raccourci_ecoute = self.raccourci.text().strip()
        p.demarrer_avec_windows = self.autostart.isChecked()
        p.demarrer_en_arriere_plan = self.arriere.isChecked()
        p.commandes_sans_mot_activation = self.sans_wake.isChecked()
        p.confirmer_actions_sensibles = self.confirmer.isChecked()
        p.memoire_active = self.memoire.isChecked()
        p.apparence = self.apparence.currentText()
        p.niveau_logs = self.logs.currentText()
        p.outils_actifs = [o.strip() for o in self.outils.text().split(",") if o.strip()]
        p.racines_autorisees = [r.strip() for r in self.racines.text().split(";") if r.strip()]
        p.projet_actif = self.projet.text().strip()
        p.masquer_overlay_apres_secondes = self.overlay_s.value()
        self.sauvegarde.emit(p)
