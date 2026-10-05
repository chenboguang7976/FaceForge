"""Video processing: decode → parallel face processing → ordered encode.

- Frames are encoded straight into FFmpeg through a pipe (no thousands of
  temporary JPEGs on disk), using a hardware encoder (NVENC / QuickSync /
  AMF / VideoToolbox) when one works, so the CPU stays free for inference.
- Output is written in segments; a job that is cancelled or crashes resumes
  from the last finished segment next time the same video is processed with
  the same settings.
- The original audio track is muxed back at the end.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

import cv2
import numpy as np

from faceforge.core.pipeline import FacePipeline, ProcessOptions, SwapContext
from faceforge.helpers import ffmpeg
from faceforge.helpers.logger import get_logger
from faceforge.helpers.paths import temp_dir

log = get_logger(__name__)

SEGMENT_FRAMES = 300


class JobCancelled(Exception):
    pass


@dataclass
class VideoInfo:
    width: int
    height: int
    fps: float
    frame_count: int
    has_audio: bool

    @property
    def duration(self) -> float:
        return self.frame_count / self.fps if self.fps else 0.0


# --------------------------------------------------------------------- reading
def _open_capture(path: str) -> cv2.VideoCapture | None:
    cap = cv2.VideoCapture(path)
    if cap.isOpened():
        return cap
    cap.release()
    return None


def probe_video(path: str) -> VideoInfo:
    meta = ffmpeg.probe_media(path)
    cap = _open_capture(path)
    if cap is not None:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or meta["fps"]
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
    else:
        width, height, fps, count = meta["width"], meta["height"], meta["fps"], 0
    fps = fps if fps and fps < 1000 else 25.0
    if count <= 0 and meta["duration"]:
        count = int(meta["duration"] * fps)
    return VideoInfo(width, height, float(fps), max(0, count), bool(meta["has_audio"]))


def read_frame_at(path: str, index: int) -> np.ndarray | None:
    """Random access for previews and scrubbing."""
    cap = _open_capture(path)
    if cap is not None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, index))
        ok, frame = cap.read()
        cap.release()
        if ok:
            return frame
    # Fallback (e.g. non-ASCII paths on Windows): let ffmpeg seek and decode one frame.
    info = probe_video(path)
    if not info.width:
        return None
    seconds = index / info.fps if info.fps else 0
    try:
        out = ffmpeg.run(["-loglevel", "error", "-ss", f"{seconds:.3f}", "-i", path, "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], timeout=60).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    if len(out) < info.width * info.height * 3:
        return None
    return np.frombuffer(out[: info.width * info.height * 3], np.uint8).reshape(info.height, info.width, 3).copy()


def iter_frames(path: str, info: VideoInfo, start: int = 0) -> Iterator[np.ndarray]:
    cap = _open_capture(path)
    if cap is not None:
        try:
            for _ in range(start):  # grab() decodes without converting: exact and cheap
                if not cap.grab():
                    return
            while True:
                ok, frame = cap.read()
                if not ok:
                    return
                yield frame
        finally:
            cap.release()
        return

    exe = ffmpeg.find_ffmpeg()
    if not exe:
        raise RuntimeError("ffmpeg not found")
    proc = subprocess.Popen(
        [exe, "-hide_banner", "-loglevel", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, **ffmpeg.popen_kwargs())
    frame_bytes = info.width * info.height * 3
    try:
        index = 0
        while True:
            data = proc.stdout.read(frame_bytes)
            if len(data) < frame_bytes:
                return
            if index >= start:
                yield np.frombuffer(data, np.uint8).reshape(info.height, info.width, 3).copy()
            index += 1
    finally:
        proc.kill()
        proc.wait()


# --------------------------------------------------------------------- writing
class FFmpegWriter:
    def __init__(self, path: Path, width: int, height: int, fps: float, codec_args: list[str]):
        exe = ffmpeg.find_ffmpeg()
        if not exe:
            raise RuntimeError("ffmpeg not found")
        self.path = path
        self._log_path = path.with_suffix(".log")
        self._log = open(self._log_path, "wb")
        cmd = [exe, "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{width}x{height}", "-r", f"{fps:.6f}",
               "-i", "-", "-an", *codec_args,
               "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-pix_fmt", "yuv420p", str(path)]
        self._proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                      stderr=self._log, **ffmpeg.popen_kwargs())

    def write(self, frame: np.ndarray) -> None:
        try:
            self._proc.stdin.write(np.ascontiguousarray(frame).tobytes())
        except (BrokenPipeError, OSError) as exc:
            raise RuntimeError(f"Video encoder stopped: {self._error_text()}") from exc

    def _error_text(self) -> str:
        try:
            self._log.flush()
            return self._log_path.read_text("utf-8", "ignore").strip()[-500:]
        except OSError:
            return ""

    def close(self) -> None:
        try:
            if self._proc.stdin and not self._proc.stdin.closed:
                self._proc.stdin.close()
        except OSError:
            pass
        code = self._proc.wait()
        self._log.close()
        if code != 0:
            raise RuntimeError(f"Video encoder failed: {self._error_text()}")
        self._log_path.unlink(missing_ok=True)

    def abort(self) -> None:
        self._proc.kill()
        self._proc.wait()
        self._log.close()
        self.path.unlink(missing_ok=True)
        self._log_path.unlink(missing_ok=True)


# ------------------------------------------------------------------------ job
@dataclass
class VideoJob:
    input_path: str
    output_path: Path
    options: ProcessOptions
    context: SwapContext
    encoder: str = "auto"
    quality: int = 80
    keep_audio: bool = True
    workers: int = 2
    low_end: bool = False
    max_frames: int | None = None  # diagnostics: stop after this many frames
    resume: bool = True            # diagnostics: never reuse segments from another run

    def fingerprint(self) -> str:
        """Identifies 'the same work' for resuming: input file, settings and identities."""
        src = Path(self.input_path)
        stat = src.stat()
        h = hashlib.sha1()
        h.update(f"{src.resolve()}|{stat.st_size}|{stat.st_mtime_ns}|{self.options!r}|"
                 f"{self.encoder}|{self.quality}|{self.max_frames}".encode())
        for emb in (self.context.source_embedding, self.context.reference_embedding):
            if emb is not None:
                h.update(np.round(emb, 4).tobytes())
        return h.hexdigest()[:16]


ProgressFn = Callable[[int, int, float], None]


class VideoProcessor:
    def __init__(self, pipeline: FacePipeline):
        self.pipeline = pipeline

    @staticmethod
    def pick_encoder(requested: str) -> str:
        available = ffmpeg.available_encoders()
        if requested != "auto" and requested in available:
            return requested
        return available[0] if available else "libx264"

    def run(self, job: VideoJob, progress: ProgressFn | None = None,
            pause: threading.Event | None = None, cancel: threading.Event | None = None) -> tuple[Path, int]:
        """Process ``job``. Returns (output path, frame index it resumed from)."""
        info = probe_video(job.input_path)
        if not info.width:
            raise RuntimeError("Unable to read video")
        encoder = self.pick_encoder(job.encoder)
        codec_args = ffmpeg.encoder_args(encoder, job.quality, job.low_end)
        log.info("Video %dx%d @ %.2f fps, %d frames, encoder %s", info.width, info.height,
                 info.fps, info.frame_count, encoder)

        if job.resume:
            job_dir = temp_dir() / "jobs" / job.fingerprint()
        else:
            import uuid

            job_dir = temp_dir() / "jobs" / f"fresh-{uuid.uuid4().hex[:12]}"
        job_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = job_dir / "manifest.json"
        manifest = {"done": []}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text("utf-8"))
            except (OSError, json.JSONDecodeError):
                manifest = {"done": []}
        done_segments = sorted(int(i) for i in manifest.get("done", [])
                               if (job_dir / f"seg_{int(i):05d}.mp4").exists())
        # Only a contiguous run of finished segments from the start can be reused.
        first_todo = 0
        while first_todo in done_segments:
            first_todo += 1
        start_frame = first_todo * SEGMENT_FRAMES

        self.pipeline.prepare(job.options)
        total = info.frame_count
        processed = start_frame
        window: deque[float] = deque(maxlen=30)

        def process(frame: np.ndarray) -> np.ndarray:
            return self.pipeline.process_frame(frame, job.context, job.options)

        writer: FFmpegWriter | None = None
        segment = first_todo
        frame_index = start_frame
        pending: deque = deque()
        max_inflight = max(2, job.workers * 2)

        def finish_segment() -> None:
            nonlocal writer
            if writer is None:
                return
            writer.close()
            writer = None
            done = sorted(set(done_segments) | {segment})
            done_segments[:] = done
            manifest_path.write_text(json.dumps({"done": done}), "utf-8")

        def write_next() -> None:
            nonlocal writer, segment, processed
            result = pending.popleft().result()
            target_segment = processed // SEGMENT_FRAMES
            if target_segment != segment:
                finish_segment()
                segment = target_segment
            if writer is None:
                writer = FFmpegWriter(job_dir / f"seg_{segment:05d}.mp4", info.width, info.height,
                                      info.fps, codec_args)
            writer.write(result)
            processed += 1
            window.append(time.perf_counter())
            if progress:
                # The first frames arrive in a burst from the pipeline buffer, so
                # wait for a few samples before showing a (meaningful) rate.
                span = window[-1] - window[0]
                fps = (len(window) - 1) / span if len(window) >= 8 and span > 0 else 0.0
                progress(processed, max(total, processed), fps)

        try:
            with ThreadPoolExecutor(max_workers=max(1, job.workers),
                                    thread_name_prefix="ff-frame") as pool:
                for frame in iter_frames(job.input_path, info, start_frame):
                    if job.max_frames is not None and frame_index >= job.max_frames:
                        break
                    while pause is not None and pause.is_set():
                        if cancel is not None and cancel.is_set():
                            break
                        time.sleep(0.1)
                    if cancel is not None and cancel.is_set():
                        raise JobCancelled()
                    pending.append(pool.submit(process, frame))
                    frame_index += 1
                    while len(pending) >= max_inflight:
                        write_next()
                while pending:
                    if cancel is not None and cancel.is_set():
                        raise JobCancelled()
                    write_next()
            finish_segment()
        except BaseException:
            for fut in pending:
                fut.cancel()
            if writer is not None:
                writer.abort()  # the unfinished segment is redone on resume
            raise

        output = self._concat(job, info, job_dir, done_segments)
        shutil.rmtree(job_dir, ignore_errors=True)
        return output, start_frame

    def _concat(self, job: VideoJob, info: VideoInfo, job_dir: Path, segments: list[int]) -> Path:
        if not segments:
            raise RuntimeError("No frames were decoded from the video")
        list_file = job_dir / "segments.txt"
        list_file.write_text("".join(f"file 'seg_{i:05d}.mp4'\n" for i in segments), "utf-8")
        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_out = job_dir / f"final{job.output_path.suffix or '.mp4'}"

        base = ["-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file)]
        with_audio = job.keep_audio and info.has_audio
        attempts = []
        if with_audio:
            attempts.append([*base, "-i", job.input_path, "-map", "0:v:0", "-map", "1:a:0?",
                             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                             "-movflags", "+faststart", str(tmp_out)])
        attempts.append([*base, "-map", "0:v:0", "-c:v", "copy", "-movflags", "+faststart", str(tmp_out)])

        error = ""
        for args in attempts:
            result = ffmpeg.run(args, timeout=None)
            if result.returncode == 0:
                shutil.move(str(tmp_out), str(job.output_path))
                return job.output_path
            error = result.stderr.decode("utf-8", "ignore")[-500:]
            log.warning("Muxing failed, retrying without audio: %s", error)
        raise RuntimeError(f"Could not assemble the output video: {error}")
