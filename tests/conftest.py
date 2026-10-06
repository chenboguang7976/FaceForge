import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Every test gets its own data folder (settings, temp, logs)."""
    monkeypatch.setenv("FACEFORGE_HOME", str(tmp_path / "home"))
    from faceforge.helpers import paths

    paths.data_dir.cache_clear()
    yield tmp_path / "home"
    paths.data_dir.cache_clear()


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])
