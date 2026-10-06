"""End-to-end check with the real models.

Skipped unless FACEFORGE_TEST_MODELS points to a folder with scrfd_2.5g.onnx,
arcface_w600k_r50.onnx and inswapper_128.onnx, and FACEFORGE_TEST_IMAGE to a
photo with at least two people.
"""
import os
import time
from pathlib import Path

import pytest

MODELS = os.environ.get("FACEFORGE_TEST_MODELS")
IMAGE = os.environ.get("FACEFORGE_TEST_IMAGE")
pytestmark = pytest.mark.skipif(not (MODELS and IMAGE), reason="real models not configured")


def _wait(qapp, predicate, timeout=300):
    end = time.time() + timeout
    while time.time() < end:
        qapp.processEvents()
        if predicate():
            return True
        time.sleep(0.05)
    return False


def test_image_and_video_jobs_through_controller(qapp, tmp_path):
    from faceforge.config import Settings
    from faceforge.helpers import ffmpeg
    from faceforge.helpers.image_io import read_image, write_image
    from faceforge.ui.controller import Controller

    settings = Settings(tmp_path / "settings.json")
    settings.update({"models_dir": MODELS, "device": "cpu", "output_folder": str(tmp_path / "out")})
    controller = Controller(settings)
    controller.apply_preset("performance")

    image = read_image(IMAGE)
    h, w = image.shape[:2]
    source = tmp_path / "source.png"
    write_image(source, image[:, w // 2:])  # a person from the right half
    controller.add_sources([str(source)])
    assert _wait(qapp, lambda: controller.source_embedding is not None, 60)

    results = {}
    controller.job_finished.connect(lambda path, resumed: results.update(done=path))
    controller.job_failed.connect(lambda error: results.update(error=error))

    controller.set_targets([IMAGE])
    assert _wait(qapp, lambda: len(controller.target_faces) >= 2, 60)
    controller.start_job()
    assert _wait(qapp, lambda: results, 300), "image job did not finish"
    assert "done" in results, results
    assert read_image(results["done"]).shape == image.shape

    clip = tmp_path / "clip.mp4"
    ffmpeg.run(["-loglevel", "error", "-y", "-loop", "1", "-i", IMAGE, "-f", "lavfi", "-i",
                "sine=duration=1", "-t", "1", "-r", "10", "-vf", "scale=640:-2", "-c:v", "libx264",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(clip)])
    results.clear()
    controller.set_targets([str(clip)])
    controller.start_job()
    assert _wait(qapp, lambda: results, 600), "video job did not finish"
    assert "done" in results, results
    assert Path(results["done"]).stat().st_size > 0
    controller.shutdown()
