"""Main application window."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel,
                               QMainWindow, QMessageBox, QSizePolicy, QSlider, QSplitter, QStatusBar,
                               QVBoxLayout, QWidget)

from faceforge import __version__, edition
from faceforge.config import Settings
from faceforge.core.presets import default_preset, meets_pro_requirements
from faceforge.helpers.image_io import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from faceforge.ui import icons
from faceforge.ui.controller import KIND_BATCH, KIND_NONE, KIND_VIDEO, Controller
from faceforge.ui.i18n import bind_text, i18n, tr
from faceforge.ui.model_manager import ModelManagerDialog
from faceforge.ui.monitor import ResourceMonitor
from faceforge.ui.settings_panel import SettingsPanel
from faceforge.ui.theme import theme
from faceforge.ui.translations import TRANSLATIONS
from faceforge.ui.widgets.chrome import LanguageSwitcher, Toast, icon_button
from faceforge.ui.widgets.compare_view import MODE_ORIGINAL, MODE_RESULT, MODE_SPLIT, CompareView
from faceforge.ui.widgets.animated import Button, Segmented, SmoothProgress
from faceforge.ui.widgets.media import DropZone, TargetInfo, ThumbGrid

IMAGE_FILTER = "*" + " *".join(sorted(IMAGE_EXTENSIONS))
VIDEO_FILTER = "*" + " *".join(sorted(VIDEO_EXTENSIONS))


def _fmt_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _gb(value: int) -> str:
    return f"{value / 2**30:.1f}"


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.controller = Controller(settings)
        self._state = "idle"
        self._state_prev = "idle"
        self._faded_in = False
        self._dialog: ModelManagerDialog | None = None
        if settings.is_new or not settings.get("first_run_done"):
            self._first_run_defaults()

        self.setMinimumSize(1100, 680)
        self._build()
        self._connect()
        self._restore_geometry()
        self._refresh_target()
        self._refresh_sources()
        self._set_state("idle")
        i18n.bind(self, self._retitle)

    # ------------------------------------------------------------ first run
    def _first_run_defaults(self) -> None:
        c = self.controller
        from faceforge.core.hardware import runtime_settings

        self.settings.update(runtime_settings(c.hardware, c.models.device))
        c.apply_runtime()
        preset = default_preset(c.hardware)
        from faceforge.core.presets import preset_settings

        self.settings.update(preset_settings(preset, c.hardware, c.models.device))
        self.settings.set("preset", preset)
        self._show_welcome = True

    # ---------------------------------------------------------------- build
    def _build(self) -> None:
        root = QWidget()
        root.setObjectName("AppRoot")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        layout.addWidget(self._build_header())

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(12)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self._build_inputs())
        self.splitter.addWidget(self._build_center())
        self.settings_panel = SettingsPanel(self.controller)
        right = self._panel(self.settings_panel)
        right.setMinimumWidth(360)
        self.splitter.addWidget(right)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([300, 860, 380])
        layout.addWidget(self.splitter, 1)

        self._build_status()
        self.toast = Toast(root)

    @staticmethod
    def _panel(content: QWidget) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Panel")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(content)
        return frame

    def _build_header(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("HeaderBar")
        row = QHBoxLayout(bar)
        row.setContentsMargins(4, 0, 4, 0)
        row.setSpacing(10)
        self.logo = QLabel()
        row.addWidget(self.logo)
        title = QLabel("FaceForge")
        title.setObjectName("AppTitle")
        row.addWidget(title)
        badge = QLabel("LITE" if edition.is_lite() else "PRO")
        badge.setObjectName("EditionBadge")
        row.addWidget(badge)
        self.subtitle = QLabel()
        self.subtitle.setObjectName("Muted")
        bind_text(self.subtitle, "app.tagline")
        row.addWidget(self.subtitle)
        row.addStretch()
        self.about_btn = icon_button("info", "app.about")
        self.about_btn.clicked.connect(self._about)
        row.addWidget(self.about_btn)
        self.theme_btn = icon_button("sun", "app.toggle_theme")
        self.theme_btn.clicked.connect(self._toggle_theme)
        row.addWidget(self.theme_btn)
        sep = QFrame()
        sep.setFixedSize(1, 22)
        sep.setStyleSheet(f"background: {theme.tokens['border']};")
        self._sep = sep
        row.addWidget(sep)
        self.lang = LanguageSwitcher(self.settings.get("language"))
        row.addWidget(self.lang)
        return bar

    def _build_inputs(self) -> QFrame:
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        lay.addWidget(self._caption("input.source"))
        self.source_drop = DropZone("input.source.drop", "input.source.drop_hint", "user")
        lay.addWidget(self.source_drop)
        self.source_grid = ThumbGrid(columns=4, thumb_size=52, removable=True, selectable=False)
        lay.addWidget(self.source_grid)
        self.source_status = QLabel()
        self.source_status.setObjectName("Hint")
        self.source_status.setWordWrap(True)
        lay.addWidget(self.source_status)

        lay.addSpacing(8)
        lay.addWidget(self._caption("input.target"))
        self.target_drop = DropZone("input.target.drop", "input.target.drop_hint", "film")
        lay.addWidget(self.target_drop)
        self.target_info = TargetInfo()
        lay.addWidget(self.target_info)

        lay.addSpacing(8)
        lay.addWidget(self._caption("input.faces"))
        faces_row = QHBoxLayout()
        faces_row.setSpacing(8)
        self.faces_hint = QLabel()
        self.faces_hint.setObjectName("Hint")
        self.faces_hint.setWordWrap(True)
        faces_row.addWidget(self.faces_hint, 1)
        self.clear_ref = Button("input.faces.all", "link")
        self.clear_ref.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        faces_row.addWidget(self.clear_ref, 0, Qt.AlignmentFlag.AlignTop)
        lay.addLayout(faces_row)
        self.face_grid = ThumbGrid(columns=4, thumb_size=52, removable=False, selectable=True)
        lay.addWidget(self.face_grid)
        lay.addStretch()
        frame = self._panel(content)
        frame.setMinimumWidth(280)
        frame.setMaximumWidth(380)
        return frame

    @staticmethod
    def _caption(key: str) -> QLabel:
        label = QLabel()
        label.setObjectName("SectionTitle")
        bind_text(label, key)
        return label

    def _build_center(self) -> QFrame:
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(8)
        self.view_mode = Segmented([(MODE_ORIGINAL, "view.original", "image"),
                                    (MODE_SPLIT, "view.split", "split"),
                                    (MODE_RESULT, "view.result", "sparkles")])
        self.view_mode.setFixedWidth(360)
        self.view_mode.set_value(MODE_SPLIT)
        top.addWidget(self.view_mode)
        top.addStretch()
        self.preview_info = QLabel()
        self.preview_info.setObjectName("Hint")
        top.addWidget(self.preview_info)
        self.fit_btn = icon_button("zoom_fit", "view.fit")
        top.addWidget(self.fit_btn)
        self.refresh_btn = icon_button("refresh", "view.refresh")
        top.addWidget(self.refresh_btn)
        lay.addLayout(top)

        self.view = CompareView()
        i18n.bind(self.view, self._retranslate_view)
        lay.addWidget(self.view, 1)

        self.timeline = QWidget()
        tl = QHBoxLayout(self.timeline)
        tl.setContentsMargins(4, 0, 4, 0)
        self.time_label = QLabel("00:00")
        self.time_label.setObjectName("Value")
        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.duration_label = QLabel("00:00")
        self.duration_label.setObjectName("Value")
        tl.addWidget(self.time_label)
        tl.addWidget(self.frame_slider, 1)
        tl.addWidget(self.duration_label)
        lay.addWidget(self.timeline)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        progress_box = QVBoxLayout()
        progress_box.setSpacing(6)
        progress_box.setContentsMargins(4, 0, 12, 0)
        self.progress = SmoothProgress()
        self.progress_label = QLabel()
        self.progress_label.setObjectName("Hint")
        progress_box.addWidget(self.progress_label)
        progress_box.addWidget(self.progress)
        actions.addLayout(progress_box, 1)
        self.open_btn = Button("action.open_output", icon_name="folder")
        actions.addWidget(self.open_btn)
        self.pause_btn = Button(None, icon_name="pause")
        actions.addWidget(self.pause_btn)
        self.stop_btn = Button("action.stop", "danger", "stop")
        actions.addWidget(self.stop_btn)
        self.start_btn = Button(None, "primary", "play")
        self.start_btn.setMinimumWidth(160)
        self.start_btn.setMinimumHeight(40)
        actions.addWidget(self.start_btn)
        lay.addLayout(actions)
        return self._panel(content)

    def _build_status(self) -> None:
        bar = QStatusBar()
        bar.setSizeGripEnabled(False)
        bar.setContentsMargins(12, 0, 12, 0)
        self.setStatusBar(bar)
        self.device_chip = QLabel()
        self.device_chip.setObjectName("Chip")
        bar.addWidget(self.device_chip)
        self.profile_chip = QLabel()
        self.profile_chip.setObjectName("Chip")
        bar.addWidget(self.profile_chip)
        self.loading_label = QLabel()
        bar.addWidget(self.loading_label, 1)
        self.ram_label = QLabel()
        bar.addPermanentWidget(self.ram_label)
        self.vram_label = QLabel()
        bar.addPermanentWidget(self.vram_label)
        i18n.bind(bar, self._refresh_chips)

    # -------------------------------------------------------------- signals
    def _connect(self) -> None:
        c = self.controller
        self.lang.language_selected.connect(self._set_language)
        self.source_drop.clicked.connect(self._browse_sources)
        self.source_drop.files_dropped.connect(c.add_sources)
        self.source_grid.removed.connect(c.remove_source)
        self.target_drop.clicked.connect(self._browse_target)
        self.target_drop.files_dropped.connect(c.set_targets)
        self.view.files_dropped.connect(self._on_view_drop)
        self.target_info.clear_requested.connect(c.clear_target)
        self.face_grid.selected.connect(c.select_reference)
        self.clear_ref.clicked.connect(lambda: (c.select_reference(None), self.face_grid.set_selected(None)))
        self.view_mode.changed.connect(self.view.set_mode)
        self.fit_btn.clicked.connect(self.view.fit)
        self.refresh_btn.clicked.connect(lambda: c.request_preview(True))
        self.frame_slider.valueChanged.connect(self._on_scrub)
        self.frame_slider.sliderReleased.connect(lambda: c.seek(self.frame_slider.value()))
        self.start_btn.clicked.connect(c.start_job)
        self.pause_btn.clicked.connect(self._toggle_pause)
        self.stop_btn.clicked.connect(c.stop)
        self.open_btn.clicked.connect(self._open_output)
        self.settings_panel.open_model_manager.connect(lambda: self._show_models())

        c.source_changed.connect(self._refresh_sources)
        c.source_analyzed.connect(self._on_source_analyzed)
        c.target_changed.connect(self._refresh_target)
        c.target_faces_changed.connect(self._on_faces)
        c.preview_ready.connect(self._on_preview)
        c.preview_busy.connect(self._on_preview_busy)
        c.job_started.connect(lambda _k: self._set_state("running"))
        c.job_progress.connect(self._on_progress)
        c.job_finished.connect(self._on_finished)
        c.job_failed.connect(self._on_failed)
        c.job_cancelled.connect(self._on_cancelled)
        c.models_missing.connect(self._show_models)
        c.model_loading.connect(self._on_model_loading)
        c.message.connect(self._notify)
        c.settings_applied.connect(self._refresh_chips)

        self.monitor = ResourceMonitor(bool(c.hardware.nvidia_gpus), parent=self)
        self.monitor.updated.connect(self._on_stats)

        QShortcut(QKeySequence.StandardKey.Open, self, activated=self._browse_target)
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=c.start_job)
        self.restyle()

    # -------------------------------------------------------------- texts
    def _retitle(self) -> None:
        self.setWindowTitle(f"FaceForge {'Lite' if edition.is_lite() else 'Pro'} {__version__}")
        self._refresh_sources()
        self._refresh_target()
        self._set_state(self._state)

    def _retranslate_view(self) -> None:
        self.view.placeholder_title = tr("view.empty_title")
        self.view.placeholder_hint = tr("view.empty_hint")
        self.view.update()

    def _refresh_chips(self) -> None:
        c = self.controller
        adapter = c.models.adapter_name
        device = c.models.device_label + (f" · {adapter}" if adapter else "")
        self.device_chip.setText(device)
        self.profile_chip.setText(tr(f"profile.{self.settings.get('performance_profile')}"))

    def _notify(self, text: str, kind: str = "info") -> None:
        self.toast.show_message(tr(text) if text in TRANSLATIONS else text, kind)

    # -------------------------------------------------------------- inputs
    def _browse_sources(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, tr("input.source"), self.settings.get("last_open_dir"),
                                                f"{tr('filter.images')} ({IMAGE_FILTER})")
        if paths:
            self.settings.set("last_open_dir", str(Path(paths[0]).parent))
            self.controller.add_sources(paths)

    def _browse_target(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, tr("input.target"), self.settings.get("last_open_dir"),
            f"{tr('filter.media')} ({IMAGE_FILTER} {VIDEO_FILTER});;{tr('filter.images')} ({IMAGE_FILTER});;"
            f"{tr('filter.videos')} ({VIDEO_FILTER})")
        if paths:
            self.settings.set("last_open_dir", str(Path(paths[0]).parent))
            self.controller.set_targets(paths)

    def _on_view_drop(self, paths: list[str]) -> None:
        self.controller.set_targets(paths)

    def _refresh_sources(self) -> None:
        c = self.controller
        self.source_grid.set_images(c.source_images, [Path(p).name for p in c.source_paths])
        if not c.source_images:
            self.source_status.setText(tr("input.source.empty"))

    def _on_source_analyzed(self, count: int) -> None:
        if count:
            self.source_status.setText(tr("input.source.ready", count=count))
        else:
            self.source_status.setText(tr("input.source.no_face"))
            self._notify("input.source.no_face", "warning")

    def _refresh_target(self) -> None:
        c = self.controller
        has = c.target_kind != KIND_NONE
        self.target_info.setVisible(has)
        self.timeline.setVisible(c.target_kind == KIND_VIDEO)
        if not has:
            self.view.set_images(None)
            self.face_grid.set_images([])
            self.faces_hint.setText(tr("input.faces.empty"))
            self.preview_info.setText("")
            return
        frame = c.target_frame
        name = Path(c.target_paths[0]).name
        if c.target_kind == KIND_VIDEO and c.video_info:
            info = c.video_info
            meta = tr("input.target.video_meta", w=info.width, h=info.height, fps=f"{info.fps:.2f}",
                      duration=_fmt_time(info.duration))
            self.frame_slider.blockSignals(True)
            self.frame_slider.setRange(0, max(0, info.frame_count - 1))
            self.frame_slider.setValue(c.frame_index)
            self.frame_slider.blockSignals(False)
            self.duration_label.setText(_fmt_time(info.duration))
            self._on_scrub(c.frame_index)
        elif c.target_kind == KIND_BATCH:
            name = tr("input.target.batch_name", count=len(c.target_paths))
            meta = tr("input.target.batch_meta")
        else:
            h, w = frame.shape[:2] if frame is not None else (0, 0)
            meta = tr("input.target.image_meta", w=w, h=h)
        self.target_info.set_target(frame, name, meta)
        if frame is not None and not self.view.has_image():
            self.view.set_images(frame, None, reset_view=True)
        elif frame is not None:
            self.view.set_images(frame, None)

    def _on_scrub(self, value: int) -> None:
        info = self.controller.video_info
        if info and info.fps:
            self.time_label.setText(_fmt_time(value / info.fps))

    def _on_faces(self, thumbs: list) -> None:
        c = self.controller
        self.face_grid.set_images(thumbs, [f"#{i + 1}" for i in range(len(thumbs))])
        self.face_grid.set_selected(c.reference_index)
        if not thumbs:
            self.faces_hint.setText(tr("input.faces.none_found") if c.target_frame is not None
                                    else tr("input.faces.empty"))
        else:
            self.faces_hint.setText(tr("input.faces.hint", count=len(thumbs)))

    # ------------------------------------------------------------- preview
    def _on_preview(self, before, after, seconds: float) -> None:
        self.view.set_images(before, after)
        if after is not None:
            self.preview_info.setText(tr("view.preview_time", ms=int(seconds * 1000)))
        else:
            self.preview_info.setText(tr("view.need_source") if self.controller.source_embedding is None else "")

    def _on_preview_busy(self, busy: bool) -> None:
        self.view.set_busy(busy)
        if busy:
            self.preview_info.setText(tr("view.rendering"))

    def _on_model_loading(self, key: str, on: bool) -> None:
        from faceforge.core.models_data import MODELS

        self.loading_label.setText(tr("status.loading_model", name=MODELS[key].title) if on else "")

    def _on_stats(self, stats: dict) -> None:
        self.ram_label.setText(tr("status.ram", used=_gb(stats["ram_used"]), total=_gb(stats["ram_total"]),
                                  app=_gb(stats["app_ram"])))
        if stats["vram_total"]:
            self.vram_label.setText(tr("status.vram", used=_gb(stats["vram_used"]), total=_gb(stats["vram_total"])))
        else:
            self.vram_label.setText("")

    # ---------------------------------------------------------------- jobs
    def _set_state(self, state: str) -> None:
        self._state = state
        running = state in ("running", "paused")
        self.start_btn.setEnabled(not running)
        self.pause_btn.setVisible(running)
        self.stop_btn.setVisible(running)
        self.open_btn.setVisible(not running and bool(self.controller.last_output))
        self.progress.setVisible(running)
        self.start_btn.setText(tr("action.processing") if running else tr("action.start"))
        self.pause_btn.setText(tr("action.resume") if state == "paused" else tr("action.pause"))
        self.pause_btn.icon_name = "play" if state == "paused" else "pause"
        if state == "running" and self.progress.value() and self._state_prev not in ("running", "paused"):
            self.progress.set_fraction(0)
        self._state_prev = state
        self.source_drop.setEnabled(not running)
        self.target_drop.setEnabled(not running)
        self.settings_panel.setEnabled(not running)
        if not running:
            self.progress_label.setText(tr("action.ready_hint") if state == "idle" else self.progress_label.text())

    def _toggle_pause(self) -> None:
        paused = self._state != "paused"
        self.controller.pause(paused)
        self._set_state("paused" if paused else "running")

    def _on_progress(self, done: int, total: int, fps: float) -> None:
        self.progress.set_fraction(done / max(1, total))
        eta = (total - done) / fps if fps > 0 else 0
        self.progress_label.setText(tr("progress.text", done=done, total=total, fps=f"{fps:.1f}",
                                       eta=_fmt_time(eta)))

    def _on_finished(self, path: str, resumed: int) -> None:
        self._set_state("done")
        self.progress_label.setText(tr("progress.done", path=path))
        if resumed:
            self._notify(tr("progress.resumed", frame=resumed), "info")
        self._notify("progress.done_toast", "success")
        QApplication.alert(self)

    def _on_failed(self, error: str) -> None:
        self._set_state("idle")
        self.progress_label.setText(tr("progress.failed"))
        QMessageBox.critical(self, tr("progress.failed"), error)

    def _on_cancelled(self) -> None:
        self._set_state("idle")
        self.progress_label.setText(tr("progress.cancelled"))

    def _open_output(self) -> None:
        if self.controller.last_output:
            self.controller.open_path(self.controller.last_output)

    # -------------------------------------------------------------- dialogs
    def _show_models(self, required: list[str] | None = None) -> None:
        if self._dialog is not None and self._dialog.isVisible():
            return
        self._dialog = ModelManagerDialog(self.controller, required, self)
        accepted = self._dialog.exec() == ModelManagerDialog.DialogCode.Accepted
        self._dialog = None
        if required is not None:
            self.controller.resume_after_download(accepted and not self.controller.models.missing(required))

    def _about(self) -> None:
        hw = self.controller.hardware
        QMessageBox.about(self, tr("app.about"), tr(
            "app.about_text", version=__version__, edition="Lite" if edition.is_lite() else "Pro",
            hardware=hw.summary(), device=self.controller.models.device_label))

    def maybe_welcome(self) -> None:
        if not getattr(self, "_show_welcome", False):
            return
        self._show_welcome = False
        hw = self.controller.hardware
        text = tr("welcome.text", hardware=hw.summary(), preset=tr(f"preset.{self.settings.get('preset')}"))
        if not edition.is_lite() and not meets_pro_requirements(hw):
            text += "\n\n" + tr("welcome.pro_warning")
        QMessageBox.information(self, tr("welcome.title"), text)
        self.settings.set("first_run_done", True)
        self.settings.save()

    # ---------------------------------------------------------- appearance
    def _set_language(self, code: str) -> None:
        self.settings.set("language", code)
        i18n.set_language(code)

    def _toggle_theme(self) -> None:
        name = "light" if theme.name == "dark" else "dark"
        self.settings.set("theme", name)
        theme.apply(QApplication.instance(), name)
        self.restyle()

    def restyle(self) -> None:
        """Re-tint icons and custom-painted widgets after a theme change."""
        t = theme.tokens
        self.logo.setPixmap(icons.pixmap("logo", t["accent_hover"], 26))
        self.theme_btn.set_icon("moon" if theme.name == "dark" else "sun")
        self._sep.setStyleSheet(f"background: {t['border']};")
        for widget in self.findChildren(QWidget):
            restyle = getattr(widget, "restyle", None)
            if callable(restyle) and widget is not self:
                restyle()
        self._set_state(self._state)
        self.update()

    # ------------------------------------------------------------ lifecycle
    def _restore_geometry(self) -> None:
        geometry = self.settings.get("window_geometry")
        if geometry:
            self.restoreGeometry(QByteArray.fromBase64(geometry.encode()))
        else:
            self.resize(1440, 860)
        state = self.settings.get("splitter_state")
        if state:
            self.splitter.restoreState(QByteArray.fromBase64(state.encode()))

    def showEvent(self, event) -> None:
        super().showEvent(event)
        platform = QApplication.platformName()
        if not self._faded_in and platform not in ("offscreen", "minimal", "wayland"):
            # Gentle fade-in on launch (window opacity isn't supported everywhere).
            self._faded_in = True
            self.setWindowOpacity(0.0)
            self._fade = QPropertyAnimation(self, b"windowOpacity", self)
            self._fade.setDuration(260)
            self._fade.setStartValue(0.0)
            self._fade.setEndValue(1.0)
            self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._fade.start()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.toast.isVisible():
            self.toast._place()

    def closeEvent(self, event) -> None:
        if self.controller.is_busy():
            answer = QMessageBox.question(self, tr("app.quit_title"), tr("app.quit_busy"))
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        self.settings.set("window_geometry", bytes(self.saveGeometry().toBase64()).decode())
        self.settings.set("splitter_state", bytes(self.splitter.saveState().toBase64()).decode())
        self.settings.save()
        self.controller.shutdown()
        event.accept()
