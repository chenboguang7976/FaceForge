"""Lightweight RAM/VRAM monitor for the status bar.

Sampling runs on a background thread every few seconds; ``nvidia-smi`` is
only queried when an NVIDIA GPU was detected.
"""
from __future__ import annotations

import os
import subprocess
import threading

import psutil
from PySide6.QtCore import QObject, QTimer, Signal

from faceforge.helpers.ffmpeg import popen_kwargs


class ResourceMonitor(QObject):
    updated = Signal(dict)

    def __init__(self, has_nvidia: bool, interval_ms: int = 3000, parent=None):
        super().__init__(parent)
        self._has_nvidia = has_nvidia
        self._process = psutil.Process(os.getpid())
        self._busy = False
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self._tick()

    def _tick(self) -> None:
        if self._busy:
            return
        self._busy = True
        threading.Thread(target=self._sample, daemon=True, name="ff-monitor").start()

    def _sample(self) -> None:
        try:
            vm = psutil.virtual_memory()
            stats = {
                "ram_used": vm.total - vm.available,
                "ram_total": vm.total,
                "app_ram": self._process.memory_info().rss,
                "vram_used": None,
                "vram_total": None,
            }
            if self._has_nvidia:
                try:
                    out = subprocess.run(
                        ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=4, **popen_kwargs())
                    used, total = out.stdout.decode().splitlines()[0].split(",")
                    stats["vram_used"], stats["vram_total"] = int(used) * 2**20, int(total) * 2**20
                except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
                    self._has_nvidia = False
            self.updated.emit(stats)
        finally:
            self._busy = False
