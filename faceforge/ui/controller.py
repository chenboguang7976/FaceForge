"""Application controller: owns the engine and runs all heavy work off the UI thread.

Threads
-------
- ``_analysis`` (1 worker): source/target face analysis and live previews.
  A single worker keeps weak machines responsive; stale preview requests
  are dropped (latest wins).
- a dedicated thread per render job (image batch or video).
- a thread for model downloads.

All results come back to the UI as Qt signals.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

import numpy as np
from PySide6.QtCore import QObject, QTimer, Signal

from faceforge.config import Settings
from faceforge.core.face import Face
from faceforge.core.hardware import detect_hardware, runtime_settings
from faceforge.core.models_data import MODELS
from faceforge.core.models_processor import ModelMissingError, ModelsProcessor
from faceforge.core.pipeline import (SELECT_REFERENCE, FacePipeline, ProcessOptions,
                                     SwapContext)
from faceforge.core.presets import PRESET_CUSTOM, PRESET_KEYS, preset_settings
from faceforge.core.video_processor import (JobCancelled, VideoJob, VideoProcessor, VideoInfo,
                                            probe_video, read_frame_at)
from faceforge.helpers.downloader import DownloadCancelled, download_model
from faceforge.helpers.image_io import is_image, is_video, read_image, unique_path, write_image
from faceforge.helpers.logger import get_logger
from faceforge.processors.face_recognizer import RECOGNIZER

log = get_logger(__name__)

KIND_NONE, KIND_IMAGE, KIND_VIDEO, KIND_BATCH = "none", "image", "video", "batch"
MAX_PREVIEW_SIDE = 1600


def _downscale(frame: np.ndarray, side: int = MAX_PREVIEW_SIDE) -> np.ndarray:
    import cv2

    h, w = frame.shape[:2]
    scale = side / max(h, w)
    if scale >= 1:
        return frame
    return cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


class Controller(QObject):
    source_changed = Signal()
    source_analyzed = Signal(int)                     # number of usable source faces
    target_changed = Signal()
    target_faces_changed = Signal(list)               # list[np.ndarray] thumbnails
    preview_ready = Signal(object, object, float)     # before, after, seconds
    preview_busy = Signal(bool)
    job_started = Signal(str)                         # kind
    job_progress = Signal(int, int, float)            # done, total, fps
    job_finished = Signal(str, int)                   # output path, resumed-from frame
    job_failed = Signal(str)
    job_cancelled = Signal()
    models_missing = Signal(list)                     # model keys
    download_progress = Signal(str, int, int)         # key, done, total
    download_finished = Signal(bool, str)             # ok, error
    model_loading = Signal(str, bool)
    message = Signal(str, str)                        # text, kind (info/success/warning/error)
    settings_applied = Signal()
    runtime_changed = Signal()                        # device / GPU actually in use changed
    _invoke = Signal(object, object)

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.hardware = detect_hardware()
        self.models = ModelsProcessor(settings.models_dir, settings.get("device"),
                                      settings.get("execution_workers"),
                                      settings.get("max_loaded_models"),
                                      settings.get("gpu_device_id"), self.hardware)
        self.models.on_warning = lambda text: self.message.emit(text, "warning")
        self.models.on_loading = lambda key, on: self.model_loading.emit(key, on)
        self.pipeline = FacePipeline(self.models)
        self.video = VideoProcessor(self.pipeline)

        self._invoke.connect(self._on_invoke)
        self._analysis = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ff-analysis")
        self._preview_gen = 0
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(250)
        self._preview_timer.timeout.connect(self._run_preview)
        self._pending_after_download: Callable[[], None] | None = None
        self._download_cancel = threading.Event()

        # Sources
        self.source_paths: list[str] = []
        self.source_images: list[np.ndarray] = []
        self.source_embedding: np.ndarray | None = None
        # Target
        self.target_paths: list[str] = []
        self.target_kind = KIND_NONE
        self.video_info: VideoInfo | None = None
        self.frame_index = 0
        self.target_frame: np.ndarray | None = None
        self.target_faces: list[Face] = []
        self.reference_index: int | None = None
        self.reference_embedding: np.ndarray | None = None
        self.last_output: str | None = None
        # Job
        self._job_thread: threading.Thread | None = None
        self._pause = threading.Event()
        self._cancel = threading.Event()

    # ------------------------------------------------------------- settings
    def options(self) -> ProcessOptions:
        return ProcessOptions.from_settings(self.settings)

    def set_option(self, key: str, value) -> None:
        if self.settings.get(key) == value:
            return
        self.settings.set(key, value)
        if key in PRESET_KEYS and self.settings.get("preset") != PRESET_CUSTOM:
            self.settings.set("preset", PRESET_CUSTOM)
            self.settings_applied.emit()
        if key == "device":
            # Parallel frames depend on the device: on a 4-thread CPU, 2 workers measured
            # slower than 1 (637 s vs 475 s for 90 frames of 1080p), on a GPU 2 help.
            from faceforge.core.hardware import resolve_device

            resolved = resolve_device(value, self.hardware)
            self.settings.set("execution_workers",
                              runtime_settings(self.hardware, resolved)["execution_workers"])
            self.settings_applied.emit()
        if key in ("device", "execution_workers", "max_loaded_models", "gpu_device_id"):
            self.apply_runtime()
        if key in ("face_detector_model", "face_detector_size", "face_detector_score"):
            self.analyze_target()
        self.request_preview()

    def apply_preset(self, name: str) -> None:
        values = preset_settings(name, self.hardware, self.models.device)
        self.settings.update(values)
        self.settings.set("preset", name)
        self.settings_applied.emit()
        self.analyze_target()
        self.request_preview()

    def apply_recommended_runtime(self) -> None:
        self.settings.update(runtime_settings(self.hardware, self.models.device))
        self.apply_runtime()
        self.settings_applied.emit()

    def apply_runtime(self) -> None:
        if self.is_busy():
            self.message.emit("error.busy", "warning")
            return
        self.models.models_dir = self.settings.models_dir
        self.models.configure(self.settings.get("device"), self.settings.get("execution_workers"),
                              self.settings.get("max_loaded_models"), self.settings.get("gpu_device_id"))
        self.runtime_changed.emit()
        self.request_preview()

    # --------------------------------------------------------------- models
    def _ensure(self, keys: list[str], then: Callable[[], None]) -> bool:
        missing = self.models.missing(keys)
        if not missing:
            return True
        self._pending_after_download = then
        self.models_missing.emit(missing)
        return False

    def download(self, keys: list[str]) -> None:
        self._download_cancel.clear()

        def work() -> None:
            try:
                for key in keys:
                    info = MODELS[key]
                    download_model(info, self.models.models_dir,
                                   lambda d, t, k=key: self.download_progress.emit(k, d, t),
                                   self._download_cancel)
                self.download_finished.emit(True, "")
            except DownloadCancelled:
                self.download_finished.emit(False, "")
            except Exception as exc:  # noqa: BLE001
                log.exception("Download failed")
                self.download_finished.emit(False, str(exc))

        threading.Thread(target=work, name="ff-download", daemon=True).start()

    def cancel_download(self) -> None:
        self._download_cancel.set()

    def resume_after_download(self, ok: bool) -> None:
        action, self._pending_after_download = self._pending_after_download, None
        if ok and action:
            action()

    # -------------------------------------------------------------- sources
    def add_sources(self, paths: list[str]) -> None:
        added = 0
        for path in paths:
            if not is_image(path) or path in self.source_paths:
                continue
            image = read_image(path)
            if image is None:
                continue
            self.source_paths.append(path)
            self.source_images.append(image)
            added += 1
        if added:
            self.source_changed.emit()
            self.analyze_sources()

    def remove_source(self, index: int) -> None:
        if 0 <= index < len(self.source_paths):
            del self.source_paths[index]
            del self.source_images[index]
            self.source_changed.emit()
            self.analyze_sources()

    def clear_sources(self) -> None:
        self.source_paths, self.source_images, self.source_embedding = [], [], None
        self.source_changed.emit()
        self.request_preview()

    def analyze_sources(self) -> None:
        options = self.options()
        if not self.source_images:
            self.source_embedding = None
            self.request_preview()
            return
        if not self._ensure([options.detector, RECOGNIZER], self.analyze_sources):
            return
        images = list(self.source_images)

        def work():
            return self.pipeline.source_embedding(images, options), len(images)

        def done(result):
            embedding, _ = result
            self.source_embedding = embedding
            self.source_analyzed.emit(0 if embedding is None else len(images))
            self.request_preview()

        self._submit(work, done)

    # --------------------------------------------------------------- target
    def set_targets(self, paths: list[str]) -> None:
        videos = [p for p in paths if is_video(p)]
        images = [p for p in paths if is_image(p)]
        if videos:
            self.target_paths, self.target_kind = [videos[0]], KIND_VIDEO
            self.video_info = probe_video(videos[0])
            if not self.video_info.width:
                self.message.emit("error.read_video", "error")
                self.clear_target()
                return
        elif images:
            self.target_paths = images
            self.target_kind = KIND_IMAGE if len(images) == 1 else KIND_BATCH
            self.video_info = None
        else:
            self.message.emit("error.unsupported", "warning")
            return
        self.frame_index = 0
        self.reference_index = None
        self.reference_embedding = None
        self._load_frame()
        self.target_changed.emit()
        self.analyze_target()
        self.request_preview(immediate=True)

    def clear_target(self) -> None:
        self.target_paths, self.target_kind = [], KIND_NONE
        self.video_info, self.target_frame, self.target_faces = None, None, []
        self.reference_index = self.reference_embedding = None
        self.target_changed.emit()
        self.target_faces_changed.emit([])

    def _load_frame(self) -> None:
        if self.target_kind == KIND_VIDEO:
            frame = read_frame_at(self.target_paths[0], self.frame_index)
        elif self.target_paths:
            frame = read_image(self.target_paths[0])
        else:
            frame = None
        if frame is None:
            self.message.emit("error.read_frame", "error")
        self.target_frame = frame

    def seek(self, index: int) -> None:
        if self.target_kind != KIND_VIDEO:
            return
        self.frame_index = index
        self._load_frame()
        self.analyze_target()
        self.request_preview()

    def analyze_target(self) -> None:
        frame = self.target_frame
        if frame is None:
            return
        options = self.options()
        if not self._ensure([options.detector, RECOGNIZER], self.analyze_target):
            return

        def work():
            faces = self.pipeline.detect(frame, options, with_embeddings=True)
            return faces, [f.crop_thumbnail(frame, 96) for f in faces]

        def done(result):
            faces, thumbs = result
            self.target_faces = faces
            # Keep following the chosen person when scrubbing through a video.
            if self.reference_embedding is not None and faces:
                best = min(range(len(faces)), key=lambda i: faces[i].distance(self.reference_embedding))
                self.reference_index = best if faces[best].distance(self.reference_embedding) < 0.8 else None
            else:
                self.reference_index = None
            self.target_faces_changed.emit(thumbs)

        self._submit(work, done)

    def select_reference(self, index: int | None) -> None:
        if index is None or not (0 <= index < len(self.target_faces)):
            self.reference_index, self.reference_embedding = None, None
        else:
            self.reference_index = index
            self.reference_embedding = self.target_faces[index].embedding
            if self.settings.get("face_selector_mode") != SELECT_REFERENCE:
                self.settings.set("face_selector_mode", SELECT_REFERENCE)
                self.settings_applied.emit()
        self.request_preview()

    # -------------------------------------------------------------- preview
    def request_preview(self, immediate: bool = False) -> None:
        if self.target_frame is None:
            return
        self._preview_timer.start(0 if immediate else 250)

    def _context(self) -> SwapContext:
        return SwapContext(source_embedding=self.source_embedding,
                           reference_embedding=self.reference_embedding)

    def _run_preview(self) -> None:
        frame = self.target_frame
        if frame is None or self.is_busy():
            return
        options = self.options()
        if options.swap_enabled and self.source_embedding is None and not options.enhancer:
            self.preview_ready.emit(frame, None, 0.0)
            return
        keys = self.pipeline.required_models(options)
        if options.selector == SELECT_REFERENCE:
            keys.append(RECOGNIZER)
        if not self._ensure(keys, lambda: self.request_preview(True)):
            self.preview_ready.emit(frame, None, 0.0)
            return
        self._preview_gen += 1
        gen = self._preview_gen
        ctx = self._context()
        small = _downscale(frame)
        self.preview_busy.emit(True)

        def work():
            if gen != self._preview_gen:
                return None
            self.pipeline.prepare(options)
            for key in keys:  # load first so the timing shows processing only
                self.models.session(key)
            start = time.perf_counter()
            # Process at full resolution so the preview matches the final output.
            result = self.pipeline.process_frame(frame, ctx, options)
            return result, time.perf_counter() - start

        def done(result):
            if gen != self._preview_gen:
                return
            self.preview_busy.emit(False)
            if result is None:
                return
            after, seconds = result
            self.preview_ready.emit(small, _downscale(after), seconds)

        self._submit(work, done, lambda: self.preview_busy.emit(False))

    def _submit(self, work: Callable, done: Callable, on_error: Callable | None = None) -> None:
        def run():
            try:
                result = work()
            except ModelMissingError as exc:
                self.models_missing.emit(list(exc.keys))
                if on_error:
                    on_error()
                return
            except Exception as exc:  # noqa: BLE001
                log.exception("Background task failed")
                self.message.emit(f"{type(exc).__name__}: {exc}", "error")
                if on_error:
                    on_error()
                return
            self._deliver(done, result)

        self._analysis.submit(run)

    def _deliver(self, callback: Callable, result) -> None:
        # The controller lives on the UI thread, so this emit is queued there.
        try:
            self._invoke.emit(callback, result)
        except RuntimeError:  # app is shutting down; nobody is listening any more
            pass

    def _on_invoke(self, callback, result) -> None:
        callback(result)

    # ------------------------------------------------------------------ jobs
    def is_busy(self) -> bool:
        return self._job_thread is not None and self._job_thread.is_alive()

    def can_start(self) -> str | None:
        """Return an i18n key describing why we can't start, or None."""
        options = self.options()
        if self.target_kind == KIND_NONE:
            return "error.no_target"
        if options.swap_enabled and self.source_embedding is None:
            return "error.no_source"
        if not options.swap_enabled and not options.enhancer:
            return "error.nothing_to_do"
        if options.selector == SELECT_REFERENCE and self.reference_embedding is None:
            return "error.no_reference"
        return None

    def start_job(self) -> None:
        reason = self.can_start()
        if reason:
            self.message.emit(reason, "warning")
            return
        options = self.options()
        keys = self.pipeline.required_models(options)
        if options.selector == SELECT_REFERENCE:
            keys.append(RECOGNIZER)
        if not self._ensure(keys, self.start_job):
            return
        self._pause.clear()
        self._cancel.clear()
        ctx = self._context()
        kind = self.target_kind
        target = self._job_video if kind == KIND_VIDEO else self._job_images
        self._job_thread = threading.Thread(target=target, args=(options, ctx), name="ff-job", daemon=True)
        self.job_started.emit(kind)
        self._job_thread.start()

    def _output_path(self, src: str, ext: str) -> Path:
        out_dir = self.settings.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        return unique_path(out_dir / f"{Path(src).stem}_faceforge{ext}")

    def _job_images(self, options: ProcessOptions, ctx: SwapContext) -> None:
        paths = list(self.target_paths)
        fmt = self.settings.get("output_image_format")
        quality = self.settings.get("output_image_quality")
        last = None
        try:
            self.pipeline.prepare(options)
            start = time.perf_counter()
            for index, path in enumerate(paths):
                if self._cancel.is_set():
                    raise JobCancelled()
                while self._pause.is_set() and not self._cancel.is_set():
                    time.sleep(0.1)
                frame = read_image(path)
                if frame is None:
                    log.warning("Skipping unreadable image %s", path)
                    continue
                result = self.pipeline.process_frame(frame, ctx, options)
                last = self._output_path(path, f".{fmt}")
                write_image(last, result, quality)
                elapsed = time.perf_counter() - start
                self.job_progress.emit(index + 1, len(paths), (index + 1) / elapsed if elapsed else 0.0)
            if last is None:
                raise RuntimeError("No images could be processed")
            self.last_output = str(last if len(paths) == 1 else last.parent)
            self.job_finished.emit(self.last_output, 0)
        except JobCancelled:
            self.job_cancelled.emit()
        except Exception as exc:  # noqa: BLE001
            log.exception("Image job failed")
            self.job_failed.emit(str(exc))

    def _job_video(self, options: ProcessOptions, ctx: SwapContext) -> None:
        src = self.target_paths[0]
        job = VideoJob(
            input_path=src,
            output_path=self._output_path(src, ".mp4"),
            options=options, context=ctx,
            encoder=self.settings.get("output_video_encoder"),
            quality=self.settings.get("output_video_quality"),
            keep_audio=self.settings.get("keep_audio"),
            workers=self.models.workers,
            low_end=self.settings.get("performance_profile") == "low",
        )
        try:
            output, resumed = self.video.run(job, self.job_progress.emit, self._pause, self._cancel)
            self.last_output = str(output)
            self.job_finished.emit(str(output), resumed)
        except JobCancelled:
            self.job_cancelled.emit()
        except Exception as exc:  # noqa: BLE001
            log.exception("Video job failed")
            self.job_failed.emit(str(exc))

    def pause(self, paused: bool) -> None:
        if paused:
            self._pause.set()
        else:
            self._pause.clear()

    def stop(self) -> None:
        self._cancel.set()
        self._pause.clear()

    # ----------------------------------------------------------------- misc
    @staticmethod
    def open_path(path: str | Path) -> None:
        path = str(path)
        try:
            if sys.platform == "win32":
                os.startfile(path)  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except OSError as exc:
            log.warning("Could not open %s: %s", path, exc)

    def shutdown(self) -> None:
        self.stop()
        self.cancel_download()
        if self._job_thread is not None:
            self._job_thread.join(timeout=5)
        self._analysis.shutdown(wait=False, cancel_futures=True)
        self.models.unload_all()
