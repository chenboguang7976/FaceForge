"""On-device GPU diagnostic: an A/B matrix run on the user's own hardware.

GitHub's Windows runners can't run DirectML, so GPU-only bugs (like a video
job crashing on a GTX 1050) have to be measured where they happen. Each case
runs in its own process, so a native crash ends only that case and is
recorded (exit code + faulthandler traceback) instead of killing the app.

Cases (all on the selected device, Balanced preset, same video):
  raw_nolock   4 threads run one GPU session concurrently, no lock
  raw_lock     same, serialized
  video_w1     video job, 1 worker            (no concurrency at all)
  video_w2_nolock  2 workers, GPU calls NOT serialized   (old build)
  video_w2_lock    2 workers, GPU calls serialized       (current build)
  video_w2_x264    as above but CPU encoder (rules NVENC in or out)

Each case verifies the session really ran on the GPU; if onnxruntime fell back
to CPU the case is reported INCONCLUSIVE rather than as a pass.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable

CASES = [
    ("raw_nolock", "4 threads share one GPU session, no lock"),
    ("raw_lock", "4 threads share one GPU session, serialized"),
    ("video_w1", "video, 1 worker"),
    ("video_w2_nolock", "video, 2 workers, GPU calls not serialized (old build)"),
    ("video_w2_lock", "video, 2 workers, GPU calls serialized (current build)"),
    ("video_w2_x264", "video, 2 workers, serialized, CPU encoder instead of hardware"),
]
FRAMES = int(os.environ.get("FACEFORGE_DIAGNOSE_FRAMES", "90"))
EXIT_INCONCLUSIVE = 3


_out = None


def _emit(result: dict) -> None:
    _out.write("RESULT " + json.dumps(result) + "\n")
    _out.flush()


# --------------------------------------------------------------------- worker
def run_case(case: str, video: str, device: str, out_path: str) -> int:
    """Executed in a child process (``--diagnose-case``).

    Windowed builds have no stdout/stderr, so the result line and any native
    crash traceback (faulthandler) go to ``out_path``.
    """
    global _out
    import faulthandler
    import logging

    _out = open(out_path, "w", encoding="utf-8", buffering=1)  # noqa: SIM115 - kept open for faulthandler
    faulthandler.enable(_out, all_threads=True)
    handler = logging.StreamHandler(_out)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
    logging.getLogger("faceforge").addHandler(handler)

    from faceforge.config import Settings
    from faceforge.core.hardware import detect_hardware
    from faceforge.core.models_processor import ModelsProcessor

    if case == "_crash":  # test hook: proves native crashes are captured in the report
        faulthandler._sigsegv()

    settings = Settings()
    os.environ["FACEFORGE_DML_SERIALIZE"] = "0" if case.endswith("nolock") else "1"
    hw = detect_hardware()
    mp = ModelsProcessor(settings.models_dir, device=device, workers=1 if case == "video_w1" else 2,
                         max_loaded=6, gpu_device_id=settings.get("gpu_device_id"), hardware=hw)
    base = {"case": case, "device": mp.device, "adapter": mp.adapter_name}
    start = time.perf_counter()
    if case.startswith("raw"):
        result = _raw(mp, use_lock=(case == "raw_lock"))
    else:
        result = _video(mp, video, encoder="libx264" if case.endswith("x264") else settings.get("output_video_encoder"))
    result.update(base, seconds=round(time.perf_counter() - start, 1))
    actual = set(mp._session_device.values())
    result["providers"] = sorted(actual)
    if mp.device != "cpu" and actual != {mp.device}:
        result["status"] = "INCONCLUSIVE (GPU fell back to CPU)"
        _emit(result)
        return EXIT_INCONCLUSIVE
    _emit(result)
    return 0 if result.get("status") == "OK" else 1


def _raw(mp, use_lock: bool) -> dict:
    import numpy as np

    key = "gpen_bfr_256"
    sess = mp.session(key)
    blob = np.random.default_rng(0).uniform(-1, 1, (1, 3, 256, 256)).astype(np.float32)
    reference = sess.run(None, {"input": blob})[0]
    lock = threading.Lock()
    errors, done = [], [0]

    def worker():
        for _ in range(25):
            try:
                if use_lock:
                    with lock:
                        out = sess.run(None, {"input": blob})[0]
                else:
                    out = sess.run(None, {"input": blob})[0]
                if not np.allclose(out, reference, atol=1e-2):
                    errors.append("wrong result")
                done[0] += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{type(exc).__name__}: {exc}")

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return {"status": "OK" if not errors else "ERRORS", "runs": f"{done[0]}/100", "errors": errors[:3]}


def _video(mp, video: str, encoder: str) -> dict:
    import tempfile

    from faceforge.core.pipeline import FacePipeline, ProcessOptions, SwapContext
    from faceforge.core.presets import preset_settings
    from faceforge.core.video_processor import VideoJob, VideoProcessor, probe_video, read_frame_at

    values = preset_settings("balanced", mp.hardware, mp.device)
    options = ProcessOptions(
        detector=values["face_detector_model"], detector_size=values["face_detector_size"],
        swapper=values["face_swapper_model"], pixel_boost=values["face_swapper_pixel_boost"],
        enhancer=values["face_enhancer_model"], enhancer_blend=values["face_enhancer_blend"] / 100)
    pipe = FacePipeline(mp)
    # Use the video's own first face as the source identity: no extra input needed.
    first = read_frame_at(video, 0)
    embedding = pipe.source_embedding([first], options) if first is not None else None
    if embedding is None:
        return {"status": "ERRORS", "errors": ["no face found in the first frame"]}
    with tempfile.TemporaryDirectory() as tmp:
        job = VideoJob(video, Path(tmp) / "out.mp4", options, SwapContext(source_embedding=embedding),
                       encoder=encoder, quality=80, workers=mp.workers, low_end=True, max_frames=FRAMES,
                       resume=False)
        frames = [0]
        output, _ = VideoProcessor(pipe).run(job, lambda d, t, f: frames.__setitem__(0, d))
        written = probe_video(str(output)).frame_count
    return {"status": "OK" if written >= FRAMES - 1 else "ERRORS", "frames": written,
            "encoder": encoder, "workers": mp.workers}


def diagnostic_device(hardware) -> str | None:
    """The GPU backend to test, independent of the user's current device setting
    (a run on 2026-10-06 tested CPU only because the app was set to CPU)."""
    from faceforge.core.hardware import resolve_device

    device = resolve_device("auto", hardware)
    return None if device == "cpu" else device


# ----------------------------------------------------------------- orchestrator
def run_all(video: str, device: str, report_path: Path,
            progress: Callable[[str], None] | None = None, timeout: int = 900,
            cases: list[tuple[str, str]] | None = None) -> Path:
    if getattr(sys, "frozen", False):
        base_cmd = [sys.executable]
    else:
        base_cmd = [sys.executable, str(Path(__file__).resolve().parent.parent / "run.py")]
    lines = [f"FaceForge GPU diagnostic — {time.strftime('%Y-%m-%d %H:%M:%S')}",
             f"video: {video}", f"device: {device}"]
    if device == "cpu":
        lines.append("WARNING: device is CPU, so this is NOT a GPU test.")
    lines.append("")
    for case, description in cases or CASES:
        if progress:
            progress(case)
        start = time.perf_counter()
        case_log = report_path.with_name(f"diagnose-{case}.log")
        kwargs = {"creationflags": 0x08000000} if sys.platform == "win32" else {}
        try:
            proc = subprocess.run([*base_cmd, "--diagnose-case", case, "--diagnose-video", video,
                                   "--diagnose-device", device, "--diagnose-out", str(case_log)],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout, **kwargs)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            code = "TIMEOUT"
        elapsed = time.perf_counter() - start
        try:
            output = case_log.read_text("utf-8", "replace")
        except OSError:
            output = ""
        result = next((ln[7:] for ln in reversed(output.splitlines()) if ln.startswith("RESULT ")), None)
        if isinstance(code, int) and code > 255:
            code_text = f"{code} (0x{code & 0xFFFFFFFF:08X}, native crash)"
        elif isinstance(code, int) and code < 0:
            code_text = f"{code} (killed by signal {-code}, native crash)"
        else:
            code_text = str(code)
        lines.append(f"## {case}: {description}")
        lines.append(f"exit code: {code_text}   time: {elapsed:.0f}s")
        lines.append(f"result: {result or '(no result: crashed or timed out)'}")
        if not result or code not in (0, EXIT_INCONCLUSIVE):
            tail = "\n".join(output.splitlines()[-40:])
            lines.append("last output:\n" + tail)
        lines.append("")
        report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
