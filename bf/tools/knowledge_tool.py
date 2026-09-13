from __future__ import annotations

import webbrowser
from urllib.parse import quote_plus

import wikipedia

from bf.security.permissions import NiveauPermission
from bf.tools.base import Outil, ResultatOutil


def creer_outil_connaissance() -> Outil:
    def executer(question: str, langue: str = "fr") -> ResultatOutil:
        if not question:
            return ResultatOutil(False, "Pose-moi ta question.", erreur="empty")
        webbrowser.open(f"https://www.google.com/search?q={quote_plus(question)}")
        wikipedia.set_lang(langue)
        try:
            resume = wikipedia.summary(question, sentences=3)
            return ResultatOutil(True, resume, {"source": "google+wikipedia"})
        except wikipedia.exceptions.DisambiguationError:
            return ResultatOutil(
                True,
                f"Plusieurs résultats existent. J'ai ouvert Google pour « {question} ».",
                {"source": "google"},
            )
        except wikipedia.exceptions.PageError:
            return ResultatOutil(
                True,
                f"Je n'ai pas trouvé cette page dans Wikipedia. J'ai ouvert Google pour « {question} ».",
                {"source": "google"},
            )
        except Exception as erreur:  # noqa: BLE001
            return ResultatOutil(
                True,
                f"J'ai ouvert Google pour rechercher « {question} ». Lis les résultats affichés.",
                {"source": "google"},
            )

    return Outil(
        nom="knowledge",
        description="Recherche une réponse dans Wikipedia et ouvre Google pour compléter la recherche.",
        permission=NiveauPermission.SAFE,
        parametres={"question": "texte", "langue": "fr|en"},
        executer=executer,
    )
