"""Hardware detection and performance profiles.

The profile decides sensible defaults (detector, model precision, number of
cached models, worker threads) so that weak machines — e.g. a 4-core laptop
with 8 GB RAM and a 4 GB GTX 1050 — stay responsive.
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from functools import lru_cache

import psutil

from faceforge.helpers.ffmpeg import popen_kwargs
from faceforge.helpers.logger import get_logger

log = get_logger(__name__)

try:
    import onnxruntime as ort
except ImportError:  # pragma: no cover - reported in the UI
    ort = None


def _ort_version() -> tuple[int, int]:
    try:
        major, minor = ort.__version__.split(".")[:2]
        return int(major), int(minor)
    except (AttributeError, ValueError):
        return (0, 0)


@dataclass
class GpuInfo:
    name: str
    vram_mb: int = 0
    compute_capability: float = 0.0  # NVIDIA only

    @property
    def supports_fast_fp16(self) -> bool:
        # Pascal (6.x) consumer cards run FP16 at a fraction of FP32 speed.
        return self.compute_capability >= 7.0


@dataclass
class HardwareInfo:
    os_name: str
    cpu_name: str
    cpu_threads: int
    cpu_cores: int
    ram_mb: int
    nvidia_gpus: list[GpuInfo] = field(default_factory=list)
    providers: list[str] = field(default_factory=list)

    @property
    def primary_gpu(self) -> GpuInfo | None:
        return max(self.nvidia_gpus, key=lambda g: g.vram_mb, default=None)

    @property
    def has_cuda(self) -> bool:
        if not self.nvidia_gpus or "CUDAExecutionProvider" not in self.providers:
            return False
        gpu = self.primary_gpu
        # onnxruntime-gpu >= 1.27 is built on CUDA 13, which dropped Maxwell,
        # Pascal and Volta (e.g. GTX 1050). Those GPUs use DirectML/CPU instead.
        if gpu and gpu.compute_capability and gpu.compute_capability < 7.5 and _ort_version() >= (1, 27):
            return False
        return True

    @property
    def has_directml(self) -> bool:
        return "DmlExecutionProvider" in self.providers

    @property
    def has_coreml(self) -> bool:
        return "CoreMLExecutionProvider" in self.providers

    def summary(self) -> str:
        gpu = self.primary_gpu
        gpu_text = f"{gpu.name} ({gpu.vram_mb // 1024} GB)" if gpu else "—"
        return (f"{self.cpu_name} · {self.cpu_cores}C/{self.cpu_threads}T · "
                f"RAM {round(self.ram_mb / 1024)} GB · GPU {gpu_text}")


def _query_nvidia() -> list[GpuInfo]:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,compute_cap",
             "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=8, **popen_kwargs(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    gpus = []
    for line in out.stdout.decode("utf-8", "ignore").splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            continue
        try:
            vram = int(float(parts[1]))
        except ValueError:
            vram = 0
        try:
            cc = float(parts[2]) if len(parts) > 2 else 0.0
        except ValueError:
            cc = 0.0
        gpus.append(GpuInfo(name=parts[0], vram_mb=vram, compute_capability=cc))
    return gpus


def _cpu_name() -> str:
    name = platform.processor() or ""
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/cpuinfo", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except OSError:
            pass
    elif sys.platform == "darwin":
        try:
            out = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
            name = out.stdout.decode().strip() or name
        except OSError:
            pass
    return name or platform.machine()


@lru_cache(maxsize=1)
def detect_hardware() -> HardwareInfo:
    providers = ort.get_available_providers() if ort else []
    info = HardwareInfo(
        os_name=f"{platform.system()} {platform.release()}",
        cpu_name=_cpu_name(),
        cpu_threads=os.cpu_count() or 1,
        cpu_cores=psutil.cpu_count(logical=False) or os.cpu_count() or 1,
        ram_mb=int(psutil.virtual_memory().total / 2**20),
        nvidia_gpus=_query_nvidia(),
        providers=providers,
    )
    log.info("Hardware: %s | providers: %s", info.summary(), ", ".join(providers))
    return info


# ---------------------------------------------------------------------------
# Performance profiles
# ---------------------------------------------------------------------------
PROFILE_LOW = "low"
PROFILE_MEDIUM = "medium"
PROFILE_HIGH = "high"


def classify(info: HardwareInfo) -> str:
    gpu = info.primary_gpu
    gpu_accel = info.has_cuda or info.has_directml or info.has_coreml
    if info.ram_mb <= 9 * 1024 or (gpu and gpu.vram_mb <= 4096) or not gpu_accel:
        return PROFILE_LOW
    if info.ram_mb <= 17 * 1024 or (gpu and gpu.vram_mb <= 8192):
        return PROFILE_MEDIUM
    return PROFILE_HIGH


def resolve_device(requested: str, info: HardwareInfo) -> str:
    """Turn the ``device`` setting (``auto``/``cuda``/``directml``/``coreml``/``cpu``)
    into a device that is actually available."""
    available = {
        "cuda": info.has_cuda,
        "directml": info.has_directml,
        "coreml": info.has_coreml,
        "cpu": True,
    }
    if requested != "auto" and available.get(requested):
        return requested
    if info.has_cuda:
        return "cuda"
    if info.has_directml:
        return "directml"
    # CoreML compiles every model on load and doesn't support every op used
    # here; the Apple CPU path is fast and predictable, so it's the default.
    return "cpu"


def runtime_settings(info: HardwareInfo, device: str) -> dict:
    """Threading/caching limits that depend only on the machine, not on quality."""
    profile = classify(info)
    workers = {PROFILE_LOW: 2, PROFILE_MEDIUM: 3, PROFILE_HIGH: 4}[profile]
    if device == "cpu":
        # On CPU, fewer parallel frames with more threads each avoids thrashing.
        workers = 1 if info.cpu_threads <= 4 else 2
    max_models = {PROFILE_LOW: 3, PROFILE_MEDIUM: 5, PROFILE_HIGH: 8}[profile]
    if profile == PROFILE_LOW and info.ram_mb >= 12 * 1024:
        # Plenty of RAM but a small GPU (e.g. 16 GB + GTX 1050 4 GB): one more
        # cached model avoids reloads when toggling options.
        max_models = 4
    return {
        "performance_profile": profile,
        "execution_workers": workers,
        "max_loaded_models": max_models,
    }


def fast_fp16(info: HardwareInfo, device: str) -> bool:
    """FP16 only pays off on GPUs with fast half precision (Turing and newer)."""
    gpu = info.primary_gpu
    return device in ("cuda", "directml") and gpu is not None and gpu.supports_fast_fp16
