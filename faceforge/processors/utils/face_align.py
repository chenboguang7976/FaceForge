"""Face alignment, masks and paste-back.

Templates are 5-point landmark positions (eyes, nose, mouth corners)
normalised to [0, 1] for the crop each model was trained on.
"""
from __future__ import annotations

import cv2
import numpy as np

TEMPLATES = {
    # InsightFace ArcFace 112x112 (recognition).
    "arcface_112": np.array([[0.34191607, 0.46157411], [0.65653393, 0.45983393],
                             [0.50022500, 0.64050536], [0.37097589, 0.82469196],
                             [0.63151696, 0.82325089]], np.float32),
    # ArcFace template shifted for 128px crops (InSwapper / HyperSwap).
    "arcface_128": np.array([[0.36167656, 0.40387734], [0.63696719, 0.40235469],
                             [0.50019687, 0.56044219], [0.38710391, 0.72160547],
                             [0.61507734, 0.72034453]], np.float32),
    # FFHQ alignment (GFPGAN, CodeFormer, GPEN, RestoreFormer).
    "ffhq_512": np.array([[0.37691676, 0.46864664], [0.62285697, 0.46912813],
                          [0.50123859, 0.61331904], [0.39308822, 0.72541100],
                          [0.61150205, 0.72490465]], np.float32),
}


def estimate_matrix(kps5: np.ndarray, template: str, size: int) -> np.ndarray:
    dst = TEMPLATES[template] * size
    matrix, _ = cv2.estimateAffinePartial2D(kps5.astype(np.float32), dst,
                                            method=cv2.RANSAC, ransacReprojThreshold=100)
    if matrix is None:  # degenerate landmarks; fall back to a least-squares fit
        matrix, _ = cv2.estimateAffinePartial2D(kps5.astype(np.float32), dst, method=cv2.LMEDS)
    return matrix


def warp_face(frame: np.ndarray, kps5: np.ndarray, template: str, size: int) -> tuple[np.ndarray, np.ndarray]:
    matrix = estimate_matrix(kps5, template, size)
    crop = cv2.warpAffine(frame, matrix, (size, size), flags=cv2.INTER_AREA,
                          borderMode=cv2.BORDER_REPLICATE)
    return crop, matrix


def paste_back(frame: np.ndarray, crop: np.ndarray, mask: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Blend ``crop`` back into ``frame`` (in place) using ``mask`` (float 0..1).

    Only the face's bounding region is warped and blended, not the whole
    frame — on a 1080p video this is several times cheaper on a weak CPU.
    """
    height, width = frame.shape[:2]
    inverse = cv2.invertAffineTransform(matrix)
    ch, cw = crop.shape[:2]
    corners = np.array([[0, 0, 1], [cw, 0, 1], [0, ch, 1], [cw, ch, 1]], np.float32) @ inverse.T
    x0 = int(max(0, np.floor(corners[:, 0].min())))
    y0 = int(max(0, np.floor(corners[:, 1].min())))
    x1 = int(min(width, np.ceil(corners[:, 0].max()) + 1))
    y1 = int(min(height, np.ceil(corners[:, 1].max()) + 1))
    if x1 <= x0 or y1 <= y0:
        return frame

    inverse[:, 2] -= (x0, y0)
    size = (x1 - x0, y1 - y0)
    warped = cv2.warpAffine(crop, inverse, size, flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_REPLICATE)
    alpha = cv2.warpAffine(mask, inverse, size, flags=cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    alpha = np.clip(alpha, 0, 1)[..., None]
    roi = frame[y0:y1, x0:x1]
    blended = roi.astype(np.float32) * (1 - alpha) + warped.astype(np.float32) * alpha
    frame[y0:y1, x0:x1] = np.clip(blended, 0, 255).astype(np.uint8)
    return frame


def box_mask(size: int, blur: float = 0.3, padding: tuple[int, int, int, int] = (0, 0, 0, 0)) -> np.ndarray:
    """Soft rectangular mask. ``padding`` is (top, right, bottom, left) in % of the crop."""
    blur_amount = int(size * 0.5 * blur)
    blur_area = max(blur_amount // 2, 1)
    mask = np.ones((size, size), np.float32)
    top, right, bottom, left = padding
    mask[:max(blur_area, int(size * top / 100)), :] = 0
    mask[-max(blur_area, int(size * bottom / 100)):, :] = 0
    mask[:, :max(blur_area, int(size * left / 100))] = 0
    mask[:, -max(blur_area, int(size * right / 100)):] = 0
    if blur_amount > 0:
        mask = cv2.GaussianBlur(mask, (0, 0), blur_amount * 0.25)
    return mask


def match_color(source: np.ndarray, reference: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Shift ``source`` colours (LAB mean/std) towards ``reference`` inside ``mask``."""
    weights = (mask > 0.5)
    if weights.sum() < 64:
        return source
    src = cv2.cvtColor(source, cv2.COLOR_BGR2LAB).astype(np.float32)
    ref = cv2.cvtColor(reference, cv2.COLOR_BGR2LAB).astype(np.float32)
    for c in range(3):
        s_vals, r_vals = src[..., c][weights], ref[..., c][weights]
        s_mean, s_std = s_vals.mean(), s_vals.std() + 1e-6
        r_mean, r_std = r_vals.mean(), r_vals.std() + 1e-6
        # Only luminance gets its contrast rescaled; chroma is just shifted.
        scale = np.clip(r_std / s_std, 0.7, 1.4) if c == 0 else 1.0
        src[..., c] = (src[..., c] - s_mean) * scale + r_mean
    return cv2.cvtColor(np.clip(src, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)


# ------------------------------------------------------------------ detection
def nms(boxes: np.ndarray, scores: np.ndarray, threshold: float) -> list[int]:
    if len(boxes) == 0:
        return []
    x1, y1, x2, y2 = boxes.T
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(int(i))
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        inter = np.maximum(0, xx2 - xx1 + 1) * np.maximum(0, yy2 - yy1 + 1)
        iou = inter / (areas[i] + areas[order[1:]] - inter)
        order = order[np.where(iou <= threshold)[0] + 1]
    return keep
