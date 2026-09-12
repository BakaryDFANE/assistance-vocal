from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


RACINE_PROJET = Path(__file__).resolve().parents[1]
DOSSIER_ASSETS = RACINE_PROJET / "assets"
FICHIER_ICONE = DOSSIER_ASSETS / "bf.ico"
FICHIER_LOGO = DOSSIER_ASSETS / "bf.png"


def charger_police(taille):
    polices = [
        "C:/Windows/Fonts/timesbd.ttf",
        "C:/Windows/Fonts/timesbi.ttf",
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/georgiab.ttf",
    ]

    for police in polices:
        chemin = Path(police)
        if chemin.exists():
            return ImageFont.truetype(str(chemin), taille)

    return ImageFont.load_default()


def dessiner_monogramme(taille):
    image = Image.new("RGBA", (taille, taille), (0, 0, 0, 0))
    dessin = ImageDraw.Draw(image)
    marge = taille * 0.08

    dessin.rounded_rectangle(
        (marge, marge, taille - marge, taille - marge),
        radius=taille * 0.18,
        fill="#101820",
    )
    dessin.rounded_rectangle(
        (marge * 1.45, marge * 1.45, taille - marge * 1.45, taille - marge * 1.45),
        radius=taille * 0.14,
        outline="#d8b15f",
        width=max(2, taille // 35),
    )

    police_b = charger_police(int(taille * 0.82))
    police_f = charger_police(int(taille * 0.63))

    texte_b = "B"
    boite_b = dessin.textbbox((0, 0), texte_b, font=police_b)
    largeur_b = boite_b[2] - boite_b[0]
    hauteur_b = boite_b[3] - boite_b[1]
    x_b = taille * 0.18
    y_b = (taille - hauteur_b) / 2 - taille * 0.07

    texte_f = "F"
    boite_f = dessin.textbbox((0, 0), texte_f, font=police_f)
    largeur_f = boite_f[2] - boite_f[0]
    hauteur_f = boite_f[3] - boite_f[1]
    x_f = x_b + largeur_b * 0.43
    y_f = (taille - hauteur_f) / 2 - taille * 0.01

    dessin.text((x_b + 3, y_b + 4), texte_b, font=police_b, fill=(0, 0, 0, 120))
    dessin.text((x_b, y_b), texte_b, font=police_b, fill="#f7f1df")

    # Le F est incruste dans la partie droite du B, avec un fin contour sombre.
    contour = max(1, taille // 70)
    for dx, dy in [(-contour, 0), (contour, 0), (0, -contour), (0, contour)]:
        dessin.text((x_f + dx, y_f + dy), texte_f, font=police_f, fill="#101820")

    dessin.text((x_f, y_f), texte_f, font=police_f, fill="#d8b15f")
    dessin.line(
        (x_f + largeur_f * 0.03, y_f + hauteur_f * 0.53, x_f + largeur_f * 0.78, y_f + hauteur_f * 0.53),
        fill="#f7f1df",
        width=max(1, taille // 80),
    )
    return image


def main():
    DOSSIER_ASSETS.mkdir(exist_ok=True)
    tailles = [16, 24, 32, 48, 64, 128, 256]
    images = [dessiner_monogramme(taille) for taille in tailles]
    images[-1].save(FICHIER_LOGO)
    images[-1].save(FICHIER_ICONE, sizes=[(taille, taille) for taille in tailles])
    print(f"Logo cree: {FICHIER_LOGO}")
    print(f"Icone creee: {FICHIER_ICONE}")


if __name__ == "__main__":
    main()
