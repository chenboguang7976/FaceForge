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


_crash_file = None


def install_crash_handlers() -> None:
    """Make crashes leave a trace in <data>/logs:

    - native crashes (access violations in GPU drivers/DLLs) -> crash.log via faulthandler
    - uncaught Python exceptions, in any thread -> faceforge.log
    """
    global _crash_file
    import faulthandler
    import threading

    log = get_logger("crash")
    try:
        _crash_file = open(logs_dir() / "crash.log", "a", encoding="utf-8")  # noqa: SIM115 - must stay open
        _crash_file.write(f"\n=== session started (pid {__import__('os').getpid()}) ===\n")
        _crash_file.flush()
        faulthandler.enable(_crash_file, all_threads=True)
    except OSError:
        pass

    def excepthook(exc_type, exc, tb):
        log.critical("Uncaught exception", exc_info=(exc_type, exc, tb))

    def thread_excepthook(args):
        log.critical("Uncaught exception in thread %s", args.thread.name if args.thread else "?",
                     exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

    sys.excepthook = excepthook
    threading.excepthook = thread_excepthook
