"""Settings and configuration management for FaceForge.

Provides a centralized settings manager that persists to JSON
and supplies defaults for all configurable parameters.
"""
import json
import os
from pathlib import Path
from typing import Any


# Default settings with English keys
DEFAULT_SETTINGS = {
    # --- Device & Performance ---
    "device": "cuda",                    # "cuda" or "cpu"
    "max_threads": 4,
    "max_memory_gb": 16,                 # Max RAM usage
    "vram_strategy": "strict",           # "strict" or "balanced"

    # --- Output ---
    "output_quality": 80,                # JPEG quality 1-100
    "output_folder": "",
    "keep_fps": True,
    "keep_audio": True,
    "temp_frame_format": "jpg",
    "temp_frame_quality": 100,

    # --- Face Detection ---
    "face_detector": "RetinaFace",       # RetinaFace, SCRFD, Yolov8, Yunet
    "face_detect_size": "640x640",
    "face_detect_score": 0.5,
    "face_sort_order": "left-right",     # left-right, right-left, top-bottom, etc.
    "face_filter_age": "any",
    "face_filter_gender": "any",

    # --- Face Swap ---
    "face_swapper_model": "Inswapper128",
    "face_swap_mode": "all",             # "all" or "selected"
    "face_swapper_pixel_boost": "256x256",
    "reference_face_distance": 0.3,

    # --- Face Enhancement ---
    "face_enhancer_model": "GFPGAN 1.4",
    "face_enhancer_blend": 80,           # Blend % with original

    # --- Face Editing ---
    "face_editor_eyebrow": 0.0,
    "face_editor_eye_gaze_h": 0.0,
    "face_editor_eye_gaze_v": 0.0,
    "face_editor_eye_open": 0.0,
    "face_editor_lip_open": 0.0,
    "face_editor_mouth_grim": 0.0,
    "face_editor_mouth_pout": 0.0,
    "face_editor_mouth_purse": 0.0,
    "face_editor_mouth_smile": 0.0,
    "face_editor_mouth_pos_h": 0.0,
    "face_editor_mouth_pos_v": 0.0,
    "face_editor_head_pitch": 0.0,
    "face_editor_head_yaw": 0.0,
    "face_editor_head_roll": 0.0,
    "age_modifier_direction": 0,
    "expression_restorer_factor": 100,

    # --- Frame Enhancement ---
    "frame_enhancer_model": "SPAN x4",
    "frame_enhancer_blend": 80,

    # --- Colorization ---
    "colorizer_model": "DDColor",
    "colorizer_blend": 100,

    # --- Face Mask ---
    "mask_type": "box",                  # "box", "occlusion", "region"
    "mask_blur": 30,
    "mask_padding_top": 0,
    "mask_padding_bottom": 0,
    "mask_padding_left": 0,
    "mask_padding_right": 0,

    # --- Lip Sync ---
    "lip_syncer_model": "Wav2Lip-GAN",

    # --- Live / Webcam ---
    "webcam_device": "0",
    "webcam_resolution": "960x540",
    "webcam_fps": 25,

    # --- UI ---
    "theme": "dark",
    "window_width": 1376,
    "window_height": 768,
    "show_parameters_panel": True,
    "show_faces_panel": True,
    "show_media_panel": True,

    # --- Misc ---
    "auto_shutdown": False,
    "open_output_folder": False,

    # --- Source / Target paths (session) ---
    "source_face_path": "",
    "target_media_path": "",
}


class Settings:
    """Manages application settings with JSON persistence.

    Settings are loaded from 'settings.json' in the application directory.
    If the file doesn't exist, defaults are used and saved on first write.
    """

    def __init__(self, settings_file: str = "settings.json"):
        self._file = Path(settings_file)
        self._data: dict = {}
        self._defaults = DEFAULT_SETTINGS.copy()
        self._load()

    def _load(self):
        """Load settings from file, falling back to defaults."""
        if self._file.exists():
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                # Merge: defaults as base, override with saved values
                self._data = {**self._defaults, **saved}
            except (json.JSONDecodeError, OSError):
                self._data = self._defaults.copy()
        else:
            self._data = self._defaults.copy()

    def save(self):
        """Persist current settings to file."""
        try:
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4, ensure_ascii=False)
        except OSError as e:
            print(f"[Settings] Failed to save: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value (does not auto-save)."""
        self._data[key] = value

    def get_all(self) -> dict:
        """Return a copy of all settings."""
        return self._data.copy()

    def reset(self, key: str = None):
        """Reset a specific key or all settings to defaults."""
        if key:
            self._data[key] = self._defaults.get(key)
        else:
            self._data = self._defaults.copy()

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any):
        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._data
