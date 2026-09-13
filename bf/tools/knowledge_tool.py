from __future__ import annotations

import wikipedia

from bf.ai.ollama import ClientOllama
from bf.security.permissions import NiveauPermission
from bf.tools.base import Outil, ResultatOutil


def creer_outil_connaissance(client: ClientOllama) -> Outil:
    def executer(question: str, langue: str = "fr") -> ResultatOutil:
        if not question:
            return ResultatOutil(False, "Pose-moi ta question.", erreur="empty")
        wikipedia.set_lang(langue)
        reponse = client.demander(question, langue)
        if reponse:
            return ResultatOutil(True, reponse, {"source": "ollama"})
        try:
            resume = wikipedia.summary(question, sentences=3)
            return ResultatOutil(True, resume, {"source": "wikipedia"})
        except wikipedia.exceptions.DisambiguationError:
            return ResultatOutil(False, "Plusieurs résultats possibles. Sois plus précis.", erreur="disambiguation")
        except wikipedia.exceptions.PageError:
            return ResultatOutil(False, "Pas de réponse Wikipedia.", erreur="page")
        except Exception as erreur:  # noqa: BLE001
            return ResultatOutil(False, "Recherche impossible.", erreur=str(erreur))

    return Outil(
        nom="knowledge",
        description="Répond via l'IA locale Ollama, avec repli Wikipedia.",
        permission=NiveauPermission.SAFE,
        parametres={"question": "texte", "langue": "fr|en"},
        executer=executer,
    )
