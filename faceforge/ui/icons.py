"""Inline SVG icons (stroke style, 24×24 grid) and flag images.

Icons are tinted with the current theme colour at render time, so the same
definitions work in dark and light mode.
"""
from __future__ import annotations

import math
from functools import lru_cache

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPainterPath, QPixmap
from PySide6.QtSvg import QSvgRenderer

_PATHS = {
    "image": '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="9" cy="9" r="2"/>'
             '<path d="m21 15-4-4a2 2 0 0 0-2.8 0L5 20"/>',
    "film": '<rect x="2" y="4" width="20" height="16" rx="3"/><path d="M7 4v16M17 4v16M2 9h5M2 15h5M17 9h5M17 15h5"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "scan_face": '<path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2"/>'
                 '<path d="M8 14s1.5 2 4 2 4-2 4-2"/><path d="M9 9h.01M15 9h.01"/>',
    "play": '<path d="M7 4.5v15a1 1 0 0 0 1.5.9l12-7.5a1 1 0 0 0 0-1.8l-12-7.5A1 1 0 0 0 7 4.5z"/>',
    "pause": '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',
    "stop": '<rect x="5" y="5" width="14" height="14" rx="2"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "sliders": '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
    "sparkles": '<path d="M12 3l1.8 4.9L19 10l-5.2 2.1L12 17l-1.8-4.9L5 10l5.2-2.1z"/><path d="M19 3v4M17 5h4M5 17v4M3 19h4"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2'
           'M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "moon": '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
    "download": '<path d="M12 3v12M7 10l5 5 5-5M5 21h14"/>',
    "upload": '<path d="M12 21V9M7 14l5-5 5 5M5 3h14"/>',
    "x": '<path d="M18 6 6 18M6 6l12 12"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-2.6-6.4L21 8"/><path d="M21 3v5h-5"/>',
    "cpu": '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4'
           'M18 9h4M18 15h4"/>',
    "box": '<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/>',
    "wand": '<path d="m15 4 5 5L8 21l-5-5z"/><path d="M12 7l5 5M20 2v3M18.5 3.5h3"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
    "eye": '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "split": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M12 3v18"/>',
    "trash": '<path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5h.01"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "zoom_fit": '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "gauge": '<path d="M12 14l4-4"/><path d="M3.3 19a10 10 0 1 1 17.4 0z"/>',
    "logo": '<path d="M12 2 3 7v10l9 5 9-5V7z"/><path d="M9 10.5h.01M15 10.5h.01"/><path d="M9 14.5s1.2 1.5 3 1.5 3-1.5 3-1.5"/>',
}


def _svg(name: str, color: str, stroke: float = 1.8) -> bytes:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{_PATHS[name]}</svg>').encode()


@lru_cache(maxsize=256)
def pixmap(name: str, color: str, size: int = 20, ratio: float = 2.0) -> QPixmap:
    px = int(size * ratio)
    image = QImage(px, px, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(QByteArray(_svg(name, color)))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    result = QPixmap.fromImage(image)
    result.setDevicePixelRatio(ratio)
    return result


def icon(name: str, color: str, size: int = 20) -> QIcon:
    return QIcon(pixmap(name, color, size))


# ---------------------------------------------------------------------- flags
def _star(cx: float, cy: float, r: float, rotation: float = -90) -> str:
    points = []
    for i in range(10):
        radius = r if i % 2 == 0 else r * 0.382
        angle = math.radians(rotation + i * 36)
        points.append(f"{cx + radius * math.cos(angle):.2f},{cy + radius * math.sin(angle):.2f}")
    return " ".join(points)


def _flag_svg(code: str) -> str:
    if code == "vi":
        body = (f'<rect width="30" height="20" fill="#da251d"/>'
                f'<polygon points="{_star(15, 10.4, 6)}" fill="#ffff00"/>')
    elif code == "zh":
        small = []
        for x, y in ((10, 2), (12, 4), (12, 7), (10, 9)):
            rot = math.degrees(math.atan2(5 - y, 5 - x))
            small.append(f'<polygon points="{_star(x, y, 1, rot)}" fill="#ffde00"/>')
        body = (f'<rect width="30" height="20" fill="#de2910"/>'
                f'<polygon points="{_star(5, 5, 3)}" fill="#ffde00"/>' + "".join(small))
    else:  # en — Union Jack
        body = ('<rect width="30" height="20" fill="#012169"/>'
                '<path d="M0,0 30,20 M30,0 0,20" stroke="#fff" stroke-width="4"/>'
                '<path d="M0,0 30,20 M30,0 0,20" stroke="#c8102e" stroke-width="1.6"/>'
                '<path d="M15,0v20M0,10h30" stroke="#fff" stroke-width="6"/>'
                '<path d="M15,0v20M0,10h30" stroke="#c8102e" stroke-width="3.4"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 20">{body}</svg>'


@lru_cache(maxsize=8)
def flag_icon(code: str, width: int = 26) -> QIcon:
    ratio = 2.0
    w, h = int(width * ratio), int(width * 2 / 3 * ratio)
    image = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    clip = QPainterPath()
    clip.addRoundedRect(QRectF(0, 0, w, h), 4 * ratio, 4 * ratio)
    painter.setClipPath(clip)
    QSvgRenderer(QByteArray(_flag_svg(code).encode())).render(painter, QRectF(0, 0, w, h))
    painter.end()
    pm = QPixmap.fromImage(image)
    pm.setDevicePixelRatio(ratio)
    return QIcon(pm)


def flag_size(width: int = 26) -> QSize:
    return QSize(width, int(width * 2 / 3))


def app_icon_image(size: int = 256):
    """App icon: white logo on a violet→cyan rounded square (also used by the build)."""
    from PySide6.QtGui import QColor, QLinearGradient

    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    margin = size * 0.06
    rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0.0, QColor("#7c5cff"))
    gradient.setColorAt(1.0, QColor("#38bdf8"))
    path = QPainterPath()
    path.addRoundedRect(rect, size * 0.22, size * 0.22)
    p.fillPath(path, gradient)
    inner = size * 0.58
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#ffffff" '
           f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{_PATHS["logo"]}</svg>')
    QSvgRenderer(QByteArray(svg.encode())).render(
        p, QRectF((size - inner) / 2, (size - inner) / 2, inner, inner))
    p.end()
    return image


def app_icon() -> QIcon:
    result = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        result.addPixmap(QPixmap.fromImage(app_icon_image(size)))
    return result
