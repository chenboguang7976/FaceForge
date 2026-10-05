"""Preview canvas with before/after split slider, zoom and pan."""
from __future__ import annotations

import numpy as np
from PySide6.QtCore import Property, QEasingCurve, QPointF, QPropertyAnimation, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from faceforge.ui.theme import theme

MODE_RESULT = "result"
MODE_ORIGINAL = "original"
MODE_SPLIT = "split"


def bgr_to_pixmap(frame: np.ndarray) -> QPixmap:
    rgb = np.ascontiguousarray(frame[:, :, ::-1])
    h, w = rgb.shape[:2]
    image = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(image.copy())


class CompareView(QWidget):
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 240)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self._before: QPixmap | None = None
        self._after: QPixmap | None = None
        self.mode = MODE_SPLIT
        self._split = 0.5
        self._zoom = 1.0          # relative to "fit"
        self._offset = QPointF()  # pan in widget pixels
        self._drag: str | None = None
        self._last = QPointF()
        self._busy = False
        self.placeholder_title = ""
        self.placeholder_hint = ""
        self.drop_highlight = False
        # Results fade in over the original instead of popping.
        self._fade = 1.0
        self._fade_anim = QPropertyAnimation(self, b"fade", self)
        self._fade_anim.setDuration(240)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._busy_alpha = 0.0
        self._busy_anim = QPropertyAnimation(self, b"busy_alpha", self)
        self._busy_anim.setDuration(200)

    def _get_fade(self): return self._fade
    def _set_fade(self, v): self._fade = v; self.update()
    fade = Property(float, _get_fade, _set_fade)

    def _get_busy(self): return self._busy_alpha
    def _set_busy(self, v): self._busy_alpha = v; self.update()
    busy_alpha = Property(float, _get_busy, _set_busy)

    def _start_fade(self) -> None:
        self._fade_anim.stop()
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()

    # ----------------------------------------------------------------- content
    def set_images(self, before: np.ndarray | None, after: np.ndarray | None = None, reset_view: bool = False) -> None:
        self._before = bgr_to_pixmap(before) if before is not None else None
        self._after = bgr_to_pixmap(after) if after is not None else None
        if self._after is not None:
            self._start_fade()
        if reset_view:
            self.fit()
        self.update()

    def set_result(self, after: np.ndarray | None) -> None:
        self._after = bgr_to_pixmap(after) if after is not None else None
        if self._after is not None:
            self._start_fade()
        self.update()

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._busy_anim.stop()
        self._busy_anim.setStartValue(self._busy_alpha)
        self._busy_anim.setEndValue(1.0 if busy else 0.0)
        self._busy_anim.start()

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.update()

    def fit(self) -> None:
        self._zoom = 1.0
        self._offset = QPointF()
        self.update()

    def has_image(self) -> bool:
        return self._before is not None

    # ---------------------------------------------------------------- geometry
    def _image_rect(self) -> QRectF:
        pm = self._before
        if pm is None:
            return QRectF()
        area = QRectF(self.rect()).adjusted(12, 12, -12, -12)
        scale = min(area.width() / pm.width(), area.height() / pm.height()) * self._zoom
        w, h = pm.width() * scale, pm.height() * scale
        center = area.center() + self._offset
        return QRectF(center.x() - w / 2, center.y() - h / 2, w, h)

    def _split_x(self, rect: QRectF) -> float:
        return rect.left() + rect.width() * self._split

    # ------------------------------------------------------------------- paint
    def paintEvent(self, _event) -> None:
        t = theme.tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        outer = QPainterPath()
        outer.addRoundedRect(QRectF(self.rect()), 12, 12)
        p.fillPath(outer, QColor(t["preview_bg"]))
        p.setClipPath(outer)

        if self._before is None:
            self._paint_placeholder(p, t)
            return

        rect = self._image_rect()
        after = self._after
        if self.mode == MODE_ORIGINAL or after is None:
            p.drawPixmap(rect, self._before, QRectF(self._before.rect()))
        elif self.mode == MODE_RESULT:
            p.drawPixmap(rect, self._before, QRectF(self._before.rect()))
            p.setOpacity(self._fade)
            p.drawPixmap(rect, after, QRectF(after.rect()))
            p.setOpacity(1.0)
        else:
            x = self._split_x(rect)
            p.save()
            p.setClipRect(QRectF(rect.left(), rect.top(), x - rect.left(), rect.height()))
            p.drawPixmap(rect, self._before, QRectF(self._before.rect()))
            p.restore()
            p.save()
            p.setClipRect(QRectF(x, rect.top(), rect.right() - x, rect.height()))
            p.drawPixmap(rect, self._before, QRectF(self._before.rect()))
            p.setOpacity(self._fade)
            p.drawPixmap(rect, after, QRectF(after.rect()))
            p.restore()
            self._paint_handle(p, rect, x, t)

        if self._busy_alpha > 0.01:
            # Thin animated-in accent bar along the top edge while rendering.
            p.setOpacity(self._busy_alpha)
            bar = QRectF(0, 0, self.width(), 3)
            p.fillRect(bar, QColor(t["accent"]))
            p.setOpacity(1.0)

    def _paint_handle(self, p: QPainter, rect: QRectF, x: float, t: dict) -> None:
        p.setPen(QPen(QColor(255, 255, 255, 230), 2))
        p.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
        knob = QRectF(x - 15, rect.center().y() - 15, 30, 30)
        p.setBrush(QColor(t["accent"]))
        p.setPen(QPen(QColor("#ffffff"), 2))
        p.drawEllipse(knob)
        p.setPen(QPen(QColor("#ffffff"), 2))
        cy = knob.center().y()
        for sign in (-1, 1):
            cx = knob.center().x() + sign * 5
            p.drawLine(QPointF(cx, cy - 4), QPointF(cx + sign * 3, cy))
            p.drawLine(QPointF(cx + sign * 3, cy), QPointF(cx, cy + 4))

    def _paint_placeholder(self, p: QPainter, t: dict) -> None:
        r = QRectF(self.rect()).adjusted(18, 18, -18, -18)
        pen = QPen(QColor(t["accent"] if self.drop_highlight else t["border_strong"]), 1.5, Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r, 12, 12)
        from faceforge.ui.icons import pixmap

        icon = pixmap("upload", t["muted"], 40)
        p.drawPixmap(int(r.center().x() - 20), int(r.center().y() - 56), icon)
        p.setPen(QColor(t["text"]))
        font = p.font()
        font.setPointSizeF(12.5)
        font.setBold(True)
        p.setFont(font)
        p.drawText(QRectF(r.left(), r.center().y() - 6, r.width(), 26), Qt.AlignmentFlag.AlignCenter,
                   self.placeholder_title)
        font.setPointSizeF(9.5)
        font.setBold(False)
        p.setFont(font)
        p.setPen(QColor(t["muted"]))
        p.drawText(QRectF(r.left() + 20, r.center().y() + 22, r.width() - 40, 44),
                   Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap, self.placeholder_hint)

    # ------------------------------------------------------------------- input
    def _near_handle(self, pos: QPointF) -> bool:
        if self.mode != MODE_SPLIT or self._after is None or self._before is None:
            return False
        rect = self._image_rect()
        return abs(pos.x() - self._split_x(rect)) < 14 and rect.top() <= pos.y() <= rect.bottom()

    def mousePressEvent(self, event) -> None:
        pos = event.position()
        if event.button() == Qt.MouseButton.LeftButton and self._near_handle(pos):
            self._drag = "split"
        elif event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton) and self._before:
            if self.mode == MODE_SPLIT and self._after is not None and self._zoom <= 1.0:
                self._drag = "split"
                self._move_split(pos)
            else:
                self._drag = "pan"
        self._last = pos

    def _move_split(self, pos: QPointF) -> None:
        rect = self._image_rect()
        if rect.width() > 0:
            self._split = min(1.0, max(0.0, (pos.x() - rect.left()) / rect.width()))
            self.update()

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        if self._drag == "split":
            self._move_split(pos)
        elif self._drag == "pan":
            self._offset += pos - self._last
            self.update()
        else:
            near = self._near_handle(pos)
            self.setCursor(Qt.CursorShape.SplitHCursor if near else Qt.CursorShape.ArrowCursor)
        self._last = pos

    def mouseReleaseEvent(self, _event) -> None:
        self._drag = None

    def mouseDoubleClickEvent(self, _event) -> None:
        self.fit()

    def wheelEvent(self, event) -> None:
        if self._before is None:
            return
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        new_zoom = min(12.0, max(1.0, self._zoom * factor))
        # Zoom around the cursor.
        center = QRectF(self.rect()).center() + self._offset
        pos = event.position()
        self._offset += (pos - center) * (1 - new_zoom / self._zoom)
        self._zoom = new_zoom
        if self._zoom == 1.0:
            self._offset = QPointF()
        self.update()

    # ------------------------------------------------------------- drag & drop
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_highlight = True
            self.update()

    def dragLeaveEvent(self, _event) -> None:
        self.drop_highlight = False
        self.update()

    def dropEvent(self, event) -> None:
        self.drop_highlight = False
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
        self.update()
