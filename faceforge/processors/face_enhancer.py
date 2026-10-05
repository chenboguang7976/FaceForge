"""Face restoration: GFPGAN, CodeFormer, GPEN-BFR, RestoreFormer++."""
from __future__ import annotations

import numpy as np

from faceforge.core.face import Face
from faceforge.core.models_processor import ModelsProcessor
from faceforge.processors.utils.face_align import box_mask, paste_back, warp_face

ENHANCERS = {
    "gfpgan_1.4": 512,
    "codeformer": 512,
    "gpen_bfr_256": 256,
    "gpen_bfr_512": 512,
    "restoreformer_plus_plus": 512,
}


class FaceEnhancer:
    def __init__(self, models: ModelsProcessor):
        self.models = models
        self._masks: dict[int, np.ndarray] = {}

    def _mask(self, size: int) -> np.ndarray:
        if size not in self._masks:
            self._masks[size] = box_mask(size, blur=0.3)
        return self._masks[size]

    def enhance(self, frame: np.ndarray, face: Face, model: str, blend: float = 0.8,
                fidelity: float = 0.7) -> np.ndarray:
        size = ENHANCERS[model]
        crop, matrix = warp_face(frame, face.kps, "ffhq_512", size)
        rgb = (crop[:, :, ::-1].astype(np.float32) / 255.0 - 0.5) / 0.5
        feeds = {"input": rgb.transpose(2, 0, 1)[None]}
        if model == "codeformer":
            feeds["weight"] = np.array(fidelity, dtype=np.float64)
        output = self.models.run(model, feeds)[0][0].transpose(1, 2, 0)
        enhanced = ((np.clip(output, -1, 1) + 1) / 2 * 255).astype(np.uint8)[:, :, ::-1]
        if blend < 1.0:
            enhanced = (crop.astype(np.float32) * (1 - blend)
                        + enhanced.astype(np.float32) * blend).astype(np.uint8)
        return paste_back(frame, enhanced, self._mask(size), matrix)
