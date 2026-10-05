"""Runtime language switching (English / 中文 / Tiếng Việt).

Widgets register how to (re)apply their text with :func:`bind`; switching
language re-runs every binding, so the UI updates instantly without a
restart.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, Signal

from faceforge.ui.translations import TRANSLATIONS

LANGUAGES = ["en", "zh", "vi"]
LANGUAGE_NAMES = {"en": "English", "zh": "中文", "vi": "Tiếng Việt"}


class _I18n(QObject):
    language_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.language = "en"
        self._bindings: list[tuple[QObject | None, Callable[[], None]]] = []

    def set_language(self, language: str) -> None:
        if language not in LANGUAGES:
            language = "en"
        if language == self.language:
            return
        self.language = language
        self.refresh()
        self.language_changed.emit(language)

    def tr(self, key: str, **kwargs) -> str:
        table = TRANSLATIONS.get(key)
        if table is None:
            return key
        text = table.get(self.language) or table.get("en") or key
        return text.format(**kwargs) if kwargs else text

    def bind(self, owner: QObject | None, apply: Callable[[], None]) -> None:
        """Run ``apply`` now and after every language change, while ``owner`` lives."""
        apply()
        self._bindings.append((owner, apply))
        if owner is not None:
            owner.destroyed.connect(lambda *_: self._drop(owner))

    def _drop(self, owner: QObject) -> None:
        self._bindings = [(o, f) for o, f in self._bindings if o is not owner]

    def refresh(self) -> None:
        for owner, apply in list(self._bindings):
            try:
                apply()
            except RuntimeError:  # C++ object already deleted
                self._drop(owner)


i18n = _I18n()
tr = i18n.tr


def bind_text(widget, key: str, setter: str = "setText", **kwargs) -> None:
    """Shortcut: keep ``widget.<setter>(tr(key))`` up to date."""
    method = getattr(widget, setter)
    i18n.bind(widget, lambda: method(tr(key, **kwargs)))


def bind_tooltip(widget, key: str) -> None:
    i18n.bind(widget, lambda: widget.setToolTip(tr(key)))
