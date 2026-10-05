# Replacement for cv2/config.py inside frozen builds.
#
# OpenCV's loader derives its search path from realpath(cv2/__init__.py). In a
# macOS .app, PyInstaller moves the .py files to Contents/Resources (symlinked
# from Contents/Frameworks) while the native extension stays in Frameworks, so
# the loader searches the wrong folder and recurses. Point it at the folder
# that actually holds the extension.
import os
import sys

_frozen_cv2 = os.path.join(getattr(sys, "_MEIPASS", ""), "cv2")
PYTHON_EXTENSIONS_PATHS = [
    _frozen_cv2 if getattr(sys, "frozen", False) and os.path.isdir(_frozen_cv2) else LOADER_DIR  # noqa: F821
] + PYTHON_EXTENSIONS_PATHS  # noqa: F821
