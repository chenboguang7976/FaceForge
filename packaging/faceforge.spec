# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for all FaceForge builds.

Environment:
  FACEFORGE_EDITION   pro | lite      (default: pro)
  FACEFORGE_BACKEND   cuda | directml | cpu   (informational; the installed
                      onnxruntime package decides what gets bundled)

Run from the repository root:
  python packaging/make_icon.py
  pyinstaller packaging/faceforge.spec --noconfirm
"""
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

ROOT = Path(SPECPATH).resolve().parent
EDITION = os.environ.get("FACEFORGE_EDITION", "pro").lower()
NAME = "FaceForge Lite" if EDITION == "lite" else "FaceForge Pro"
BUILD = ROOT / "packaging" / "build"
BUILD.mkdir(parents=True, exist_ok=True)

# Bake the edition in via a runtime hook (source files stay untouched).
rthook = BUILD / f"rthook_edition_{EDITION}.py"
rthook.write_text(f"import os\nos.environ.setdefault('FACEFORGE_EDITION', '{EDITION}')\n", encoding="utf-8")

binaries = collect_dynamic_libs("onnxruntime")
datas = collect_data_files("imageio_ffmpeg", include_py_files=False)  # bundled ffmpeg binary
datas += collect_data_files("onnx", includes=["**/*.pyi"])  # keeps onnx's lazy imports happy

# CUDA/cuDNN from the nvidia-* wheels: place them next to the onnxruntime
# provider DLL so the loader finds them inside the frozen app.
try:
    import nvidia  # noqa: F401

    nvidia_root = Path(nvidia.__path__[0])
    patterns = ("*.dll",) if sys.platform == "win32" else ("*.so*",)
    for pattern in patterns:
        for lib in nvidia_root.rglob(pattern):
            binaries.append((str(lib), "onnxruntime/capi"))
except ImportError:
    pass

# Qt modules FaceForge never uses: keeps the bundle (and RAM use) smaller.
EXCLUDES = [
    "tkinter", "matplotlib", "torch", "torchvision", "IPython", "pytest",
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.QtQuick", "PySide6.QtQuick3D", "PySide6.QtQml",
    "PySide6.QtMultimedia", "PySide6.QtCharts", "PySide6.QtDataVisualization", "PySide6.QtPdf",
    "PySide6.QtBluetooth", "PySide6.QtNfc", "PySide6.QtPositioning", "PySide6.QtSensors",
    "PySide6.QtSerialPort", "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtDesigner",
]

icon = str(BUILD / "icon.png") if (BUILD / "icon.png").exists() else None

a = Analysis(
    [str(ROOT / "run.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=["faceforge.ui.translations", "PySide6.QtSvg"],
    runtime_hooks=[str(rthook)],
    excludes=EXCLUDES,
    noarchive=False,
)
# Swap in our OpenCV loader config (see packaging/cv2_config.py).
def _is_cv2_config(entry):
    return entry[0].replace("\\", "/") == "cv2/config.py"


a.datas = [e for e in a.datas if not _is_cv2_config(e)]
a.datas.append(("cv2/config.py", str(ROOT / "packaging" / "cv2_config.py"), "DATA"))

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=NAME,
    console=False,
    icon=icon,
    upx=False,  # UPX slows start-up and trips antivirus heuristics
)

coll = COLLECT(exe, a.binaries, a.datas, name=NAME, upx=False)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{NAME}.app",
        icon=icon,
        bundle_identifier="app.faceforge." + EDITION,
        info_plist={
            "CFBundleShortVersionString": "2.0.0",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "12.0",
        },
    )
