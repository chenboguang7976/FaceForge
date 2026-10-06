"""Input widgets: drop zones for source/target media and the face gallery."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import Property, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractButton, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QSizePolicy, QVBoxLayout, QWidget)

from faceforge.ui import icons
from faceforge.ui.i18n import i18n, tr
from faceforge.ui.theme import theme
from faceforge.ui.widgets.animated import (RADIUS_BUTTON, RADIUS_CARD, RADIUS_INPUT, IconButton,
                                           _Animated, mix, with_alpha)
from faceforge.ui.widgets.compare_view import bgr_to_pixmap


class DropZone(QFrame, _Animated):
    """Dashed area that accepts files by drag & drop or click-to-browse."""
    files_dropped = Signal(list)
    clicked = Signal()

    hover = Property(float, _Animated._get_hover, _Animated._set_hover)
    press = Property(float, _Animated._get_press, _Animated._set_press)
    check = Property(float, _Animated._get_check, _Animated._set_check)

    def __init__(self, title_key: str, hint_key: str, icon_name: str, parent=None):
        super().__init__(parent)
        self._init_anim()
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(84)
        self._title_key, self._hint_key, self._icon = title_key, hint_key, icon_name
        i18n.bind(self, self.update)

    def paintEvent(self, _event) -> None:
        t = theme.tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = self._hover if self.isEnabled() else 0.0
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setBrush(mix(t["surface2"], with_alpha(t["accent"], 0.12), h))
        p.setPen(QPen(mix(t["border_strong"], t["accent"], h), 1.2, Qt.PenStyle.DashLine))
        p.drawRoundedRect(r, RADIUS_CARD, RADIUS_CARD)
        # Icon in a soft rounded square.
        badge = QRectF(r.left() + 14, r.center().y() - 18, 36, 36)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(mix(with_alpha(t["accent"], 0.12), with_alpha(t["accent"], 0.24), h))
        p.drawRoundedRect(badge, RADIUS_BUTTON, RADIUS_BUTTON)
        p.drawPixmap(QPointF(badge.center().x() - 10, badge.center().y() - 10),
                     icons.pixmap(self._icon, t["accent_hover"], 20))
        text_rect = QRectF(badge.right() + 12, r.top() + 10, r.right() - badge.right() - 24, r.height() - 20)
        font = self.font()
        font.setWeight(font.Weight.DemiBold)
        p.setFont(font)
        p.setPen(QColor(t["text"]))
        title_h = QFontMetrics(font).height()
        p.drawText(QRectF(text_rect.left(), text_rect.top(), text_rect.width(), title_h),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   QFontMetrics(font).elidedText(tr(self._title_key), Qt.TextElideMode.ElideRight,
                                                 int(text_rect.width())))
        font = self.font()
        font.setPointSizeF(font.pointSizeF() * 0.88)
        p.setFont(font)
        p.setPen(QColor(t["muted"]))
        p.drawText(QRectF(text_rect.left(), text_rect.top() + title_h + 2, text_rect.width(),
                          text_rect.height() - title_h - 2),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                   tr(self._hint_key))

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def enterEvent(self, _event) -> None:
        self._animate("hover", 1.0)

    def leaveEvent(self, _event) -> None:
        self._animate("hover", 0.0)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._animate("hover", 1.0)

    def dragLeaveEvent(self, _event) -> None:
        self._animate("hover", 0.0)

    def dropEvent(self, event) -> None:
        self._animate("hover", 0.0)
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)


def rounded_pixmap(pm: QPixmap, size: int, radius: float = 10) -> QPixmap:
    ratio = 2.0
    out = QPixmap(int(size * ratio), int(size * ratio))
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size * ratio, size * ratio), radius * ratio, radius * ratio)
    p.setClipPath(path)
    scaled = pm.scaled(int(size * ratio), int(size * ratio), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                       Qt.TransformationMode.SmoothTransformation)
    p.drawPixmap(int((size * ratio - scaled.width()) / 2), int((size * ratio - scaled.height()) / 2), scaled)
    p.end()
    out.setDevicePixelRatio(ratio)
    return out


class Thumb(QAbstractButton, _Animated):
    """Rounded thumbnail with an animated selection ring and an optional
    remove badge that fades in on hover."""
    remove_requested = Signal()

    hover = Property(float, _Animated._get_hover, _Animated._set_hover)
    press = Property(float, _Animated._get_press, _Animated._set_press)
    check = Property(float, _Animated._get_check, _Animated._set_check)

    def __init__(self, image: np.ndarray, size: int = 56, removable: bool = False, tooltip: str = "", parent=None):
        super().__init__(parent)
        self._init_anim()
        self._size = size
        self._pixmap = rounded_pixmap(bgr_to_pixmap(image), size, RADIUS_BUTTON)
        self.removable = removable
        self.setFixedSize(size + 8, size + 8)
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggled.connect(lambda on: self._animate("check", 1.0 if on else 0.0))

    def _remove_rect(self) -> QRectF:
        return QRectF(self.width() - 24, 2, 20, 20)

    def enterEvent(self, e):
        self._animate("hover", 1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._animate("hover", 0.0)
        super().leaveEvent(e)

    def mouseReleaseEvent(self, e):
        if self.removable and self._remove_rect().contains(e.position()):
            self.setDown(False)
            self.remove_requested.emit()
            return
        super().mouseReleaseEvent(e)

    def paintEvent(self, _e) -> None:
        t = theme.tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        ring = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        if self._check > 0.01 or self._hover > 0.01:
            color = mix(with_alpha(t["border_strong"], self._hover), t["accent"], self._check)
            p.setPen(QPen(color, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(ring, RADIUS_BUTTON + 3, RADIUS_BUTTON + 3)
        p.drawPixmap(4, 4, self._pixmap)
        if self.removable and self._hover > 0.01:
            p.setOpacity(self._hover)
            badge = self._remove_rect()
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, 170))
            p.drawEllipse(badge)
            p.drawPixmap(QPointF(badge.center().x() - 6, badge.center().y() - 6), icons.pixmap("x", "#ffffff", 12))


class ThumbGrid(QWidget):
    """Wrapping grid of thumbnails."""
    selected = Signal(int)
    removed = Signal(int)

    def __init__(self, columns: int = 4, thumb_size: int = 56, removable: bool = False,
                 selectable: bool = True, parent=None):
        super().__init__(parent)
        self.columns, self.thumb_size = columns, thumb_size
        self.removable, self.selectable = removable, selectable
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(6)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.thumbs: list[Thumb] = []

    def set_images(self, images: list[np.ndarray], tooltips: list[str] | None = None) -> None:
        for thumb in self.thumbs:
            thumb.deleteLater()
        self.thumbs = []
        for index, image in enumerate(images):
            thumb = Thumb(image, self.thumb_size, self.removable,
                          tooltips[index] if tooltips and index < len(tooltips) else "")
            thumb.setCheckable(self.selectable)
            if not self.selectable:
                thumb.setCursor(Qt.CursorShape.ArrowCursor)
            thumb.clicked.connect(lambda _=False, i=index: self._on_click(i))
            thumb.remove_requested.connect(lambda i=index: self.removed.emit(i))
            self.grid.addWidget(thumb, index // self.columns, index % self.columns)
            self.thumbs.append(thumb)
        self.setVisible(bool(images))

    def _on_click(self, index: int) -> None:
        for i, thumb in enumerate(self.thumbs):
            thumb.setChecked(i == index and self.selectable)
        self.selected.emit(index)

    def set_selected(self, index: int | None) -> None:
        for i, thumb in enumerate(self.thumbs):
            thumb.setChecked(i == index)


class TargetInfo(QFrame):
    """Card showing the current target: thumbnail, file name, kind and size."""
    clear_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 6, 10)
        layout.setSpacing(12)
        self.thumb = QLabel()
        self.thumb.setFixedSize(52, 52)
        layout.addWidget(self.thumb)
        text = QVBoxLayout()
        text.setSpacing(2)
        self.name = QLabel()
        self.name.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.name.setStyleSheet("font-weight: 600;")
        self.meta = QLabel()
        self.meta.setObjectName("Hint")
        text.addWidget(self.name)
        text.addWidget(self.meta)
        layout.addLayout(text, 1)
        self.clear = IconButton("x", "common.remove")
        self.clear.clicked.connect(self.clear_requested.emit)
        layout.addWidget(self.clear)

    def set_target(self, image: np.ndarray | None, name: str, meta: str) -> None:
        if image is not None:
            self.thumb.setPixmap(rounded_pixmap(bgr_to_pixmap(image), 52, RADIUS_INPUT))
        metrics = self.name.fontMetrics()
        self.name.setText(metrics.elidedText(name, Qt.TextElideMode.ElideMiddle, 170))
        self.name.setToolTip(name)
        self.meta.setText(meta)


def short_name(path: str) -> str:
    return Path(path).name
