"""Face data structure shared by all processors."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Face:
    bbox: np.ndarray                    # x1, y1, x2, y2
    kps: np.ndarray                     # 5x2 landmarks: eyes, nose, mouth corners
    score: float
    embedding: np.ndarray | None = None  # L2-normalised ArcFace identity vector

    @property
    def area(self) -> float:
        x1, y1, x2, y2 = self.bbox
        return float(max(0.0, x2 - x1) * max(0.0, y2 - y1))

    def distance(self, embedding: np.ndarray) -> float:
        """Cosine distance (0 = identical identity, ~1 = unrelated)."""
        if self.embedding is None:
            return 2.0
        return float(1.0 - np.dot(self.embedding, embedding))

    def crop_thumbnail(self, frame: np.ndarray, size: int = 96) -> np.ndarray:
        """Square, padded crop around the face for gallery thumbnails."""
        import cv2

        x1, y1, x2, y2 = self.bbox
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        half = max(x2 - x1, y2 - y1) * 0.65
        h, w = frame.shape[:2]
        ax1, ay1 = int(max(0, cx - half)), int(max(0, cy - half))
        ax2, ay2 = int(min(w, cx + half)), int(min(h, cy + half))
        crop = frame[ay1:ay2, ax1:ax2]
        if crop.size == 0:
            return np.zeros((size, size, 3), np.uint8)
        return cv2.resize(crop, (size, size), interpolation=cv2.INTER_AREA)
