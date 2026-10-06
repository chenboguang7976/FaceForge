"""Unicode-safe image I/O.

``cv2.imread``/``cv2.imwrite`` fail on Windows for paths containing
non-ASCII characters (Vietnamese or Chinese file names), so we go through
``numpy.fromfile``/``tofile`` with ``imdecode``/``imencode`` instead.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".wmv", ".flv", ".mpg", ".mpeg"}


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def is_video(path: str | Path) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS


def read_image(path: str | Path) -> np.ndarray | None:
    """Read an image as a BGR uint8 array, or ``None`` if unreadable."""
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    image = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if image is None:
        return None
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    if image.dtype != np.uint8:
        image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return image


def write_image(path: str | Path, image: np.ndarray, quality: int = 95) -> bool:
    path = Path(path)
    ext = path.suffix.lower() or ".png"
    params: list[int] = []
    if ext in (".jpg", ".jpeg"):
        params = [cv2.IMWRITE_JPEG_QUALITY, int(quality)]
    elif ext == ".webp":
        params = [cv2.IMWRITE_WEBP_QUALITY, int(quality)]
    elif ext == ".png":
        params = [cv2.IMWRITE_PNG_COMPRESSION, 3]
    ok, buffer = cv2.imencode(ext, image, params)
    if not ok:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer.tofile(str(path))
    return True


def unique_path(path: str | Path) -> Path:
    """Return ``path`` or ``name (2).ext``… so existing files are never overwritten."""
    path = Path(path)
    if not path.exists():
        return path
    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem} ({counter}){path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
