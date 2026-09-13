from __future__ import annotations

from dataclasses import dataclass

from bf.core.text import normaliser_texte, retirer_motif


@dataclass
class Intention:
    nom: str
    outil: str
    arguments: dict
    confiance: float = 1.0


class RouteurIntentions:
    def interpreter(self, commande: str, langue: str = "fr") -> Intention:
        texte = normaliser_texte(commande)

        if any(mot in texte for mot in ["stop", "arrete", "quit", "quitte"]):
            return Intention("stop", "", {})

        if _contient(texte, ["quelle heure", "what time", "heure"]):
            if "date" not in texte and "jour" not in texte:
                return Intention("datetime", "datetime", {"sujet": "heure", "langue": langue})
        if _contient(texte, ["quel jour", "what day", "aujourd hui"]):
            return Intention("datetime", "datetime", {"sujet": "jour", "langue": langue})
        if _contient(texte, ["quelle date", "what is the date", "on est le combien"]):
            return Intention("datetime", "datetime", {"sujet": "date", "langue": langue})

        if _contient(texte, ["image", "photo", "picture", "montre"]):
            recherche = retirer_motif(
                commande,
                ["cherche", "recherche", "image", "photo", "montre", "search", "picture", "show me"],
            )
            return Intention("image", "image_search", {"recherche": recherche})

        if _contient(texte, ["cherche", "recherche", "search", "look up", "navigateur"]):
            recherche = retirer_motif(commande, ["cherche", "recherche", "search", "look up", "ouvre", "open"])
            return Intention("search", "web_search", {"recherche": recherche})

        if _contient(texte, ["ouvre mon projet", "open my project", "structure du projet", "analyse mon projet"]):
            action = "ouvrir" if "ouvre" in texte or "open" in texte else "structure"
            return Intention("project", "project", {"action": action})

        if _contient(texte, ["vs code", "vscode", "visual studio code"]):
            return Intention("app", "application", {"application": "vscode"})
        if _contient(texte, ["ouvre le navigateur", "open browser"]):
            return Intention("app", "application", {"application": "navigateur"})
        if _contient(texte, ["ouvre", "open", "lance"]):
            reste = retirer_motif(commande, ["ouvre", "open", "lance", "launch", "s il te plait"])
            if reste:
                return Intention("app", "application", {"application": reste})

        if _contient(texte, ["oui", "yes", "confirme"]):
            return Intention("confirm_yes", "", {})
        if _contient(texte, ["non", "no", "annule"]):
            return Intention("confirm_no", "", {})

        return Intention("knowledge", "knowledge", {"question": commande, "langue": langue})


def _contient(texte: str, motifs: list[str]) -> bool:
    return any(motif in texte for motif in motifs)
