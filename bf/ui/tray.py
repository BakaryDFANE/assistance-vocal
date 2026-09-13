from __future__ import annotations

import threading
from typing import Callable

from bf.core.logging import configurer_logging

journal = configurer_logging()

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None
    ImageDraw = None

try:
    import pystray
except ImportError:
    pystray = None


def creer_icone_image():
    if Image is None or ImageDraw is None:
        return None
    image = Image.new("RGBA", (256, 256), (7, 11, 20, 255))
    dessin = ImageDraw.Draw(image)
    dessin.ellipse((24, 24, 232, 232), fill="#5b4dff")
    dessin.ellipse((70, 70, 186, 186), fill="#7cf0ff")
    return image


class BarreSysteme:
    def __init__(
        self,
        ouvrir: Callable[[], None],
        ecoute: Callable[[], None],
        quitter: Callable[[], None],
    ) -> None:
        self.icone = None
        self.thread = None
        if pystray is None or Image is None:
            return
        menu = pystray.Menu(
            pystray.MenuItem("Ouvrir BF", lambda *_: ouvrir(), default=True),
            pystray.MenuItem("Écoute / veille", lambda *_: ecoute()),
            pystray.MenuItem("Quitter BF", lambda *_: quitter()),
        )
        image = creer_icone_image()
        self.icone = pystray.Icon("BF", image, "BF — Copilote", menu)
        self.thread = threading.Thread(target=self.icone.run, daemon=True)
        self.thread.start()

    def arreter(self) -> None:
        if self.icone is not None:
            try:
                self.icone.stop()
            except Exception:
                journal.exception("Arrêt de l'icône système.")
