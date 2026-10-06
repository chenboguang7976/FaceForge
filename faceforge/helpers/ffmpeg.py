"""FFmpeg discovery, hardware-encoder detection and subprocess helpers."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from functools import lru_cache

from faceforge.helpers.logger import get_logger

log = get_logger(__name__)

# Hide the console window that would otherwise flash for every ffmpeg call
# in the windowed (no console) Windows build.
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


def popen_kwargs() -> dict:
    return {"creationflags": CREATE_NO_WINDOW} if sys.platform == "win32" else {}


@lru_cache(maxsize=1)
def find_ffmpeg() -> str | None:
    """Prefer the binary bundled by imageio-ffmpeg, then the one on PATH."""
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe:
            return exe
    except Exception:  # noqa: BLE001 - optional dependency / missing binary
        pass
    return shutil.which("ffmpeg")


def run(args: list[str], timeout: float | None = None) -> subprocess.CompletedProcess:
    exe = find_ffmpeg()
    if not exe:
        raise FileNotFoundError("ffmpeg")
    return subprocess.run(
        [exe, "-hide_banner", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        **popen_kwargs(),
    )


# Encoders tried in order for each platform; libx264 is the universal fallback.
_HW_ENCODERS = {
    "win32": ["h264_nvenc", "h264_qsv", "h264_amf"],
    "darwin": ["h264_videotoolbox"],
    "linux": ["h264_nvenc"],
}


def _encoder_works(encoder: str) -> bool:
    """Encode a few blank frames; listing an encoder doesn't mean the GPU/driver supports it."""
    try:
        result = run(
            ["-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=256x256:r=25",
             "-frames:v", "5", "-c:v", encoder, "-f", "null", "-"],
            timeout=20,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


@lru_cache(maxsize=1)
def available_encoders() -> list[str]:
    """Working H.264 encoders, best first. Always ends with ``libx264``."""
    if not find_ffmpeg():
        return []
    try:
        listing = run(["-encoders"], timeout=15).stdout.decode("utf-8", "ignore")
    except (OSError, subprocess.TimeoutExpired):
        return ["libx264"]
    platform_key = "linux" if sys.platform.startswith("linux") else sys.platform
    found = [e for e in _HW_ENCODERS.get(platform_key, []) if re.search(rf"\b{e}\b", listing)]
    working = [e for e in found if _encoder_works(e)]
    log.info("Video encoders: hardware=%s", working or "none")
    return [*working, "libx264"]


def encoder_args(encoder: str, quality: int, low_end: bool) -> list[str]:
    """Map a 1-100 quality slider onto each encoder's own quality scale."""
    quality = max(1, min(100, int(quality)))
    crf = int(round(35 - quality * 0.17))  # 100 -> 18, 80 -> 21, 50 -> 26
    if encoder == "h264_nvenc":
        return ["-c:v", encoder, "-preset", "p4", "-rc", "vbr", "-cq", str(crf), "-b:v", "0"]
    if encoder == "h264_qsv":
        return ["-c:v", encoder, "-preset", "medium", "-global_quality", str(crf)]
    if encoder == "h264_amf":
        return ["-c:v", encoder, "-quality", "balanced", "-rc", "cqp",
                "-qp_i", str(crf), "-qp_p", str(crf)]
    if encoder == "h264_videotoolbox":
        return ["-c:v", encoder, "-q:v", str(quality)]
    # Software x264: a faster preset leaves CPU cores free for inference on weak machines.
    preset = "veryfast" if low_end else "medium"
    return ["-c:v", "libx264", "-preset", preset, "-crf", str(crf)]


def probe_media(path: str) -> dict:
    """Parse ``ffmpeg -i`` output: fps, size, duration and whether audio exists."""
    info = {"fps": 0.0, "width": 0, "height": 0, "duration": 0.0, "has_audio": False}
    try:
        text = run(["-i", path], timeout=30).stderr.decode("utf-8", "ignore")
    except (OSError, subprocess.TimeoutExpired, FileNotFoundError):
        return info
    if m := re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", text):
        h, mnt, s = m.groups()
        info["duration"] = int(h) * 3600 + int(mnt) * 60 + float(s)
    video_line = next((line for line in text.splitlines() if "Video:" in line), "")
    if m := re.search(r"(\d{2,5})x(\d{2,5})", video_line):
        info["width"], info["height"] = int(m.group(1)), int(m.group(2))
    if m := re.search(r"([\d.]+) fps", video_line):
        info["fps"] = float(m.group(1))
    elif m := re.search(r"([\d.]+) tbr", video_line):
        info["fps"] = float(m.group(1))
    info["has_audio"] = "Audio:" in text
    return info
