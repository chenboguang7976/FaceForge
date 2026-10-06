"""Custom-painted, animated controls.

Qt style sheets can't animate, so the controls people touch most are
painted here with eased colour transitions (hover, press, selection),
reading colours from the active theme at paint time so a theme switch
needs no extra work.

Design scale: radius 8 (inputs) · 10 (buttons) · 12 (cards) · 16 (panels);
spacing on a 4 px grid; control height 36 px.
"""
from __future__ import annotations

from PySide6.QtCore import (Property, QEasingCurve, QPointF, QPropertyAnimation, QRectF, QSize,
                            Qt, Signal)
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QAbstractButton, QProgressBar, QSizePolicy, QWidget

from faceforge.ui import icons
from faceforge.ui.i18n import i18n, tr
from faceforge.ui.theme import theme

RADIUS_INPUT, RADIUS_BUTTON, RADIUS_CARD, RADIUS_PANEL = 8, 10, 12, 16
CONTROL_HEIGHT = 36
DURATION = 160
EASING = QEasingCurve.Type.OutCubic


def mix(a: str | QColor, b: str | QColor, t: float) -> QColor:
    ca, cb = QColor(a), QColor(b)
    t = max(0.0, min(1.0, t))
    return QColor(
        round(ca.red() + (cb.red() - ca.red()) * t),
        round(ca.green() + (cb.green() - ca.green()) * t),
        round(ca.blue() + (cb.blue() - ca.blue()) * t),
        round(ca.alpha() + (cb.alpha() - ca.alpha()) * t),
    )


def with_alpha(color: str, alpha: float) -> QColor:
    c = QColor(color)
    c.setAlphaF(alpha)
    return c


class _Animated:
    """Mixin: eased ``hover``/``press``/``check`` progress values (0..1)."""

    def _init_anim(self) -> None:
        self._hover = self._press = self._check = 0.0
        self._anims = {}
        for name in ("hover", "press", "check"):
            anim = QPropertyAnimation(self, name.encode(), self)
            anim.setDuration(DURATION if name != "press" else 90)
            anim.setEasingCurve(EASING)
            self._anims[name] = anim

    def _animate(self, name: str, target: float) -> None:
        anim = self._anims[name]
        anim.stop()
        anim.setStartValue(getattr(self, f"_{name}"))
        anim.setEndValue(target)
        anim.start()

    def _get_hover(self): return self._hover
    def _set_hover(self, v): self._hover = v; self.update()
    def _get_press(self): return self._press
    def _set_press(self, v): self._press = v; self.update()
    def _get_check(self): return self._check
    def _set_check(self, v): self._check = v; self.update()


class Button(QAbstractButton, _Animated):
    """Rounded push button. Variants: primary, secondary, ghost, danger, link."""

    hover = Property(float, _Animated._get_hover, _Animated._set_hover)
    press = Property(float, _Animated._get_press, _Animated._set_press)
    check = Property(float, _Animated._get_check, _Animated._set_check)

    def __init__(self, text_key: str | None = None, variant: str = "secondary",
                 icon_name: str | None = None, parent=None):
        super().__init__(parent)
        self._init_anim()
        self.variant = variant
        self.icon_name = icon_name
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(CONTROL_HEIGHT if variant != "link" else 24)
        if text_key:
            i18n.bind(self, lambda: (self.setText(tr(text_key)), self.updateGeometry()))

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self._font())
        width = fm.horizontalAdvance(self.text()) + (24 if self.variant == "link" else 36)
        if self.icon_name:
            width += 16 + (8 if self.text() else 0)
        if not self.text() and self.icon_name:
            width = CONTROL_HEIGHT
        return QSize(width, self.minimumHeight())

    def _font(self):
        font = self.font()
        if self.variant == "primary":
            font.setWeight(font.Weight.DemiBold)
        return font

    def enterEvent(self, event):
        self._animate("hover", 1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate("hover", 0.0)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._animate("press", 1.0)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._animate("press", 0.0)
        super().mouseReleaseEvent(event)

    def _colors(self) -> tuple[QColor, QColor, QColor]:
        """(background, border, foreground) for the current animation state."""
        t = theme.tokens
        h, p = self._hover, self._press
        if not self.isEnabled():
            if self.variant in ("ghost", "link"):
                return QColor(0, 0, 0, 0), QColor(0, 0, 0, 0), QColor(t["faint"])
            return QColor(t["surface2"]), QColor(t["border"]), QColor(t["faint"])
        if self.variant == "primary":
            bg = mix(mix(t["accent"], t["accent_hover"], h), t["accent_press"], p)
            return bg, bg, QColor(t["on_accent"])
        if self.variant == "danger":
            bg = mix(t["surface3"], with_alpha(t["danger"], 0.16), h)
            return bg, mix(t["border"], t["danger"], h), mix(t["text"], t["danger"], h)
        if self.variant == "ghost":
            bg = mix(with_alpha(t["surface3"], 0.0), t["surface3"], max(h, p))
            return bg, mix(with_alpha(t["border"], 0.0), t["border"], h), mix(t["muted"], t["text"], h)
        if self.variant == "link":
            return QColor(0, 0, 0, 0), QColor(0, 0, 0, 0), mix(t["accent_hover"], t["text"], h * 0.4)
        bg = mix(mix(t["surface3"], t["surface2"], h), t["surface"], p)
        return bg, mix(t["border"], t["border_strong"], h), QColor(t["text"])

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg, border, fg = self._colors()
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        # A subtle 1px "press" sink.
        r.translate(0, self._press * 0.6)
        p.setPen(QPen(border, 1) if border.alpha() else Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(r, RADIUS_BUTTON, RADIUS_BUTTON)

        p.setFont(self._font())
        fm = QFontMetrics(self._font())
        text = self.text()
        icon_w = 16 if self.icon_name else 0
        gap = 8 if (icon_w and text) else 0
        content = icon_w + gap + fm.horizontalAdvance(text)
        x = r.center().x() - content / 2
        if self.icon_name:
            pm = icons.pixmap(self.icon_name, fg.name(), 16)
            p.drawPixmap(QPointF(x, r.center().y() - 8), pm)
        if text:
            p.setPen(fg)
            if self.variant == "link" and self._hover > 0.5:
                font = self._font()
                font.setUnderline(True)
                p.setFont(font)
            p.drawText(QRectF(x + icon_w + gap, r.top(), content, r.height()),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)


class IconButton(Button):
    """Square ghost button with only an icon (tooltip carries the label)."""

    def __init__(self, icon_name: str, tooltip_key: str | None = None, parent=None):
        super().__init__(None, "ghost", icon_name, parent)
        self.setFixedSize(CONTROL_HEIGHT - 2, CONTROL_HEIGHT - 2)
        if tooltip_key:
            i18n.bind(self, lambda: self.setToolTip(tr(tooltip_key)))

    def set_icon(self, name: str) -> None:
        self.icon_name = name
        self.update()


class Tile(QAbstractButton, _Animated):
    """Checkable preset tile: icon above label, eased selection glow."""

    hover = Property(float, _Animated._get_hover, _Animated._set_hover)
    press = Property(float, _Animated._get_press, _Animated._set_press)
    check = Property(float, _Animated._get_check, _Animated._set_check)

    def __init__(self, icon_name: str, text_key: str, parent=None):
        super().__init__(parent)
        self._init_anim()
        self.icon_name = icon_name
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(64)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        i18n.bind(self, lambda: (self.setText(tr(text_key)), self.update()))
        self.toggled.connect(lambda on: self._animate("check", 1.0 if on else 0.0))

    def sizeHint(self) -> QSize:
        return QSize(72, 64)

    def set_checked_now(self, on: bool) -> None:
        self.blockSignals(True)
        self.setChecked(on)
        self.blockSignals(False)
        self._animate("check", 1.0 if on else 0.0)

    def enterEvent(self, e):
        self._animate("hover", 1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._animate("hover", 0.0)
        super().leaveEvent(e)

    @staticmethod
    def _fit(font, text: str, available: float) -> float:
        font = QFont(font)
        while QFontMetrics(font).horizontalAdvance(text) > available and font.pointSizeF() > 7.5:
            font.setPointSizeF(font.pointSizeF() - 0.25)
        return font.pointSizeF()

    def paintEvent(self, _event) -> None:
        t = theme.tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c, h = self._check, self._hover
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        bg = mix(mix(t["surface2"], t["surface3"], h * 0.6), with_alpha(t["accent"], 0.18), c)
        border = mix(mix(t["border"], t["border_strong"], h), t["accent"], c)
        p.setBrush(bg)
        p.setPen(QPen(border, 1 + c * 0.5))
        p.drawRoundedRect(r, RADIUS_CARD, RADIUS_CARD)
        fg = mix(mix(t["muted"], t["text"], h), t["text"], c)
        icon_color = mix(fg, t["accent_hover"], c)
        p.drawPixmap(QPointF(r.center().x() - 10, r.top() + 12), icons.pixmap(self.icon_name, icon_color.name(), 20))
        font = self.font()
        font.setWeight(font.Weight.DemiBold)
        # Shrink long labels (e.g. "Chất lượng") rather than clipping them, and
        # use one size for the whole row so neighbouring tiles stay consistent.
        available = r.width() - 8
        siblings = [w for w in (self.parentWidget().findChildren(Tile) if self.parentWidget() else [])
                    if w.parentWidget() is self.parentWidget()] or [self]
        font.setPointSizeF(min(self._fit(font, w.text(), available) for w in siblings))
        p.setFont(font)
        p.setPen(fg)
        p.drawText(QRectF(r.left() + 4, r.top() + 36, available, 20),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, self.text())


class Segmented(QWidget):
    """Pill-shaped segmented control with a sliding selection indicator."""
    changed = Signal(str)

    def __init__(self, items: list[tuple[str, str, str | None]], parent=None):
        super().__init__(parent)
        self._items = items  # (value, text_key, icon)
        self._texts = [""] * len(items)
        self._index = 0
        self._hover_index = -1
        self._pos = 0.0  # animated indicator position (in segment units)
        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(CONTROL_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        i18n.bind(self, self._retranslate)

    def _retranslate(self) -> None:
        self._texts = [tr(key) for _, key, _ in self._items]
        self.updateGeometry()
        self.update()

    def _get_pos(self): return self._pos
    def _set_pos(self, v): self._pos = v; self.update()
    pos = Property(float, _get_pos, _set_pos)

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        widest = max((fm.horizontalAdvance(t) for t in self._texts), default=40)
        has_icon = any(icon for *_, icon in self._items)
        return QSize((widest + 32 + (22 if has_icon else 0)) * len(self._items) + 8, CONTROL_HEIGHT)

    def value(self) -> str:
        return self._items[self._index][0]

    def set_value(self, value: str, animate: bool = False) -> None:
        for i, (v, *_rest) in enumerate(self._items):
            if v == value:
                self._index = i
                if animate:
                    self._anim.stop()
                    self._anim.setStartValue(self._pos)
                    self._anim.setEndValue(float(i))
                    self._anim.start()
                else:
                    self._pos = float(i)
                    self.update()

    def _segment_rect(self, pos: float) -> QRectF:
        inner = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        w = inner.width() / len(self._items)
        return QRectF(inner.left() + w * pos, inner.top(), w, inner.height())

    def _index_at(self, x: float) -> int:
        inner = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        return int(max(0, min(len(self._items) - 1, (x - inner.left()) // (inner.width() / len(self._items)))))

    def mouseMoveEvent(self, e):
        index = self._index_at(e.position().x())
        if index != self._hover_index:
            self._hover_index = index
            self.update()

    def leaveEvent(self, _e):
        self._hover_index = -1
        self.update()

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton or not self.isEnabled():
            return
        index = self._index_at(e.position().x())
        if index != self._index:
            self.set_value(self._items[index][0], animate=True)
            self.changed.emit(self._items[index][0])

    def paintEvent(self, _event) -> None:
        t = theme.tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        outer = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor(t["border"]), 1))
        p.setBrush(QColor(t["surface2"]))
        p.drawRoundedRect(outer, RADIUS_BUTTON, RADIUS_BUTTON)

        indicator = self._segment_rect(self._pos)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(t["accent"] if self.isEnabled() else t["border_strong"]))
        p.drawRoundedRect(indicator, RADIUS_BUTTON - 3, RADIUS_BUTTON - 3)

        fm = QFontMetrics(self.font())
        font = self.font()
        font.setWeight(font.Weight.DemiBold)
        p.setFont(font)
        for i, (_, _, icon) in enumerate(self._items):
            seg = self._segment_rect(i)
            # Text colour follows the indicator as it slides past.
            overlap = max(0.0, 1.0 - abs(self._pos - i))
            base = t["text"] if i == self._hover_index else t["muted"]
            fg = mix(base, t["on_accent"], overlap)
            text = self._texts[i]
            icon_w = 16 if icon else 0
            gap = 6 if icon else 0
            width = icon_w + gap + fm.horizontalAdvance(text)
            x = seg.center().x() - width / 2
            if icon:
                p.drawPixmap(QPointF(x, seg.center().y() - 8), icons.pixmap(icon, fg.name(), 16))
            p.setPen(fg)
            p.drawText(QRectF(x + icon_w + gap, seg.top(), width + 4, seg.height()),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)


class SectionHeader(QAbstractButton, _Animated):
    """Collapsible section title: icon, label and a chevron that rotates open/closed."""

    hover = Property(float, _Animated._get_hover, _Animated._set_hover)
    press = Property(float, _Animated._get_press, _Animated._set_press)
    check = Property(float, _Animated._get_check, _Animated._set_check)

    def __init__(self, icon_name: str, text_key: str, expanded: bool, parent=None):
        super().__init__(parent)
        self._init_anim()
        self.icon_name = icon_name
        self.setCheckable(True)
        self.setChecked(expanded)
        self._check = 1.0 if expanded else 0.0
        self._anims["check"].setDuration(220)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        i18n.bind(self, lambda: (self.setText(tr(text_key)), self.update()))
        self.toggled.connect(lambda on: self._animate("check", 1.0 if on else 0.0))

    def enterEvent(self, e):
        self._animate("hover", 1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._animate("hover", 0.0)
        super().leaveEvent(e)

    def paintEvent(self, _e) -> None:
        t = theme.tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0, 4, 0, -4)
        if self._hover > 0.01:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(with_alpha(t["surface3"], 0.7 * self._hover))
            p.drawRoundedRect(r, RADIUS_INPUT, RADIUS_INPUT)
        p.drawPixmap(QPointF(r.left() + 8, r.center().y() - 9), icons.pixmap(self.icon_name, t["accent_hover"], 18))
        font = self.font()
        font.setWeight(font.Weight.DemiBold)
        font.setPointSizeF(font.pointSizeF() * 1.04)
        p.setFont(font)
        p.setPen(QColor(t["text"]))
        p.drawText(QRectF(r.left() + 36, r.top(), r.width() - 70, r.height()),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
        # Chevron: points right when closed, down when open.
        p.save()
        p.translate(r.right() - 16, r.center().y())
        p.rotate(-90 + 90 * self._check)
        p.setPen(QPen(mix(t["faint"], t["text"], self._hover), 1.6, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        path = QPainterPath()
        path.moveTo(-4, -2)
        path.lineTo(0, 2)
        path.lineTo(4, -2)
        p.drawPath(path)
        p.restore()


class SmoothProgress(QProgressBar):
    """Progress bar whose value glides instead of jumping."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 1000)
        self.setTextVisible(False)
        self._anim = QPropertyAnimation(self, b"value", self)
        self._anim.setDuration(350)
        self._anim.setEasingCurve(QEasingCurve.Type.OutQuad)

    def set_fraction(self, fraction: float) -> None:
        target = int(max(0.0, min(1.0, fraction)) * 1000)
        if target < self.value():
            self._anim.stop()
            self.setValue(target)
            return
        self._anim.stop()
        self._anim.setStartValue(self.value())
        self._anim.setEndValue(target)
        self._anim.start()


def expand_animation(body: QWidget, expand: bool, on_done=None) -> QPropertyAnimation:
    """Animate a widget's maximumHeight to open/close it smoothly."""
    body.setVisible(True)
    full = body.sizeHint().height()
    anim = QPropertyAnimation(body, b"maximumHeight", body)
    anim.setDuration(220)
    anim.setEasingCurve(EASING)
    anim.setStartValue(body.height() if body.maximumHeight() < 100000 else (0 if expand else full))
    anim.setEndValue(full if expand else 0)

    def finished():
        if expand:
            body.setMaximumHeight(16777215)
        else:
            body.setVisible(False)
        if on_done:
            on_done()

    anim.finished.connect(finished)
    anim.start()
    return anim
