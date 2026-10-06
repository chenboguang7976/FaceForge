"""Model manager: see what's installed, download what's missing."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QDialog, QHBoxLayout, QHeaderView, QLabel,
                               QTableWidget, QTableWidgetItem, QVBoxLayout)

from faceforge.core.models_data import MODELS
from faceforge.ui.controller import Controller
from faceforge.ui.i18n import i18n, tr
from faceforge.ui.theme import theme
from faceforge.ui.widgets.animated import Button, SmoothProgress

CATEGORY_KEYS = {"detector": "models.cat.detector", "landmarker": "models.cat.landmarker",
                 "recognizer": "models.cat.recognizer",
                 "swapper": "models.cat.swapper", "enhancer": "models.cat.enhancer", "mask": "models.cat.mask"}


class ModelManagerDialog(QDialog):
    def __init__(self, controller: Controller, required: list[str] | None = None, parent=None):
        super().__init__(parent)
        self.c = controller
        self.required = list(required or [])
        self._downloading = False
        self._queue: list[str] = []
        self.setMinimumSize(720, 520)
        i18n.bind(self, lambda: self.setWindowTitle(tr("models.title")))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        self.headline = QLabel()
        self.headline.setObjectName("SectionTitle")
        self.headline.setWordWrap(True)
        layout.addWidget(self.headline)
        self.location = QLabel()
        self.location.setObjectName("Hint")
        self.location.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.location)

        self.table = QTableWidget(0, 4)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table, 1)

        self.progress = SmoothProgress()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        self.status = QLabel()
        self.status.setObjectName("Hint")
        layout.addWidget(self.status)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self.open_folder = Button("models.open_folder", icon_name="folder")
        self.open_folder.clicked.connect(self._open_folder)
        buttons.addWidget(self.open_folder)
        buttons.addStretch()
        self.download_selected = Button("models.download_selected")
        self.download_selected.clicked.connect(self._download_selected)
        buttons.addWidget(self.download_selected)
        self.download_btn = Button(None, "primary", "download")
        self.download_btn.clicked.connect(self._download_primary)
        buttons.addWidget(self.download_btn)
        self.close_btn = Button("common.close", "ghost")
        self.close_btn.clicked.connect(self._close)
        buttons.addWidget(self.close_btn)
        layout.addLayout(buttons)

        controller.download_progress.connect(self._on_progress)
        controller.download_finished.connect(self._on_finished)
        i18n.bind(self, self._refresh)

    # ----------------------------------------------------------------- view
    def _refresh(self) -> None:
        models = self.c.models
        self.location.setText(tr("models.location", path=str(models.models_dir)))
        if self.required:
            missing = models.missing(self.required)
            size = sum(MODELS[k].size_mb for k in missing)
            self.headline.setText(tr("models.required_headline", count=len(missing), size=size))
            self.download_btn.setText(tr("models.download_required"))
        else:
            self.headline.setText(tr("models.headline"))
            self.download_btn.setText(tr("models.download_missing"))
        self.table.setHorizontalHeaderLabels([tr("models.col.name"), tr("models.col.type"),
                                              tr("models.col.size"), tr("models.col.status")])
        self.table.setRowCount(len(MODELS))
        t = theme.tokens
        from PySide6.QtGui import QColor

        for row, info in enumerate(MODELS.values()):
            installed = models.is_available(info.key)
            name = QTableWidgetItem(info.title + ("  ★" if info.key in self.required else ""))
            name.setData(Qt.ItemDataRole.UserRole, info.key)
            self.table.setItem(row, 0, name)
            self.table.setItem(row, 1, QTableWidgetItem(tr(CATEGORY_KEYS[info.category])))
            self.table.setItem(row, 2, QTableWidgetItem(f"{info.size_mb} MB"))
            status = QTableWidgetItem(tr("models.installed") if installed else tr("models.missing"))
            status.setForeground(QColor(t["success"] if installed else t["muted"]))
            self.table.setItem(row, 3, status)

    # -------------------------------------------------------------- actions
    def _open_folder(self) -> None:
        self.c.models.models_dir.mkdir(parents=True, exist_ok=True)
        self.c.open_path(self.c.models.models_dir)

    def _download_primary(self) -> None:
        keys = self.required or list(MODELS)
        self._start(self.c.models.missing(keys))

    def _download_selected(self) -> None:
        rows = {i.row() for i in self.table.selectedIndexes()}
        keys = [self.table.item(r, 0).data(Qt.ItemDataRole.UserRole) for r in sorted(rows)]
        self._start(self.c.models.missing(keys))

    def _start(self, keys: list[str]) -> None:
        if not keys:
            self.status.setText(tr("models.nothing_to_download"))
            if self.required:
                self.accept()
            return
        self._downloading = True
        self._queue = keys
        self._total = sum(MODELS[k].size for k in keys)
        self._done_before: dict[str, int] = {}
        self.progress.setVisible(True)
        self.progress.set_fraction(0)
        for widget in (self.download_btn, self.download_selected):
            widget.setEnabled(False)
        self.close_btn.setText(tr("common.cancel"))
        self.c.download(keys)

    def _on_progress(self, key: str, done: int, total: int) -> None:
        self._done_before[key] = done
        overall = sum(self._done_before.values())
        self.progress.set_fraction(overall / max(1, self._total))
        self.status.setText(tr("models.downloading", name=MODELS[key].title,
                               done=done // 2**20, total=total // 2**20))

    def _on_finished(self, ok: bool, error: str) -> None:
        if not self._downloading:
            return
        self._downloading = False
        self.progress.setVisible(False)
        for widget in (self.download_btn, self.download_selected):
            widget.setEnabled(True)
        self.close_btn.setText(tr("common.close"))
        self._refresh()
        if ok:
            self.status.setText(tr("models.download_done"))
            if self.required and not self.c.models.missing(self.required):
                self.accept()
        else:
            self.status.setText(tr("models.download_failed", error=error) if error else tr("models.download_cancelled"))

    def _close(self) -> None:
        if self._downloading:
            self.c.cancel_download()
            return
        self.reject()

    def reject(self) -> None:
        if self._downloading:
            self.c.cancel_download()
        super().reject()
