import numpy as np

from faceforge.processors.utils.face_align import (TEMPLATES, box_mask, estimate_matrix, match_color,
                                                   nms, paste_back, warp_face)


def test_warp_maps_landmarks_onto_template():
    kps = TEMPLATES["arcface_128"] * 200 + [300, 150]
    matrix = estimate_matrix(kps, "arcface_128", 128)
    mapped = np.hstack([kps, np.ones((5, 1))]) @ matrix.T
    assert np.allclose(mapped, TEMPLATES["arcface_128"] * 128, atol=0.5)


def test_paste_back_only_touches_face_region():
    frame = np.zeros((400, 600, 3), np.uint8)
    kps = TEMPLATES["arcface_128"] * 100 + [250, 150]
    crop, matrix = warp_face(frame, kps, "arcface_128", 128)
    white = np.full_like(crop, 255)
    out = paste_back(frame.copy(), white, np.ones((128, 128), np.float32), matrix)
    assert out[200, 300].min() == 255           # inside the face
    assert out[10, 10].max() == 0               # far outside untouched
    assert out[390, 590].max() == 0


def test_box_mask_is_soft_and_bounded():
    mask = box_mask(128, blur=0.3, padding=(10, 0, 0, 0))
    assert mask.shape == (128, 128)
    assert 0.0 <= mask.min() and mask.max() <= 1.0
    assert mask[64, 64] > 0.95 and mask[0, 64] < 0.05
    assert mask[5, 64] < mask[64, 64]           # top padding applied


def test_nms_suppresses_overlaps():
    boxes = np.array([[0, 0, 10, 10], [1, 1, 11, 11], [50, 50, 60, 60]], np.float32)
    scores = np.array([0.9, 0.8, 0.7], np.float32)
    assert nms(boxes, scores, 0.4) == [0, 2]


def test_match_color_shifts_towards_reference():
    src = np.full((64, 64, 3), 60, np.uint8)
    ref = np.full((64, 64, 3), 180, np.uint8)
    out = match_color(src, ref, np.ones((64, 64), np.float32))
    assert abs(int(out.mean()) - 180) < 10


def test_68_points_reduce_to_the_5_point_layout():
    from faceforge.processors.face_landmarker import to_five

    points = np.zeros((68, 2), np.float32)
    points[36:42] = (10, 20)
    points[42:48] = (30, 20)
    points[30] = (20, 30)
    points[48], points[54] = (12, 40), (28, 40)
    assert np.allclose(to_five(points), [(10, 20), (30, 20), (20, 30), (12, 40), (28, 40)])


def test_landmarker_model_is_required_only_when_enabled():
    from faceforge.core.pipeline import FacePipeline, ProcessOptions

    assert "2dfan4" in FacePipeline.required_models(ProcessOptions(landmarker=True))
    assert "2dfan4" not in FacePipeline.required_models(ProcessOptions(landmarker=False))
