"""Render the app icon to packaging/build/icon.png (PyInstaller converts it to
.ico / .icns with Pillow)."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtGui import QGuiApplication  # noqa: E402

app = QGuiApplication(sys.argv)
from faceforge.ui.icons import app_icon_image  # noqa: E402

out = ROOT / "packaging" / "build"
out.mkdir(parents=True, exist_ok=True)
app_icon_image(1024).save(str(out / "icon.png"))
print(out / "icon.png")
