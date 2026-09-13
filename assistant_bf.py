"""Point d'entrée historique (scripts .bat, PyInstaller). Délègue au paquet `bf`."""

from bf.app.runtime_env import preparer_environnement

preparer_environnement()

from bf.app.bootstrap import main

if __name__ == "__main__":
    raise SystemExit(main())
