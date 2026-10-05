"""Quality presets: one click instead of a dozen checkboxes.

Changing any individual option afterwards switches the preset to "custom".
"""
from __future__ import annotations

from faceforge import edition
from faceforge.core.hardware import (PROFILE_HIGH, PROFILE_LOW, HardwareInfo, classify,
                                     fast_fp16)

PRESET_PERFORMANCE = "performance"
PRESET_BALANCED = "balanced"
PRESET_QUALITY = "quality"
PRESET_MAXIMUM = "maximum"
PRESET_CUSTOM = "custom"
PRESETS = [PRESET_PERFORMANCE, PRESET_BALANCED, PRESET_QUALITY, PRESET_MAXIMUM]

# Settings a preset controls. Anything else (paths, UI, language) is untouched.
PRESET_KEYS = (
    "face_detector_model", "face_detector_size", "face_swapper_model", "face_swapper_pixel_boost",
    "face_enhancer_enabled", "face_enhancer_model", "face_enhancer_blend",
    "face_mask_occlusion", "face_mask_region", "face_mask_blur", "output_video_quality",
)


def preset_settings(name: str, info: HardwareInfo, device: str) -> dict:
    inswapper = "inswapper_128_fp16" if fast_fp16(info, device) else "inswapper_128"
    if name == PRESET_PERFORMANCE:
        return {
            "face_detector_model": "scrfd",
            "face_detector_size": 640 if device != "cpu" else 480,
            "face_swapper_model": inswapper,
            "face_swapper_pixel_boost": 128,
            "face_enhancer_enabled": False,
            "face_enhancer_model": "gpen_bfr_256",
            "face_enhancer_blend": 70,
            "face_mask_occlusion": False,
            "face_mask_region": False,
            "face_mask_blur": 0.3,
            "output_video_quality": 80,
        }
    if name == PRESET_BALANCED:
        return {
            "face_detector_model": "retinaface",
            "face_detector_size": 640,
            "face_swapper_model": inswapper,
            "face_swapper_pixel_boost": 256,
            "face_enhancer_enabled": True,
            "face_enhancer_model": "gpen_bfr_256",
            "face_enhancer_blend": 70,
            "face_mask_occlusion": False,
            "face_mask_region": False,
            "face_mask_blur": 0.3,
            "output_video_quality": 85,
        }
    if name == PRESET_QUALITY:
        return {
            "face_detector_model": "retinaface",
            "face_detector_size": 640,
            "face_swapper_model": "hyperswap_1a_256",
            "face_swapper_pixel_boost": 256,
            "face_enhancer_enabled": True,
            "face_enhancer_model": "gfpgan_1.4",
            "face_enhancer_blend": 80,
            "face_mask_occlusion": True,
            "face_mask_region": False,
            "face_mask_blur": 0.3,
            "output_video_quality": 90,
        }
    # Maximum: 2×2 pixel boost on HyperSwap (4 passes per face), parsing +
    # occlusion masks and the strongest restoration. For high-end GPUs.
    return {
        "face_detector_model": "retinaface",
        "face_detector_size": 640,
        "face_swapper_model": "hyperswap_1a_256",
        "face_swapper_pixel_boost": 512,
        "face_enhancer_enabled": True,
        "face_enhancer_model": "gfpgan_1.4",
        "face_enhancer_blend": 85,
        "face_mask_occlusion": True,
        "face_mask_region": True,
        "face_mask_blur": 0.25,
        "output_video_quality": 95,
    }


def default_preset(info: HardwareInfo) -> str:
    profile = classify(info)
    if edition.is_lite():
        # A 4 GB GPU handles Balanced fine when system RAM isn't also tight.
        if profile == PROFILE_LOW and (info.ram_mb < 12 * 1024 or not info.primary_gpu):
            return PRESET_PERFORMANCE
        return PRESET_BALANCED
    return PRESET_MAXIMUM if profile == PROFILE_HIGH else PRESET_QUALITY


def meets_pro_requirements(info: HardwareInfo) -> bool:
    return classify(info) != PROFILE_LOW
