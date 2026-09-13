from __future__ import annotations

import sys

from bf.app.runtime_env import preparer_environnement
from bf.config.settings import charger_parametres
from bf.core.logging import configurer_logging
from bf.core.singleton import InstanceUnique


def main(argv: list[str] | None = None) -> int:
    del argv
    preparer_environnement()
    parametres = charger_parametres()
    journal = configurer_logging(parametres.niveau_logs)
    journal.info("Demarrage de BF (frozen=%s)", getattr(sys, "frozen", False))

    verrou = InstanceUnique()
    if verrou.deja_lance():
        journal.info("BF est deja en cours d'execution, arret de cette instance.")
        return 0

    def _hook(type_exception, valeur, traceback_):
        journal.critical(
            "Exception non capturee, BF va se fermer :",
            exc_info=(type_exception, valeur, traceback_),
        )

    sys.excepthook = _hook

    from PySide6.QtWidgets import QApplication
    from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: F401 — init WebEngine

    from bf.app.runtime import RuntimeBF

    application = QApplication(sys.argv)
    application.setApplicationName("BF")
    application.setQuitOnLastWindowClosed(False)
    RuntimeBF(application, parametres)
    return application.exec()
