"""Application logging: console + rotating file in ``<data>/logs``."""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from faceforge.helpers.paths import logs_dir

_CONFIGURED = False


def setup_logging(debug: bool = False) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    level = logging.DEBUG if debug else logging.INFO
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S")

    root = logging.getLogger("faceforge")
    root.setLevel(level)
    root.propagate = False

    if sys.stderr is not None:  # None in windowed (no-console) builds
        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(fmt)
        root.addHandler(console)

    try:
        file_handler = RotatingFileHandler(
            logs_dir() / "faceforge.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    except OSError:
        root.warning("File logging disabled (logs folder is not writable).")


def get_logger(name: str) -> logging.Logger:
    if not name.startswith("faceforge"):
        name = f"faceforge.{name}"
    return logging.getLogger(name)
