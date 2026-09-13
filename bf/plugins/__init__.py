"""Point d'extension: déposer un module exposant `enregistrer(registre)`."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from bf.core.logging import configurer_logging
from bf.core.paths import racine_application
from bf.tools.registry import RegistreOutils

journal = configurer_logging()


def charger_plugins(registre: RegistreOutils) -> None:
    dossier = racine_application() / "plugins"
    if not dossier.exists():
        return
    for info in pkgutil.iter_modules([str(dossier)]):
        try:
            module = importlib.import_module(f"plugins.{info.name}")
            if hasattr(module, "enregistrer"):
                module.enregistrer(registre)
                journal.info("Plugin chargé: %s", info.name)
        except Exception:
            journal.exception("Plugin ignoré: %s", info.name)


def dossier_plugins() -> Path:
    return racine_application() / "plugins"
