"""Face swapping: InSwapper 128 (FP32/FP16) and HyperSwap 256 (1A/1B/1C).

Pixel boost renders the swap at a multiple of the model resolution by
splitting the aligned crop into interleaved sub-images (every N-th pixel),
swapping each and re-interleaving the results. It costs N² inferences, so it
is kept at the native size by default on low-end hardware.
"""
from __future__ import annotations

import threading
from pathlib import Path

import numpy as np

from faceforge.core.models_processor import ModelsProcessor
from faceforge.helpers.logger import get_logger

log = get_logger(__name__)

SWAPPERS = {
    # key: (native size, kind)
    "inswapper_128": (128, "inswapper"),
    "inswapper_128_fp16": (128, "inswapper"),
    "hyperswap_1a_256": (256, "hyperswap"),
    "hyperswap_1b_256": (256, "hyperswap"),
    "hyperswap_1c_256": (256, "hyperswap"),
}
TEMPLATE = "arcface_128"


class FaceSwapper:
    def __init__(self, models: ModelsProcessor):
        self.models = models
        self._emap: dict[str, np.ndarray] = {}
        self._emap_lock = threading.Lock()

    @staticmethod
    def native_size(model: str) -> int:
        return SWAPPERS[model][0]

    @staticmethod
    def crop_size(model: str, pixel_boost: int) -> int:
        native = SWAPPERS[model][0]
        return max(native, int(pixel_boost) // native * native)

    # ------------------------------------------------------- source identity
    def _inswapper_emap(self, model: str) -> np.ndarray:
        """InSwapper projects ArcFace embeddings through a matrix stored as the
        graph's last initializer. Extracting it means parsing the 0.5 GB model,
        so it's done once and cached as ``<model>.emap.npy``."""
        with self._emap_lock:
            if model in self._emap:
                return self._emap[model]
            model_path = self.models.path(model)
            cache = Path(str(model_path) + ".emap.npy")
            emap = None
            if cache.is_file():
                try:
                    emap = np.load(cache)
                except (OSError, ValueError):
                    emap = None
            if emap is None:
                import onnx
                from onnx import numpy_helper

                graph = onnx.load(str(model_path)).graph
                emap = numpy_helper.to_array(graph.initializer[-1]).astype(np.float32)
                del graph
                try:
                    np.save(cache, emap)
                except OSError:
                    log.warning("Could not cache %s", cache)
            self._emap[model] = emap
            return emap

    def prepare_source(self, model: str, embedding: np.ndarray) -> np.ndarray:
        kind = SWAPPERS[model][1]
        normed = embedding.reshape(1, -1).astype(np.float32)
        if kind == "inswapper":
            latent = normed @ self._inswapper_emap(model)
            return latent / np.linalg.norm(latent)
        return normed

    # ------------------------------------------------------------------- swap
    def _forward(self, model: str, tile: np.ndarray, source: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
        kind = SWAPPERS[model][1]
        rgb = tile[:, :, ::-1].astype(np.float32) / 255.0
        if kind == "hyperswap":
            rgb = (rgb - 0.5) / 0.5
        blob = rgb.transpose(2, 0, 1)[None]
        outputs = self.models.run(model, {"target": blob, "source": source})
        output = outputs[0][0].transpose(1, 2, 0)
        mask = None
        if kind == "hyperswap":
            output = (output + 1) / 2
            # HyperSwap also predicts a face-shaped blend mask.
            mask = np.clip(outputs[1][0, 0], 0, 1).astype(np.float32) if len(outputs) > 1 else None
        return (np.clip(output, 0, 1) * 255).astype(np.uint8)[:, :, ::-1], mask

    def swap(self, model: str, crop: np.ndarray, source: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
        """Swap an aligned crop (size = native × N).

        Returns the swapped crop and, for models that predict one, a blend
        mask at crop resolution (``None`` otherwise).
        """
        native = SWAPPERS[model][0]
        n = crop.shape[0] // native
        if n <= 1:
            return self._forward(model, crop, source)
        result = np.empty_like(crop)
        mask = None
        for i in range(n):
            for j in range(n):
                tile = np.ascontiguousarray(crop[i::n, j::n])
                result[i::n, j::n], tile_mask = self._forward(model, tile, source)
                if tile_mask is not None:
                    if mask is None:
                        mask = np.zeros(crop.shape[:2], np.float32)
                    mask[i::n, j::n] = tile_mask
        return result, mask
