"""Settings persisted as JSON in the data folder (see ``helpers.paths``)."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from faceforge.helpers.logger import get_logger
from faceforge.helpers.paths import default_models_dir, default_output_dir, settings_file

log = get_logger(__name__)

SETTINGS_VERSION = 3

DEFAULT_SETTINGS: dict[str, Any] = {
    "settings_version": SETTINGS_VERSION,
    "first_run_done": False,

    # --- Device & performance ---
    "device": "auto",                  # auto | cuda | directml | coreml | cpu
    "gpu_device_id": -1,               # -1 = pick the best GPU automatically
    "execution_workers": 2,
    "max_loaded_models": 3,
    "performance_profile": "low",      # informational, from hardware detection

    # --- Quality preset ---
    "preset": "performance",           # performance | balanced | quality | maximum | custom

    # --- Face detection ---
    "face_detector_model": "scrfd",    # scrfd | retinaface | yoloface
    "face_detector_size": 640,
    "face_detector_score": 0.5,

    # --- Face selection ---
    "face_selector_mode": "all",       # all | largest | reference
    "reference_face_distance": 0.6,

    # --- Face swap ---
    "face_swap_enabled": True,
    "face_swapper_model": "inswapper_128",
    "face_swapper_pixel_boost": 128,
    "face_color_match": False,

    # --- Mask ---
    "face_mask_blur": 0.3,
    "face_mask_padding": [0, 0, 0, 0],  # top, right, bottom, left (%)
    "face_mask_occlusion": False,
    "face_mask_region": False,

    # --- Face enhancement ---
    "face_enhancer_enabled": False,
    "face_enhancer_model": "gpen_bfr_256",
    "face_enhancer_blend": 80,
    "codeformer_fidelity": 0.7,

    # --- Output ---
    "output_folder": "",
    "output_image_format": "png",      # png | jpg | webp
    "output_image_quality": 95,
    "output_video_quality": 80,
    "output_video_encoder": "auto",    # auto | libx264 | h264_nvenc | h264_qsv | h264_amf | h264_videotoolbox
    "keep_audio": True,

    # --- Paths ---
    "models_dir": "",

    # --- UI ---
    "language": "en",                  # en | zh | vi
    "theme": "dark",                   # dark | light
    "window_geometry": "",
    "splitter_state": "",
    "last_open_dir": "",
}


class Settings:
    """Dict-like settings with defaults and atomic JSON persistence."""

    def __init__(self, path: str | Path | None = None):
        self._file = Path(path) if path else settings_file()
        self._data: dict[str, Any] = dict(DEFAULT_SETTINGS)
        self.is_new = not self._file.exists()
        self._load()

    def _load(self) -> None:
        if self.is_new:
            return
        try:
            with open(self._file, encoding="utf-8") as f:
                saved = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            log.warning("Settings unreadable (%s); using defaults.", exc)
            self.is_new = True
            return
        if saved.get("settings_version") == 2:
            # v2 stored GPU 0, which on dual-GPU laptops is the integrated GPU.
            saved["gpu_device_id"] = -1
            saved["settings_version"] = SETTINGS_VERSION
        if saved.get("settings_version") != SETTINGS_VERSION:
            # v1 used different keys/values; only carry over what still means the same thing.
            log.info("Migrating settings from version %s", saved.get("settings_version"))
            saved = {k: saved[k] for k in ("language", "theme", "output_folder") if k in saved}
            saved["settings_version"] = SETTINGS_VERSION
        for key, value in saved.items():
            if key in DEFAULT_SETTINGS:
                self._data[key] = value

    def save(self) -> None:
        """Write via a temp file + rename so a crash never leaves a corrupt file."""
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=self._file.parent, prefix=".settings", suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self._file)
        except OSError as exc:
            log.error("Failed to save settings: %s", exc)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, DEFAULT_SETTINGS.get(key, default))

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def update(self, values: dict[str, Any]) -> None:
        self._data.update(values)

    def reset(self, key: str | None = None) -> None:
        if key:
            self._data[key] = DEFAULT_SETTINGS.get(key)
        else:
            self._data = dict(DEFAULT_SETTINGS)

    def as_dict(self) -> dict[str, Any]:
        return dict(self._data)

    # Resolved paths ------------------------------------------------------
    @property
    def models_dir(self) -> Path:
        return Path(self.get("models_dir") or default_models_dir())

    @property
    def output_dir(self) -> Path:
        return Path(self.get("output_folder") or default_output_dir())

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        return key in self._data
