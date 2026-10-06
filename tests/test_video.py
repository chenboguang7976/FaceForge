import threading
from pathlib import Path

import numpy as np
import pytest

from faceforge.core import video_processor as vp
from faceforge.core.pipeline import ProcessOptions, SwapContext
from faceforge.helpers import ffmpeg

pytestmark = pytest.mark.skipif(not ffmpeg.find_ffmpeg(), reason="ffmpeg not available")


class InvertPipeline:
    """Stand-in for FacePipeline: inverts every frame, no models needed."""

    def prepare(self, options):
        pass

    def process_frame(self, frame, ctx, options):
        return 255 - frame


@pytest.fixture
def clip(tmp_path) -> Path:
    path = tmp_path / "clip thử.mp4"  # non-ASCII on purpose
    result = ffmpeg.run(["-loglevel", "error", "-y",
                         "-f", "lavfi", "-i", "testsrc=size=160x120:rate=25:duration=1.6",
                         "-f", "lavfi", "-i", "sine=frequency=440:duration=1.6",
                         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path)])
    assert result.returncode == 0, result.stderr
    return path


def test_probe(clip):
    info = vp.probe_video(str(clip))
    assert (info.width, info.height) == (160, 120)
    assert info.fps == pytest.approx(25, abs=0.1)
    assert info.frame_count == 40
    assert info.has_audio


def test_process_cancel_and_resume(clip, tmp_path, monkeypatch):
    monkeypatch.setattr(vp, "SEGMENT_FRAMES", 10)
    processor = vp.VideoProcessor(InvertPipeline())
    job = vp.VideoJob(str(clip), tmp_path / "out.mp4", ProcessOptions(), SwapContext(), encoder="libx264",
                      quality=95, workers=2)

    cancel = threading.Event()

    def progress(done, total, fps):
        if done >= 25:
            cancel.set()

    with pytest.raises(vp.JobCancelled):
        processor.run(job, progress, cancel=cancel)

    output, resumed_from = processor.run(job)
    assert resumed_from in (10, 20)  # whole finished segments are reused
    info = vp.probe_video(str(output))
    assert info.frame_count == 40
    assert info.has_audio

    original = vp.read_frame_at(str(clip), 30).astype(int)
    processed = vp.read_frame_at(str(output), 30).astype(int)
    assert np.abs((255 - original) - processed).mean() < 12  # inverted (allowing codec loss)


def test_encoder_args_quality_mapping():
    high = ffmpeg.encoder_args("libx264", 100, low_end=False)
    low = ffmpeg.encoder_args("libx264", 50, low_end=True)
    assert high[high.index("-crf") + 1] == "18"
    assert int(low[low.index("-crf") + 1]) > 18
    assert "veryfast" in low
