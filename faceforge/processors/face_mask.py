"""Masks that decide which pixels of the swapped face are blended back.

- box:       soft rectangle (always on, cheap)
- occlusion: XSeg — keeps hands, hair, microphones… in front of the face
- region:    BiSeNet face parsing — only skin, brows, eyes, nose and lips
"""
from __future__ import annotations

import cv2
import numpy as np

from faceforge.core.models_processor import ModelsProcessor
from faceforge.processors.utils.face_align import box_mask

OCCLUSION_MODEL = "xseg_1"
REGION_MODEL = "bisenet_resnet_34"

# BiSeNet CelebAMask-HQ labels kept for the "face region" mask.
FACE_REGIONS = {
    "skin": 1, "left_eyebrow": 2, "right_eyebrow": 3, "left_eye": 4, "right_eye": 5,
    "glasses": 6, "nose": 10, "mouth": 11, "upper_lip": 12, "lower_lip": 13,
}
_IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], np.float32)
_IMAGENET_STD = np.array([0.229, 0.224, 0.225], np.float32)


def _soften(mask: np.ndarray) -> np.ndarray:
    return (cv2.GaussianBlur(np.clip(mask, 0, 1), (0, 0), 5).clip(0.5, 1) - 0.5) * 2


class FaceMasker:
    def __init__(self, models: ModelsProcessor):
        self.models = models
        self._box_cache: dict[tuple, np.ndarray] = {}

    def box(self, size: int, blur: float, padding: tuple[int, int, int, int]) -> np.ndarray:
        key = (size, round(blur, 3), tuple(padding))
        if key not in self._box_cache:
            if len(self._box_cache) > 16:
                self._box_cache.clear()
            self._box_cache[key] = box_mask(size, blur, padding)
        return self._box_cache[key]

    def occlusion(self, crop: np.ndarray) -> np.ndarray:
        size = crop.shape[0]
        blob = cv2.resize(crop, (256, 256)).astype(np.float32)[None] / 255.0
        name = self.models.session(OCCLUSION_MODEL).get_inputs()[0].name
        mask = self.models.run(OCCLUSION_MODEL, {name: blob})[0][0, :, :, 0]
        return _soften(cv2.resize(np.clip(mask, 0, 1), (size, size)))

    def region(self, crop: np.ndarray) -> np.ndarray:
        size = crop.shape[0]
        rgb = cv2.resize(crop, (512, 512))[:, :, ::-1].astype(np.float32) / 255.0
        blob = ((rgb - _IMAGENET_MEAN) / _IMAGENET_STD).transpose(2, 0, 1)[None]
        name = self.models.session(REGION_MODEL).get_inputs()[0].name
        labels = self.models.run(REGION_MODEL, {name: blob})[0][0].argmax(0)
        mask = np.isin(labels, list(FACE_REGIONS.values())).astype(np.float32)
        return _soften(cv2.resize(mask, (size, size)))
