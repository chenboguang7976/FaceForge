"""Small reusable controls: collapsible sections, switches, sliders, segmented buttons."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import (Property, QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt,
                            Signal)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QAbstractButton, QComboBox, QHBoxLayout,
                               QLabel, QSizePolicy, QSlider, QVBoxLayout, QWidget)

from faceforge.ui.i18n import bind_text, bind_tooltip, i18n, tr
from faceforge.ui.theme import theme
from faceforge.ui.widgets.animated import SectionHeader, expand_animation, mix


class Section(QWidget):
    """A titled group of settings that opens and closes with a smooth slide."""

    def __init__(self, title_key: str, icon_name: str, expanded: bool = True, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.header = SectionHeader(icon_name, title_key, expanded)
        self.header.toggled.connect(self._toggle)
        layout.addWidget(self.header)

        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(8, 4, 8, 16)
        self.body_layout.setSpacing(12)
        layout.addWidget(self.body)
        self.body.setVisible(expanded)
        self._anim = None

    def _toggle(self, on: bool) -> None:
        self._anim = expand_animation(self.body, on)

    def add(self, widget: QWidget) -> QWidget:
        self.body_layout.addWidget(widget)
        return widget


class ToggleSwitch(QAbstractButton):
    """iOS-style switch."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(40, 22)
        self._pos = 0.0
        self._anim = QPropertyAnimation(self, b"knob", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._animate)

    def _animate(self, on: bool) -> None:
        self._anim.stop()
        self._anim.setEndValue(1.0 if on else 0.0)
        self._anim.start()

    def get_knob(self) -> float:
        return self._pos

    def set_knob(self, value: float) -> None:
        self._pos = value
        self.update()

    knob = Property(float, get_knob, set_knob)

    def setChecked(self, on: bool) -> None:  # noqa: N802 - Qt naming
        super().setChecked(on)
        self._anim.stop()
        self._pos = 1.0 if on else 0.0
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(40, 22)

    def paintEvent(self, _event) -> None:
        t = theme.tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Track and border colours glide with the knob.
        track = mix(t["surface3"], t["accent"], self._pos)
        border = mix(t["border_strong"], t["accent"], self._pos)
        if not self.isEnabled():
            track.setAlpha(110)
            border.setAlpha(110)
        p.setPen(border)
        p.setBrush(track)
        p.drawRoundedRect(QRectF(0.5, 0.5, 39, 21), 10.5, 10.5)
        x = 3 + self._pos * 18
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 40))
        p.drawEllipse(QRectF(x, 3.8, 16, 16))  # soft shadow
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(QRectF(x, 3, 16, 16))


class Row(QWidget):
    """Label (+ optional value text) on the left, control on the right or below."""

    def __init__(self, label_key: str, control: QWidget, hint_key: str | None = None,
                 stacked: bool = False, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)
        top = QHBoxLayout()
        top.setSpacing(8)
        self.label = QLabel()
        bind_text(self.label, label_key)
        if hint_key:
            bind_tooltip(self.label, hint_key)
            bind_tooltip(control, hint_key)
        top.addWidget(self.label, 1)
        self.value = QLabel()
        self.value.setObjectName("Value")
        top.addWidget(self.value)
        if not stacked:
            top.addWidget(control)
        outer.addLayout(top)
        if stacked:
            outer.addWidget(control)
        self.control = control


def make_slider(minimum: int, maximum: int, step: int = 1) -> QSlider:
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(minimum, maximum)
    slider.setSingleStep(step)
    slider.setPageStep(step)
    slider.setCursor(Qt.CursorShape.PointingHandCursor)
    return slider


class SliderRow(Row):
    value_changed = Signal(int)

    def __init__(self, label_key: str, minimum: int, maximum: int, fmt: Callable[[int], str],
                 hint_key: str | None = None, parent=None):
        self.slider = make_slider(minimum, maximum)
        super().__init__(label_key, self.slider, hint_key, stacked=True, parent=parent)
        self._fmt = fmt
        self.slider.valueChanged.connect(self._changed)

    def _changed(self, v: int) -> None:
        self.value.setText(self._fmt(v))
        self.value_changed.emit(v)

    def set_value(self, v: int) -> None:
        self.slider.blockSignals(True)
        self.slider.setValue(int(v))
        self.slider.blockSignals(False)
        self.value.setText(self._fmt(int(v)))


class ComboRow(Row):
    """Combo box whose items are (value, label_key or literal text)."""

    def __init__(self, label_key: str, items: list[tuple[str, str]], translate: bool = True,
                 hint_key: str | None = None, parent=None):
        self.combo = QComboBox()
        self.combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        super().__init__(label_key, self.combo, hint_key, stacked=True, parent=parent)
        self._items = items
        self._translate = translate
        for value, _ in items:
            self.combo.addItem("", value)
        i18n.bind(self.combo, self._retranslate)

    def _retranslate(self) -> None:
        for index, (_, text) in enumerate(self._items):
            self.combo.setItemText(index, tr(text) if self._translate else text)

    def value_of(self) -> str:
        return self.combo.currentData()

    def set_value(self, value) -> None:
        index = self.combo.findData(value)
        if index >= 0:
            self.combo.blockSignals(True)
            self.combo.setCurrentIndex(index)
            self.combo.blockSignals(False)


class SwitchRow(Row):
    def __init__(self, label_key: str, hint_key: str | None = None, parent=None):
        self.switch = ToggleSwitch()
        super().__init__(label_key, self.switch, hint_key, parent=parent)

    def set_value(self, on: bool) -> None:
        self.switch.blockSignals(True)
        self.switch.setChecked(bool(on))
        self.switch.blockSignals(False)
