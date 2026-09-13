from __future__ import annotations

import os
import sys
from pathlib import Path


def preparer_environnement() -> None:
    """Correctifs exe: stdout manquant et certificats SSL (certifi)."""
    if not getattr(sys, "frozen", False):
        return
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")
    try:
        cacert = Path(sys._MEIPASS) / "certifi" / "cacert.pem"  # type: ignore[attr-defined]
        if cacert.exists():
            os.environ.setdefault("SSL_CERT_FILE", str(cacert))
            os.environ.setdefault("REQUESTS_CA_BUNDLE", str(cacert))
    except Exception:
        pass
