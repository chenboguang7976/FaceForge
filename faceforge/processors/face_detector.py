"""Face detection: SCRFD / RetinaFace (InsightFace format) and YOLOFace."""
from __future__ import annotations

import cv2
import numpy as np

from faceforge.core.face import Face
from faceforge.core.models_processor import ModelsProcessor
from faceforge.processors.utils.face_align import nms

NMS_THRESHOLD = 0.4


def _letterbox(frame: np.ndarray, size: int) -> tuple[np.ndarray, float]:
    """Resize keeping aspect ratio, padded at the bottom/right to ``size``²."""
    h, w = frame.shape[:2]
    ratio = min(size / h, size / w)
    nh, nw = max(1, int(round(h * ratio))), max(1, int(round(w * ratio)))
    canvas = np.zeros((size, size, 3), np.uint8)
    canvas[:nh, :nw] = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA if ratio < 1 else cv2.INTER_LINEAR)
    return canvas, ratio


class FaceDetector:
    def __init__(self, models: ModelsProcessor):
        self.models = models
        self._anchor_cache: dict[tuple[int, int, int], np.ndarray] = {}

    def detect(self, frame: np.ndarray, model: str = "scrfd", size: int = 640,
               score_threshold: float = 0.5) -> list[Face]:
        if model == "yoloface":
            faces = self._detect_yolo(frame, score_threshold)
        else:
            if model == "retinaface":
                size = 640  # the exported RetinaFace graph has fixed output sizes
            size = max(160, int(size) // 32 * 32)
            faces = self._detect_scrfd(frame, model, size, score_threshold)
        faces.sort(key=lambda f: f.bbox[0])  # stable left-to-right order
        return faces

    # ------------------------------------------------------------ SCRFD family
    def _anchors(self, height: int, width: int, stride: int) -> np.ndarray:
        key = (height, width, stride)
        if key not in self._anchor_cache:
            grid = np.stack(np.mgrid[:height, :width][::-1], axis=-1).astype(np.float32)
            centers = (grid * stride).reshape(-1, 2)
            self._anchor_cache[key] = np.repeat(centers, 2, axis=0)  # 2 anchors per cell
        return self._anchor_cache[key]

    def _detect_scrfd(self, frame: np.ndarray, model: str, size: int, threshold: float) -> list[Face]:
        image, ratio = _letterbox(frame, size)
        blob = ((image[:, :, ::-1].astype(np.float32) - 127.5) / 128.0).transpose(2, 0, 1)[None]
        name = self.models.session(model).get_inputs()[0].name
        outputs = self.models.run(model, {name: blob})

        boxes, kpss, scores = [], [], []
        for index, stride in enumerate((8, 16, 32)):
            score = outputs[index].reshape(-1)
            keep = np.where(score >= threshold)[0]
            if keep.size == 0:
                continue
            anchors = self._anchors(size // stride, size // stride, stride)[keep]
            dist = outputs[index + 3][keep] * stride
            kps = outputs[index + 6][keep].reshape(-1, 5, 2) * stride
            boxes.append(np.hstack([anchors - dist[:, :2], anchors + dist[:, 2:]]))
            kpss.append(kps + anchors[:, None, :])
            scores.append(score[keep])
        if not boxes:
            return []
        boxes = np.vstack(boxes) / ratio
        kpss = np.vstack(kpss) / ratio
        scores = np.concatenate(scores)
        return [Face(boxes[i], kpss[i], float(scores[i])) for i in nms(boxes, scores, NMS_THRESHOLD)]

    # ---------------------------------------------------------------- YOLOFace
    def _detect_yolo(self, frame: np.ndarray, threshold: float) -> list[Face]:
        image, ratio = _letterbox(frame, 640)
        blob = (image[:, :, ::-1].astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
        name = self.models.session("yoloface").get_inputs()[0].name
        pred = self.models.run("yoloface", {name: blob})[0][0].T  # (8400, 20)
        keep = pred[:, 4] >= threshold
        pred = pred[keep]
        if len(pred) == 0:
            return []
        cx, cy, w, h = pred[:, 0], pred[:, 1], pred[:, 2], pred[:, 3]
        boxes = np.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], axis=1) / ratio
        kpss = pred[:, 5:].reshape(-1, 5, 3)[:, :, :2] / ratio
        scores = pred[:, 4]
        return [Face(boxes[i], kpss[i], float(scores[i])) for i in nms(boxes, scores, NMS_THRESHOLD)]
