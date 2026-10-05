"""DirectML stress test, run on a Windows CI runner (WARP software adapter).

Modes
-----
raw       N threads call session.run on ONE DirectML session at the same time.
pipeline  The real video pipeline (Balanced preset, 2 workers) on a generated clip.

Lock behaviour comes from FACEFORGE_DML_SERIALIZE (1 = fixed build, 0 = old
behaviour); for `raw` the lock is applied here when --lock is given.

Exit code 0 = finished without error; 3 = INCONCLUSIVE (DirectML did not
actually run, e.g. no usable D3D12 adapter). A native crash shows up as a non-zero
exit code (0xC0000005 = 3221225477 = access violation) plus a faulthandler
traceback on stderr.
"""
from __future__ import annotations

import argparse
import faulthandler
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
faulthandler.enable(all_threads=True)

import numpy as np  # noqa: E402


def raw(models_dir: Path, threads: int, runs: int, use_lock: bool) -> int:
    import onnxruntime as ort

    sess = ort.InferenceSession(str(models_dir / "gpen_bfr_256.onnx"),
                                providers=[("DmlExecutionProvider", {"device_id": 0})])
    print("providers:", sess.get_providers(), flush=True)
    if sess.get_providers()[0] != "DmlExecutionProvider":
        print("RESULT INCONCLUSIVE raw: DirectML did not initialise, onnxruntime fell back to CPU", flush=True)
        return 3
    lock = threading.Lock()
    errors: list[str] = []
    done = [0]
    blob = np.random.default_rng(0).uniform(-1, 1, (1, 3, 256, 256)).astype(np.float32)
    reference = sess.run(None, {"input": blob})[0]

    def worker() -> None:
        for _ in range(runs):
            try:
                if use_lock:
                    with lock:
                        out = sess.run(None, {"input": blob})[0]
                else:
                    out = sess.run(None, {"input": blob})[0]
                if not np.allclose(out, reference, atol=1e-3):
                    errors.append("wrong result")
                done[0] += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{type(exc).__name__}: {exc}")

    start = time.perf_counter()
    pool = [threading.Thread(target=worker) for _ in range(threads)]
    for t in pool:
        t.start()
    for t in pool:
        t.join()
    elapsed = time.perf_counter() - start
    print(f"RESULT raw lock={use_lock} threads={threads} ok_runs={done[0]}/{threads * runs} "
          f"errors={len(errors)} time={elapsed:.1f}s", flush=True)
    for e in errors[:5]:
        print("  error:", e, flush=True)
    return 1 if errors else 0


def pipeline(models_dir: Path, image: Path, workdir: Path, device: str = "directml") -> int:
    import cv2

    from faceforge.core.hardware import detect_hardware
    from faceforge.core.models_processor import ModelsProcessor
    from faceforge.core.pipeline import FacePipeline, ProcessOptions, SwapContext
    from faceforge.core.presets import preset_settings
    from faceforge.core.video_processor import VideoJob, VideoProcessor, probe_video
    from faceforge.helpers import ffmpeg
    from faceforge.helpers.logger import setup_logging

    setup_logging(debug=False)
    hw = detect_hardware()
    mp = ModelsProcessor(models_dir, device=device, workers=2, max_loaded=4, hardware=hw)
    print(f"device={mp.device} adapter={mp.adapter_name!r} serialize={mp.serialize_gpu}", flush=True)
    assert mp.device == device, f"{device} not available"

    values = preset_settings("balanced", hw, device)
    options = ProcessOptions(
        detector=values["face_detector_model"], detector_size=values["face_detector_size"],
        swapper=values["face_swapper_model"], pixel_boost=values["face_swapper_pixel_boost"],
        enhancer=values["face_enhancer_model"], enhancer_blend=values["face_enhancer_blend"] / 100)
    print("options:", options, flush=True)

    pipe = FacePipeline(mp)
    img = cv2.imread(str(image))
    source = img[0:260, 860:1060]
    ctx = SwapContext(source_embedding=pipe.source_embedding([source], options))
    assert ctx.source_embedding is not None, "no face in source"

    # 3 faces instead of 6 keeps the run short on a CPU-emulated GPU while
    # still issuing many concurrent DirectML calls.
    frame = img[100:500, 230:900]
    cv2.imwrite(str(workdir / "frame.jpg"), frame)
    width = 1280
    height = int(frame.shape[0] * width / frame.shape[1]) // 2 * 2
    clip = workdir / "clip.mp4"
    result = ffmpeg.run(["-loglevel", "error", "-y", "-loop", "1", "-i", str(workdir / "frame.jpg"),
                         "-f", "lavfi", "-i", "sine=duration=2", "-t", "2", "-r", "8",
                         "-vf", f"scale={width}:{height},zoompan=z='1+0.003*on':d=1:s={width}x{height}:fps=8",
                         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(clip)])
    assert result.returncode == 0, result.stderr.decode()

    job = VideoJob(str(clip), workdir / "out.mp4", options, ctx, encoder="libx264", quality=80,
                   workers=2, low_end=True)
    last = [0]

    def progress(done, total, fps):
        last[0] = done
        if done % 4 == 0:
            print(f"  frame {done}/{total} fps={fps:.2f}", flush=True)

    start = time.perf_counter()
    output, _ = VideoProcessor(pipe).run(job, progress)
    elapsed = time.perf_counter() - start
    info = probe_video(str(output))
    if set(mp._session_device.values()) != {device}:
        print(f"RESULT INCONCLUSIVE pipeline: sessions ran on {sorted(set(mp._session_device.values()))}, "
              f"not {device}", flush=True)
        return 3
    print(f"RESULT pipeline serialize={mp.serialize_gpu} frames={info.frame_count} audio={info.has_audio} "
          f"time={elapsed:.1f}s fps={last[0] / elapsed:.2f}", flush=True)
    return 0 if info.frame_count == 16 and info.has_audio else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("raw", "pipeline"))
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--workdir", type=Path, default=Path("stress-out"))
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--runs", type=int, default=25)
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--device", default="directml", help="pipeline mode only (cpu = local smoke run)")
    args = parser.parse_args()
    args.workdir.mkdir(parents=True, exist_ok=True)
    if args.mode == "raw":
        return raw(args.models, args.threads, args.runs, args.lock)
    return pipeline(args.models, args.image, args.workdir, args.device)


if __name__ == "__main__":
    sys.exit(main())
