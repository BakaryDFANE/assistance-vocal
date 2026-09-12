import subprocess
import sys
from pathlib import Path

import keyboard


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


print("Lanceur BF actif.")
print("Appuie sur Ctrl+Shift+B pour ouvrir BF.")
print("Garde cette fenetre ouverte, ou mets ce lanceur au demarrage de Windows.")

keyboard.add_hotkey("ctrl+shift+b", ouvrir_bf)
keyboard.wait()
