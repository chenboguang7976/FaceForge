"""Resumable model downloads with progress and size verification."""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Callable

import requests

from faceforge.core.models_data import ModelInfo
from faceforge.helpers.logger import get_logger

log = get_logger(__name__)

CHUNK = 1 << 20  # 1 MiB


class DownloadCancelled(Exception):
    pass


def download_model(info: ModelInfo, models_dir: Path,
                   progress: Callable[[int, int], None] | None = None,
                   cancel: threading.Event | None = None) -> Path:
    """Download ``info`` into ``models_dir``. Interrupted downloads resume from
    the ``.part`` file. Raises on network errors, size mismatch or cancel."""
    models_dir.mkdir(parents=True, exist_ok=True)
    target = models_dir / info.file
    if target.is_file() and target.stat().st_size == info.size:
        return target

    part = target.with_suffix(target.suffix + ".part")
    done = part.stat().st_size if part.exists() else 0
    if done > info.size:
        part.unlink()
        done = 0

    headers = {"Range": f"bytes={done}-"} if done else {}
    log.info("Downloading %s (%d MB)%s", info.file, info.size_mb, f", resuming at {done}" if done else "")
    with requests.get(info.url, headers=headers, stream=True, timeout=(15, 60)) as response:
        if done and response.status_code != 206:
            done = 0  # server ignored the range request; start over
        response.raise_for_status()
        with open(part, "ab" if done else "wb") as f:
            for chunk in response.iter_content(CHUNK):
                if cancel is not None and cancel.is_set():
                    raise DownloadCancelled(info.key)
                f.write(chunk)
                done += len(chunk)
                if progress:
                    progress(done, info.size)

    if part.stat().st_size != info.size:
        size = part.stat().st_size
        part.unlink(missing_ok=True)
        raise OSError(f"{info.file}: expected {info.size} bytes, got {size}")
    os.replace(part, target)
    return target
