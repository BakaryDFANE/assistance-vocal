import subprocess
import sys
from pathlib import Path


DOSSIER_PROJET = Path(__file__).resolve().parent
ASSISTANT = DOSSIER_PROJET / "assistant_bf.py"

processus_bf = None


def ouvrir_bf():
    global processus_bf

    if processus_bf is not None and processus_bf.poll() is None:
        print("BF est deja ouvert.")
        return

    print("Ouverture de BF...")
    processus_bf = subprocess.Popen([sys.executable, str(ASSISTANT)])


if __name__ == "__main__":
    print("Lanceur BF actif.")
    print("Ouvre BF au lancement du script.")
    ouvrir_bf()
    input("Appuie sur Entrée pour fermer ce lanceur.\n")
