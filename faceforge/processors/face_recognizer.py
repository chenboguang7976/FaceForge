"""Face identity embeddings (ArcFace)."""
from __future__ import annotations

import numpy as np

from faceforge.core.face import Face
from faceforge.core.models_processor import ModelsProcessor
from faceforge.processors.utils.face_align import warp_face

RECOGNIZER = "arcface_w600k_r50"


class FaceRecognizer:
    def __init__(self, models: ModelsProcessor):
        self.models = models

    def embed(self, frame: np.ndarray, face: Face) -> np.ndarray:
        crop, _ = warp_face(frame, face.kps, "arcface_112", 112)
        blob = ((crop[:, :, ::-1].astype(np.float32) - 127.5) / 127.5).transpose(2, 0, 1)[None]
        name = self.models.session(RECOGNIZER).get_inputs()[0].name
        embedding = self.models.run(RECOGNIZER, {name: blob})[0].reshape(-1)
        face.embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        return face.embedding

    def embed_all(self, frame: np.ndarray, faces: list[Face]) -> list[Face]:
        for face in faces:
            if face.embedding is None:
                self.embed(frame, face)
        return faces


def average_embedding(embeddings: list[np.ndarray]) -> np.ndarray | None:
    """Mean identity of several source photos — more robust than a single photo."""
    if not embeddings:
        return None
    mean = np.mean(np.stack(embeddings), axis=0)
    return mean / (np.linalg.norm(mean) + 1e-8)
