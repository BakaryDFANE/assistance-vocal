from __future__ import annotations

from pathlib import Path

from bf.tools.base import ResultatOutil


def chemin_autorise(cible: Path, racines: list[str]) -> bool:
    if not racines:
        return False
    resolu = cible.expanduser().resolve()
    for racine in racines:
        try:
            resolu.relative_to(Path(racine).expanduser().resolve())
            return True
        except ValueError:
            continue
    return False


def lister(cible: Path) -> ResultatOutil:
    if not cible.exists():
        return ResultatOutil(False, "Chemin introuvable.", erreur="missing")
    if cible.is_file():
        return ResultatOutil(True, str(cible), {"fichiers": [cible.name]})
    noms = [item.name for item in cible.iterdir()]
    return ResultatOutil(True, f"{len(noms)} éléments dans {cible.name}.", {"fichiers": noms[:200]})


def lire(cible: Path, limite: int = 80_000) -> ResultatOutil:
    if not cible.is_file():
        return ResultatOutil(False, "Ce n'est pas un fichier.", erreur="not_file")
    texte = cible.read_text(encoding="utf-8", errors="replace")
    return ResultatOutil(True, texte[:limite], {"tronque": len(texte) > limite})


def ecrire(cible: Path, contenu: str) -> ResultatOutil:
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_text(contenu, encoding="utf-8")
    return ResultatOutil(True, f"Fichier écrit: {cible.name}.")


def supprimer(cible: Path) -> ResultatOutil:
    if not cible.exists():
        return ResultatOutil(False, "Rien à supprimer.", erreur="missing")
    if cible.is_dir():
        return ResultatOutil(False, "La suppression de dossiers n'est pas autorisée ici.", erreur="dir")
    cible.unlink()
    return ResultatOutil(True, f"Fichier supprimé: {cible.name}.")
