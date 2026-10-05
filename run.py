#!/usr/bin/env python3
"""FaceForge — AI Face Swap & Enhancement Tool. Application entry point."""
import argparse
import os
import sys

# Ensure the project root is in path when run from source.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog="faceforge")
    parser.add_argument("--debug", action="store_true", help="verbose logging")
    parser.add_argument("--edition", choices=("pro", "lite"), help="override the build edition")
    parser.add_argument("--selftest", action="store_true",
                        help="check the installation/bundle (inference, ffmpeg, UI) and exit")
    # Internal: one case of the GPU diagnostic, run in a child process.
    parser.add_argument("--diagnose-case", help=argparse.SUPPRESS)
    parser.add_argument("--diagnose-video", help=argparse.SUPPRESS)
    parser.add_argument("--diagnose-device", default="auto", help=argparse.SUPPRESS)
    parser.add_argument("--diagnose-out", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.edition:
        os.environ["FACEFORGE_EDITION"] = args.edition

    from faceforge.helpers.logger import get_logger, install_crash_handlers, setup_logging

    setup_logging(args.debug)
    install_crash_handlers()
    log = get_logger("main")

    if args.diagnose_case:  # child process of the GPU diagnostic: no UI
        from faceforge.diagnose import run_case

        return run_case(args.diagnose_case, args.diagnose_video, args.diagnose_device, args.diagnose_out)

    if sys.platform == "win32":
        try:  # Group the taskbar icon under FaceForge rather than python.exe.
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FaceForge.App")
        except (AttributeError, OSError):
            pass

    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import QApplication, QMessageBox

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)

    from faceforge import __app_name__, __version__, edition

    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(__app_name__)
    log.info("FaceForge %s (%s edition)", __version__, edition.current())

    from faceforge.config import Settings
    from faceforge.ui import icons
    from faceforge.ui.i18n import i18n
    from faceforge.ui.theme import theme

    settings = Settings()
    theme.apply(app, settings.get("theme"))
    i18n.set_language(settings.get("language"))
    app.setWindowIcon(icons.app_icon())

    import importlib.util

    if importlib.util.find_spec("onnxruntime") is None:
        QMessageBox.critical(None, "FaceForge", "onnxruntime is not installed.\n\n"
                             "pip install -r requirements.txt")
        return 1

    from faceforge.ui.main_window import MainWindow

    if args.selftest:
        return selftest(app, settings, MainWindow)

    window = MainWindow(settings)
    window.show()
    QTimer.singleShot(300, window.maybe_welcome)
    return app.exec()


def selftest(app, settings, window_class) -> int:
    """Smoke test used by CI on the frozen build: catches missing modules,
    DLLs or Qt plugins without needing a GPU or the large models."""
    import tempfile

    import numpy as np
    import onnx
    import onnxruntime as ort
    from onnx import TensorProto, helper

    from faceforge.core.hardware import detect_hardware
    from faceforge.helpers import ffmpeg
    from faceforge.helpers.logger import get_logger

    log = get_logger("selftest")
    hw = detect_hardware()
    log.info("onnxruntime %s, providers: %s", ort.__version__, ort.get_available_providers())

    graph = helper.make_graph(
        [helper.make_node("Add", ["x", "x"], ["y"])], "selftest",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, 4])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 4])])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
    model.ir_version = 8
    with tempfile.TemporaryDirectory() as tmp:
        path = f"{tmp}/selftest.onnx"
        onnx.save(model, path)
        session = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        out = session.run(None, {"x": np.ones((1, 4), np.float32)})[0]
    assert float(out.sum()) == 8.0, "inference returned a wrong result"

    exe = ffmpeg.find_ffmpeg()
    assert exe, "ffmpeg not found"
    log.info("ffmpeg: %s", exe)

    window = window_class(settings)
    window.show()
    app.processEvents()
    window.close()
    log.info("Selftest OK — %s", hw.summary())
    if sys.stdout is not None:  # None in windowed (no-console) builds
        print("SELFTEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
