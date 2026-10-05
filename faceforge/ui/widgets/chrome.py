"""Window chrome: language flag switcher and toast notifications."""
from __future__ import annotations

from PySide6.QtCore import Property, QEasingCurve, QPoint, QPropertyAnimation, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import (QAbstractButton, QButtonGroup, QGraphicsOpacityEffect, QHBoxLayout,
                               QLabel, QWidget)

from faceforge.ui import icons
from faceforge.ui.i18n import LANGUAGE_NAMES, LANGUAGES
from faceforge.ui.theme import theme
from faceforge.ui.widgets.animated import RADIUS_INPUT, IconButton, _Animated, mix, with_alpha


class FlagButton(QAbstractButton, _Animated):
    """Rounded flag with an accent ring that fades in when selected."""

    hover = Property(float, _Animated._get_hover, _Animated._set_hover)
    press = Property(float, _Animated._get_press, _Animated._set_press)
    check = Property(float, _Animated._get_check, _Animated._set_check)

    def __init__(self, code: str, parent=None):
        super().__init__(parent)
        self._init_anim()
        self.code = code
        self.setCheckable(True)
        self.setFixedSize(38, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(LANGUAGE_NAMES[code])
        self.setAccessibleName(LANGUAGE_NAMES[code])
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
        ring = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        if self._check > 0.01 or self._hover > 0.01:
            color = mix(with_alpha(t["border_strong"], self._hover), t["accent"], self._check)
            p.setPen(QPen(color, 1.6))
            p.setBrush(with_alpha(t["accent"], 0.14 * self._check))
            p.drawRoundedRect(ring, RADIUS_INPUT, RADIUS_INPUT)
        p.setOpacity(0.72 + 0.28 * max(self._check, self._hover))
        size = icons.flag_size(24)
        icons.flag_icon(self.code, 24).paint(
            p, int(ring.center().x() - size.width() / 2), int(ring.center().y() - size.height() / 2),
            size.width(), size.height())


class LanguageSwitcher(QWidget):
    """Three flag buttons: 🇬🇧 English · 🇨🇳 中文 · 🇻🇳 Tiếng Việt."""
    language_selected = Signal(str)

    def __init__(self, current: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.group = QButtonGroup(self)
        self.buttons: dict[str, FlagButton] = {}
        for code in LANGUAGES:
            button = FlagButton(code)
            button.clicked.connect(lambda _=False, c=code: self.language_selected.emit(c))
            self.group.addButton(button)
            layout.addWidget(button)
            self.buttons[code] = button
        self.set_current(current)
        from faceforge.ui.i18n import i18n

        i18n.language_changed.connect(self.set_current)

    def set_current(self, code: str) -> None:
        if code in self.buttons:
            self.buttons[code].setChecked(True)


class Toast(QLabel):
    """Transient message in the bottom-right corner of its parent."""

    COLORS = {"info": "accent", "success": "success", "warning": "warning", "error": "danger"}

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setMaximumWidth(380)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)
        self.hide()

    def show_message(self, text: str, kind: str = "info", msec: int = 3500) -> None:
        t = theme.tokens
        color = t[self.COLORS.get(kind, "accent")]
        self.setStyleSheet(
            f"QLabel {{ background: {t['surface3']}; color: {t['text']}; border: 1px solid {t['border_strong']};"
            f" border-left: 4px solid {color}; border-radius: 12px; padding: 12px 16px; }}")
        self.setText(text)
        self.adjustSize()
        self._place()
        self._slide = QPropertyAnimation(self, b"pos", self)
        self._slide.setDuration(220)
        self._slide.setEasingCurve(QEasingCurve.Type.OutCubic)
        end = self.pos()
        self._slide.setStartValue(end + QPoint(0, 14))
        self._slide.setEndValue(end)
        self.raise_()
        self.show()
        self._slide.start()
        self._anim.stop()
        self._anim.setDuration(160)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()
        self._timer.start(msec)

    def _place(self) -> None:
        parent = self.parentWidget()
        if parent:
            self.move(parent.width() - self.width() - 20, parent.height() - self.height() - 20)

    def _fade_out(self) -> None:
        self._anim.stop()
        self._anim.setDuration(400)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self._hide_once)
        self._anim.start()

    def _hide_once(self) -> None:
        self._anim.finished.disconnect(self._hide_once)
        if self._effect.opacity() < 0.05:
            self.hide()


def icon_button(name: str, tooltip_key: str | None = None) -> IconButton:
    return IconButton(name, tooltip_key)
