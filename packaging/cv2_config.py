# Replacement for cv2/config-3.py inside frozen builds.
#
# OpenCV's loader derives its search path from realpath(cv2/__init__.py). In a
# macOS .app, PyInstaller moves the .py files to Contents/Resources (symlinked
# from Contents/Frameworks) while the native extension stays in Frameworks.
# The loader then searches the wrong folder, and because Frameworks (which
# holds the cv2 *package*) is sys.path[0], re-imports the package and
# recurses. Point it at the folder holding the extension and make the loader
# put that folder first on sys.path.
import os
import sys

_frozen_cv2 = os.path.join(getattr(sys, "_MEIPASS", ""), "cv2")
if getattr(sys, "frozen", False) and os.path.isdir(_frozen_cv2):
    sys.OpenCV_REPLACE_SYS_PATH_0 = True
    PYTHON_EXTENSIONS_PATHS = [_frozen_cv2] + PYTHON_EXTENSIONS_PATHS  # noqa: F821
else:
    PYTHON_EXTENSIONS_PATHS = [LOADER_DIR] + PYTHON_EXTENSIONS_PATHS  # noqa: F821
