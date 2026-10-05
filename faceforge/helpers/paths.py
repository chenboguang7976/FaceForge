"""Filesystem locations that work from source, from a PyInstaller bundle,
and on Windows, macOS and Linux.

Layout
------
- ``resource_dir()`` — read-only files shipped with the app (QSS, icons).
- ``data_dir()``     — writable per-user data: settings, logs, temp, models.

From source, data lives in the repository root, as it did before. A frozen
Windows/Linux build is "portable": it writes next to the executable when that
folder is writable. A macOS .app bundle (or an install into a read-only
location) falls back to the per-user application-data folder.
Set ``FACEFORGE_HOME`` to force a location.
"""
from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

APP_NAME = "FaceForge"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_dir() -> Path:
    """Directory containing the ``faceforge`` package resources."""
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "faceforge"
    return Path(__file__).resolve().parent.parent


def _user_data_root() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / APP_NAME


def _is_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


@lru_cache(maxsize=1)
def data_dir() -> Path:
    override = os.environ.get("FACEFORGE_HOME")
    if override:
        path = Path(override).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path

    if not is_frozen():
        return Path(__file__).resolve().parent.parent.parent

    exe_dir = Path(sys.executable).resolve().parent
    if sys.platform != "darwin" and _is_writable(exe_dir):
        return exe_dir

    path = _user_data_root()
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_models_dir() -> Path:
    return data_dir() / "models"


def logs_dir() -> Path:
    path = data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def temp_dir() -> Path:
    path = data_dir() / "temp"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_output_dir() -> Path:
    return data_dir() / "output"


def settings_file() -> Path:
    return data_dir() / "settings.json"
