"""ONNX Runtime session manager.

- No PyTorch: inputs/outputs are plain numpy arrays.
- Picks an execution provider (CUDA → DirectML → CPU) and falls back to CPU
  if a model fails to load on the GPU, instead of crashing.
- Keeps at most ``max_loaded`` sessions alive (least-recently-used eviction),
  which is what keeps a 4 GB GPU / 8 GB RAM machine out of memory.
- Disables ORT's busy-wait spinning so idle worker threads don't steal CPU
  time from decoding, encoding and the UI on 4-core CPUs.
"""
from __future__ import annotations

import gc
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Callable

import numpy as np

from faceforge.core.hardware import HardwareInfo, detect_hardware, resolve_device
from faceforge.core.models_data import MODELS, ModelInfo
from faceforge.helpers.logger import get_logger

log = get_logger(__name__)

try:
    import onnxruntime as ort

    ort.set_default_logger_severity(3)
except ImportError:  # pragma: no cover
    ort = None

_ORT_TYPES = {
    "tensor(float)": np.float32,
    "tensor(float16)": np.float16,
    "tensor(double)": np.float64,
    "tensor(int64)": np.int64,
    "tensor(int32)": np.int32,
}


_PROVIDER_DEVICE = {
    "CUDAExecutionProvider": "cuda",
    "DmlExecutionProvider": "directml",
    "CoreMLExecutionProvider": "coreml",
    "CPUExecutionProvider": "cpu",
}


class ModelMissingError(RuntimeError):
    def __init__(self, keys: list[str]):
        super().__init__("Missing models: " + ", ".join(keys))
        self.keys = keys


class ModelsProcessor:
    """Loads, caches and runs ONNX models. Safe to call from worker threads."""

    def __init__(self, models_dir: str | Path, device: str = "auto", workers: int = 2,
                 max_loaded: int = 3, gpu_device_id: int = -1,
                 hardware: HardwareInfo | None = None):
        if ort is None:
            raise RuntimeError("onnxruntime is not installed")
        self.hardware = hardware or detect_hardware()
        self.models_dir = Path(models_dir)
        self._sessions: OrderedDict[str, "ort.InferenceSession"] = OrderedDict()
        self._session_device: dict[str, str] = {}
        self._lock = threading.RLock()
        self._load_locks: dict[str, threading.Lock] = {}
        self._pinned: set[str] = set()
        self.fallbacks: dict[str, str] = {}   # model key -> device actually used, when not self.device
        # DirectML/CoreML sessions are not safe to Run from several threads at
        # once. Measured on a GTX 1050 (2026-10-06): unlocked
        # concurrent runs -> 8/100 failed calls and an access violation
        # (0xC0000005) in a 2-worker video job; serialized -> 100/100 and the
        # same job completes, slightly faster than 1 worker (74.5s vs 81.1s).
        # CPU pre/post-processing still runs in parallel.
        self._gpu_run_lock = threading.Lock()
        self._cuda_dlls_loaded = False
        self.on_warning: Callable[[str], None] | None = None
        self.on_loading: Callable[[str, bool], None] | None = None
        self.configure(device, workers, max_loaded, gpu_device_id)

    # ------------------------------------------------------------------ config
    def configure(self, device: str, workers: int, max_loaded: int, gpu_device_id: int = -1) -> None:
        resolved = resolve_device(device, self.hardware)
        with self._lock:
            changed = (getattr(self, "device", None) != resolved
                       or getattr(self, "gpu_device_id", None) != gpu_device_id)
            self.requested_device = device
            self.device = resolved
            self.gpu_device_id = gpu_device_id
            self.workers = max(1, int(workers))
            self.max_loaded = max(1, int(max_loaded))
        if changed:
            self.unload_all()
        self._trim()
        log.info("Execution device: %s (requested %s), workers=%d, max models=%d",
                 self.device, device, self.workers, self.max_loaded)

    def dml_adapter_index(self) -> int:
        """Requested adapter if valid, otherwise the best one (-1 = automatic)."""
        indexes = {a.index for a in self.hardware.dml_adapters}
        if self.gpu_device_id >= 0 and (not indexes or self.gpu_device_id in indexes):
            return self.gpu_device_id
        best = self.hardware.best_dml_adapter
        return best.index if best else 0

    @property
    def adapter_name(self) -> str:
        """Human-readable name of the GPU actually used."""
        if self.device == "directml":
            index = self.dml_adapter_index()
            for adapter in self.hardware.dml_adapters:
                if adapter.index == index:
                    return adapter.name
            return f"GPU {index}"
        if self.device == "cuda":
            gpus = self.hardware.nvidia_gpus
            index = max(0, self.gpu_device_id)
            return gpus[index].name if index < len(gpus) else "NVIDIA GPU"
        return ""

    @property
    def device_label(self) -> str:
        return {"cuda": "CUDA", "directml": "DirectML", "coreml": "CoreML", "cpu": "CPU"}[self.device]

    # ------------------------------------------------------------------- files
    def path(self, key: str) -> Path:
        return self.models_dir / MODELS[key].file

    def is_available(self, key: str) -> bool:
        info: ModelInfo = MODELS[key]
        p = self.path(key)
        return p.is_file() and p.stat().st_size == info.size

    def missing(self, keys: list[str]) -> list[str]:
        return [k for k in dict.fromkeys(keys) if not self.is_available(k)]

    # ---------------------------------------------------------------- sessions
    def _providers(self, device: str) -> list:
        if device == "cuda":
            options = {
                "device_id": max(0, self.gpu_device_id),
                "arena_extend_strategy": "kSameAsRequested",
                "cudnn_conv_algo_search": "HEURISTIC",
            }
            gpu = self.hardware.primary_gpu
            if gpu and gpu.vram_mb:
                # Leave headroom for the display and the CUDA context.
                options["gpu_mem_limit"] = max(1024, gpu.vram_mb - 768) * 2**20
            return [("CUDAExecutionProvider", options), "CPUExecutionProvider"]
        if device == "directml":
            # An explicit DXGI index: on dual-GPU laptops index 0 is usually the
            # integrated GPU, so never rely on the default.
            return [("DmlExecutionProvider", {"device_id": self.dml_adapter_index()}),
                    "CPUExecutionProvider"]
        if device == "coreml":
            return ["CoreMLExecutionProvider", "CPUExecutionProvider"]
        return ["CPUExecutionProvider"]

    def _session_options(self, device: str) -> "ort.SessionOptions":
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.log_severity_level = 3
        threads = self.hardware.cpu_threads
        if device == "cpu":
            opts.intra_op_num_threads = max(1, threads // self.workers)
        else:
            opts.intra_op_num_threads = 2 if threads <= 4 else 4
        opts.inter_op_num_threads = 1
        opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
        opts.add_session_config_entry("session.inter_op.allow_spinning", "0")
        if device == "directml":
            opts.enable_mem_pattern = False
            opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        return opts

    def _create_session(self, key: str, device: str) -> "ort.InferenceSession":
        if device == "cuda" and not self._cuda_dlls_loaded:
            self._cuda_dlls_loaded = True
            preload = getattr(ort, "preload_dlls", None)
            if preload:
                try:  # Finds CUDA/cuDNN installed via pip (nvidia-* wheels).
                    preload()
                except Exception as exc:  # noqa: BLE001
                    log.debug("preload_dlls failed: %s", exc)
        path = str(self.path(key))
        providers = self._providers(device)
        return ort.InferenceSession(path, sess_options=self._session_options(device), providers=providers)

    def session(self, key: str) -> "ort.InferenceSession":
        with self._lock:
            sess = self._sessions.get(key)
            if sess is not None:
                self._sessions.move_to_end(key)
                return sess
            load_lock = self._load_locks.setdefault(key, threading.Lock())

        with load_lock:  # one thread loads; others wait for the same model
            with self._lock:
                if key in self._sessions:
                    self._sessions.move_to_end(key)
                    return self._sessions[key]
            if not self.is_available(key):
                raise ModelMissingError([key])

            if self.on_loading:
                self.on_loading(key, True)
            device = self.device
            try:
                try:
                    sess = self._create_session(key, device)
                except Exception as exc:  # noqa: BLE001
                    if device == "cpu":
                        raise
                    log.warning("Loading %s on %s failed (%s); using CPU.", key, device, exc)
                    if self.on_warning:
                        self.on_warning(f"{MODELS[key].title}: {device} → CPU")
                    device = "cpu"
                    sess = self._create_session(key, device)
            finally:
                if self.on_loading:
                    self.on_loading(key, False)

            active = sess.get_providers()[0]
            log.info("Loaded %s [%s]", key, active)
            # onnxruntime silently falls back to CPU when a GPU provider fails to
            # initialise (e.g. DirectML "display adapter handle is invalid"), so
            # record what actually runs instead of what was requested.
            actual = _PROVIDER_DEVICE.get(active, "cpu")
            if actual != device:
                log.warning("%s: requested %s but onnxruntime is using %s", key, device, active)
                if self.on_warning:
                    self.on_warning(f"{MODELS[key].title}: {device} → {actual}")
            with self._lock:
                self._sessions[key] = sess
                self._session_device[key] = actual
                if actual != self.device:
                    self.fallbacks[key] = actual
                else:
                    self.fallbacks.pop(key, None)
            if self.on_loading:  # again, now that the actual device is recorded
                self.on_loading(key, False)
            self._trim()
            return sess

    def pin(self, keys: list[str]) -> None:
        """Models the current pipeline needs every frame; never evicted, so the
        cache can't thrash (reload a model per frame) when the limit is small."""
        with self._lock:
            self._pinned = set(keys)
        self._trim()

    def _trim(self) -> None:
        evicted = False
        with self._lock:
            limit = max(self.max_loaded, len(self._pinned))
            for key in list(self._sessions):
                if len(self._sessions) <= limit:
                    break
                if key in self._pinned:
                    continue
                del self._sessions[key]
                self._session_device.pop(key, None)
                self.fallbacks.pop(key, None)
                log.info("Unloaded %s (cache limit %d)", key, limit)
                evicted = True
        if evicted:
            gc.collect()

    def unload_all(self) -> None:
        with self._lock:
            self._sessions.clear()
            self._session_device.clear()
            self.fallbacks.clear()
        gc.collect()

    def loaded(self) -> list[str]:
        with self._lock:
            return list(self._sessions)

    # ------------------------------------------------------------------- run
    def input_shape(self, key: str, index: int = 0) -> list:
        return self.session(key).get_inputs()[index].shape

    def run(self, key: str, feeds: dict[str, np.ndarray]) -> list[np.ndarray]:
        """Run a model, casting each input to the dtype the model expects."""
        sess = self.session(key)
        typed = {}
        for meta in sess.get_inputs():
            if meta.name not in feeds:
                continue
            dtype = _ORT_TYPES.get(meta.type, np.float32)
            value = np.asarray(feeds[meta.name])
            typed[meta.name] = value if value.dtype == dtype else value.astype(dtype)
        if self._session_device.get(key) in ("directml", "coreml"):
            with self._gpu_run_lock:
                outputs = sess.run(None, typed)
        else:
            outputs = sess.run(None, typed)
        return [o.astype(np.float32) if o.dtype == np.float16 else o for o in outputs]
