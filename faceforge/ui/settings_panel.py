"""Right-hand settings panel: one-click presets plus grouped, collapsible options."""
from __future__ import annotations

import threading

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QButtonGroup, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QScrollArea, QSpinBox, QVBoxLayout, QWidget)

from faceforge.core.models_data import models_in
from faceforge.core.presets import PRESET_CUSTOM, PRESETS
from faceforge.helpers import ffmpeg
from faceforge.ui.controller import Controller
from faceforge.ui.i18n import bind_text, i18n, tr
from faceforge.ui.widgets.animated import Button, Segmented, Tile
from faceforge.ui.widgets.controls import ComboRow, Row, Section, SliderRow, SwitchRow

PRESET_ICONS = {"performance": "gauge", "balanced": "layers", "quality": "sparkles", "maximum": "wand"}


class SettingsPanel(QWidget):
    open_model_manager = Signal()

    def __init__(self, controller: Controller, parent=None):
        super().__init__(parent)
        self.c = controller
        self.s = controller.settings
        self._loading = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 8, 16)
        outer.setSpacing(12)

        # ---- Presets -------------------------------------------------------
        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 8, 0)
        title = QLabel()
        title.setObjectName("SectionTitle")
        bind_text(title, "preset.title")
        head.addWidget(title)
        head.addStretch()
        self.custom_badge = QLabel()
        self.custom_badge.setObjectName("Chip")
        bind_text(self.custom_badge, "preset.custom")
        head.addWidget(self.custom_badge)
        outer.addLayout(head)

        tiles = QGridLayout()
        tiles.setSpacing(8)
        self.preset_group = QButtonGroup(self)
        self.preset_buttons: dict[str, Tile] = {}
        for index, name in enumerate(PRESETS):
            button = Tile(PRESET_ICONS[name], f"preset.{name}")
            i18n.bind(button, lambda b=button, n=name: b.setToolTip(tr(f"preset.{n}.hint")))
            button.clicked.connect(lambda _=False, n=name: self.c.apply_preset(n))
            self.preset_group.addButton(button)
            self.preset_buttons[name] = button
            tiles.addWidget(button, 0, index)
        tiles_box = QWidget()
        tiles_box.setLayout(tiles)
        tiles.setContentsMargins(0, 0, 8, 0)
        outer.addWidget(tiles_box)

        # ---- Scrollable sections ------------------------------------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        self.sections = QVBoxLayout(body)
        self.sections.setContentsMargins(0, 0, 8, 0)
        self.sections.setSpacing(2)
        self.sections.setSpacing(0)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        self._build_swap()
        self._build_enhancer()
        self._build_mask()
        self._build_selector()
        self._build_detector()
        self._build_output()
        self._build_system()
        self.sections.addStretch()

        controller.settings_applied.connect(self.load)
        self.load()
        self._detect_encoders()

    # --------------------------------------------------------------- helpers
    def _set(self, key: str, value) -> None:
        if not self._loading:
            self.c.set_option(key, value)

    def _section(self, key: str, icon: str, expanded: bool = True) -> Section:
        section = Section(key, icon, expanded)
        self.sections.addWidget(section)
        return section

    # -------------------------------------------------------------- sections
    def _build_swap(self) -> None:
        sec = self._section("swap.title", "user")
        self.swap_enabled = sec.add(SwitchRow("swap.enabled", "swap.enabled.hint"))
        self.swap_enabled.switch.toggled.connect(lambda v: self._set("face_swap_enabled", v))
        self.swap_model = sec.add(ComboRow("swap.model", [(m.key, m.title) for m in models_in("swapper")],
                                           translate=False, hint_key="swap.model.hint"))
        self.swap_model.combo.currentIndexChanged.connect(self._on_swap_model)
        self.pixel_boost = sec.add(ComboRow("swap.boost", [], translate=False, hint_key="swap.boost.hint"))
        self.pixel_boost.combo.currentIndexChanged.connect(
            lambda _: self._set("face_swapper_pixel_boost", self.pixel_boost.value_of()))
        self.color_match = sec.add(SwitchRow("swap.color_match", "swap.color_match.hint"))
        self.color_match.switch.toggled.connect(lambda v: self._set("face_color_match", v))

    def _fill_boost(self, model: str) -> None:
        native = 256 if model.startswith("hyperswap") else 128
        sizes = [native * n for n in (1, 2, 3, 4) if native * n <= 512]
        combo = self.pixel_boost.combo
        combo.blockSignals(True)
        combo.clear()
        for size in sizes:
            passes = (size // native) ** 2
            combo.addItem(f"{size}×{size}  ·  {passes}×", size)
        self.pixel_boost._items = [(s, combo.itemText(i)) for i, s in enumerate(sizes)]
        current = int(self.s.get("face_swapper_pixel_boost"))
        index = combo.findData(current)
        if index < 0:
            index = 0
            for i, size in enumerate(sizes):
                if size <= current:
                    index = i
        combo.setCurrentIndex(index)
        combo.blockSignals(False)
        if combo.currentData() != current and not self._loading:
            self._set("face_swapper_pixel_boost", combo.currentData())

    def _on_swap_model(self) -> None:
        model = self.swap_model.value_of()
        self._fill_boost(model)
        self._set("face_swapper_model", model)

    def _build_enhancer(self) -> None:
        sec = self._section("enhance.title", "sparkles")
        self.enh_enabled = sec.add(SwitchRow("enhance.enabled", "enhance.enabled.hint"))
        self.enh_enabled.switch.toggled.connect(lambda v: self._set("face_enhancer_enabled", v))
        self.enh_model = sec.add(ComboRow("enhance.model", [(m.key, m.title) for m in models_in("enhancer")],
                                          translate=False))
        self.enh_model.combo.currentIndexChanged.connect(self._on_enh_model)
        self.enh_blend = sec.add(SliderRow("enhance.blend", 0, 100, lambda v: f"{v}%", "enhance.blend.hint"))
        self.enh_blend.value_changed.connect(lambda v: self._set("face_enhancer_blend", v))
        self.fidelity = sec.add(SliderRow("enhance.fidelity", 0, 100, lambda v: f"{v / 100:.2f}",
                                          "enhance.fidelity.hint"))
        self.fidelity.value_changed.connect(lambda v: self._set("codeformer_fidelity", v / 100))

    def _on_enh_model(self) -> None:
        model = self.enh_model.value_of()
        self.fidelity.setVisible(model == "codeformer")
        self._set("face_enhancer_model", model)

    def _build_mask(self) -> None:
        sec = self._section("mask.title", "scan_face", expanded=False)
        self.mask_blur = sec.add(SliderRow("mask.blur", 0, 100, lambda v: f"{v}%", "mask.blur.hint"))
        self.mask_blur.value_changed.connect(lambda v: self._set("face_mask_blur", v / 100))
        self.occlusion = sec.add(SwitchRow("mask.occlusion", "mask.occlusion.hint"))
        self.occlusion.switch.toggled.connect(lambda v: self._set("face_mask_occlusion", v))
        self.region = sec.add(SwitchRow("mask.region", "mask.region.hint"))
        self.region.switch.toggled.connect(lambda v: self._set("face_mask_region", v))

        pad = QWidget()
        grid = QGridLayout(pad)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        self.padding: list[QSpinBox] = []
        for i, key in enumerate(("mask.pad_top", "mask.pad_right", "mask.pad_bottom", "mask.pad_left")):
            label = QLabel()
            label.setObjectName("Hint")
            bind_text(label, key)
            spin = QSpinBox()
            spin.setRange(0, 50)
            spin.setSuffix("%")
            spin.valueChanged.connect(self._on_padding)
            grid.addWidget(label, 0, i)
            grid.addWidget(spin, 1, i)
            self.padding.append(spin)
        sec.add(Row("mask.padding", pad, "mask.padding.hint", stacked=True))

    def _on_padding(self) -> None:
        self._set("face_mask_padding", [s.value() for s in self.padding])

    def _build_selector(self) -> None:
        sec = self._section("select.title", "target", expanded=False)
        self.selector = Segmented([("all", "select.all", None), ("largest", "select.largest", None),
                                   ("reference", "select.reference", None)])
        self.selector.changed.connect(self._on_selector)
        sec.add(Row("select.mode", self.selector, "select.mode.hint", stacked=True))
        self.ref_distance = sec.add(SliderRow("select.distance", 10, 120, lambda v: f"{v / 100:.2f}",
                                              "select.distance.hint"))
        self.ref_distance.value_changed.connect(lambda v: self._set("reference_face_distance", v / 100))

    def _on_selector(self, mode: str) -> None:
        self.ref_distance.setVisible(mode == "reference")
        self._set("face_selector_mode", mode)

    def _build_detector(self) -> None:
        sec = self._section("detect.title", "eye", expanded=False)
        self.det_model = sec.add(ComboRow("detect.model", [(m.key, m.title) for m in models_in("detector")],
                                          translate=False))
        self.det_model.combo.currentIndexChanged.connect(self._on_det_model)
        self.det_size = sec.add(ComboRow("detect.size", [(s, f"{s}×{s}") for s in (320, 480, 640, 800, 1024)],
                                         translate=False, hint_key="detect.size.hint"))
        self.det_size.combo.currentIndexChanged.connect(lambda _: self._set("face_detector_size", self.det_size.value_of()))
        self.det_score = sec.add(SliderRow("detect.score", 10, 95, lambda v: f"{v / 100:.2f}", "detect.score.hint"))
        self.det_score.value_changed.connect(lambda v: self._set("face_detector_score", v / 100))

    def _on_det_model(self) -> None:
        model = self.det_model.value_of()
        # RetinaFace and YOLOFace graphs only accept 640×640.
        self.det_size.setEnabled(model == "scrfd")
        self._set("face_detector_model", model)

    def _build_output(self) -> None:
        sec = self._section("output.title", "folder", expanded=False)
        folder = QWidget()
        row = QHBoxLayout(folder)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        self.out_folder = QLineEdit()
        self.out_folder.setReadOnly(True)
        browse = Button("common.browse")
        browse.clicked.connect(self._browse_output)
        row.addWidget(self.out_folder, 1)
        row.addWidget(browse)
        sec.add(Row("output.folder", folder, stacked=True))
        self.img_format = sec.add(ComboRow("output.image_format",
                                           [("png", "PNG"), ("jpg", "JPEG"), ("webp", "WebP")], translate=False))
        self.img_format.combo.currentIndexChanged.connect(
            lambda _: self._set("output_image_format", self.img_format.value_of()))
        self.img_quality = sec.add(SliderRow("output.image_quality", 50, 100, str))
        self.img_quality.value_changed.connect(lambda v: self._set("output_image_quality", v))
        self.vid_quality = sec.add(SliderRow("output.video_quality", 30, 100, str, "output.video_quality.hint"))
        self.vid_quality.value_changed.connect(lambda v: self._set("output_video_quality", v))
        self.encoder = sec.add(ComboRow("output.encoder", [("auto", "output.encoder.auto")],
                                        hint_key="output.encoder.hint"))
        self.encoder.combo.currentIndexChanged.connect(lambda _: self._set("output_video_encoder", self.encoder.value_of()))
        self.keep_audio = sec.add(SwitchRow("output.keep_audio"))
        self.keep_audio.switch.toggled.connect(lambda v: self._set("keep_audio", v))

    def _browse_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, tr("output.folder"), str(self.s.output_dir))
        if path:
            self.out_folder.setText(path)
            self._set("output_folder", path)

    def _detect_encoders(self) -> None:
        """Probing hardware encoders runs ffmpeg a few times; keep it off the UI thread."""
        def work():
            names = ffmpeg.available_encoders()
            self.c._deliver(self._fill_encoders, names)

        threading.Thread(target=work, daemon=True, name="ff-encoders").start()

    def _fill_encoders(self, names: list[str]) -> None:
        labels = {"h264_nvenc": "NVIDIA NVENC", "h264_qsv": "Intel Quick Sync", "h264_amf": "AMD AMF",
                  "h264_videotoolbox": "Apple VideoToolbox", "libx264": "x264 (CPU)"}
        combo = self.encoder.combo
        combo.blockSignals(True)
        for name in names:
            if combo.findData(name) < 0:
                combo.addItem(labels.get(name, name), name)
                self.encoder._items.append((name, labels.get(name, name)))
        self.encoder._translate = True
        combo.blockSignals(False)
        # Hardware names are not translation keys; tr() returns them unchanged.
        self.encoder.set_value(self.s.get("output_video_encoder"))

    def _build_system(self) -> None:
        sec = self._section("system.title", "cpu", expanded=False)
        hw = self.c.hardware
        devices = [("auto", "system.device.auto")]
        if hw.has_cuda:
            devices.append(("cuda", "NVIDIA CUDA"))
        if hw.has_directml:
            devices.append(("directml", "DirectML"))
        if hw.has_coreml:
            devices.append(("coreml", "Apple CoreML"))
        devices.append(("cpu", "CPU"))
        self.device = sec.add(ComboRow("system.device", devices, hint_key="system.device.hint"))
        self.device.combo.currentIndexChanged.connect(lambda _: self._set("device", self.device.value_of()))
        gpus = [(-1, "system.gpu.auto")]
        if hw.has_directml:
            gpus += [(a.index, f"{a.name} ({a.vram_mb // 1024} GB)" if a.vram_mb >= 1024 else a.name)
                     for a in hw.dml_adapters if not a.software]
        elif hw.has_cuda:
            gpus += [(i, g.name) for i, g in enumerate(hw.nvidia_gpus)]
        self.gpu = sec.add(ComboRow("system.gpu", gpus, hint_key="system.gpu.hint"))
        self.gpu.setVisible(len(gpus) > 2)  # only worth showing with a real choice
        self.gpu.combo.currentIndexChanged.connect(lambda _: self._set("gpu_device_id", self.gpu.value_of()))
        self.workers = sec.add(SliderRow("system.workers", 1, 8, str, "system.workers.hint"))
        self.workers.value_changed.connect(lambda v: self._set("execution_workers", v))
        self.max_models = sec.add(SliderRow("system.max_models", 1, 10, str, "system.max_models.hint"))
        self.max_models.value_changed.connect(lambda v: self._set("max_loaded_models", v))

        buttons = QWidget()
        row = QHBoxLayout(buttons)
        row.setContentsMargins(0, 4, 0, 0)
        row.setSpacing(8)
        recommended = Button("system.recommended", icon_name="wand")
        recommended.clicked.connect(self.c.apply_recommended_runtime)
        manager = Button("models.manage", icon_name="box")
        manager.clicked.connect(self.open_model_manager.emit)
        row.addWidget(recommended, 1)
        row.addWidget(manager, 1)
        sec.add(buttons)

        self.active_label = QLabel()
        self.active_label.setWordWrap(True)
        self.active_label.setStyleSheet("font-weight: 600;")
        sec.add(self.active_label)
        self.hw_label = QLabel()
        self.hw_label.setObjectName("Hint")
        self.hw_label.setWordWrap(True)
        sec.add(self.hw_label)
        i18n.bind(self.active_label, self._refresh_device_text)
        self.c.runtime_changed.connect(self._refresh_device_text)

    def _refresh_device_text(self) -> None:
        models = self.c.models
        device = models.device_label + (f" · {models.adapter_name}" if models.adapter_name else "")
        self.active_label.setText(tr("system.active", device=device))
        self.hw_label.setText(tr("system.detected", hardware=self.c.hardware.summary()))

    # ------------------------------------------------------------------ sync
    def load(self) -> None:
        """Push settings into every control (after a preset or startup)."""
        self._loading = True
        s = self.s
        preset = s.get("preset")
        self.preset_group.setExclusive(False)
        for name, button in self.preset_buttons.items():
            button.set_checked_now(name == preset)
        self.preset_group.setExclusive(True)
        self.custom_badge.setVisible(preset == PRESET_CUSTOM)

        self.swap_enabled.set_value(s.get("face_swap_enabled"))
        self.swap_model.set_value(s.get("face_swapper_model"))
        self._fill_boost(s.get("face_swapper_model"))
        self.color_match.set_value(s.get("face_color_match"))

        self.enh_enabled.set_value(s.get("face_enhancer_enabled"))
        self.enh_model.set_value(s.get("face_enhancer_model"))
        self.enh_blend.set_value(s.get("face_enhancer_blend"))
        self.fidelity.set_value(round(float(s.get("codeformer_fidelity")) * 100))
        self.fidelity.setVisible(s.get("face_enhancer_model") == "codeformer")

        self.mask_blur.set_value(round(float(s.get("face_mask_blur")) * 100))
        self.occlusion.set_value(s.get("face_mask_occlusion"))
        self.region.set_value(s.get("face_mask_region"))
        for spin, value in zip(self.padding, s.get("face_mask_padding")):
            spin.blockSignals(True)
            spin.setValue(int(value))
            spin.blockSignals(False)

        self.selector.set_value(s.get("face_selector_mode"))
        self.ref_distance.set_value(round(float(s.get("reference_face_distance")) * 100))
        self.ref_distance.setVisible(s.get("face_selector_mode") == "reference")

        self.det_model.set_value(s.get("face_detector_model"))
        self.det_size.set_value(int(s.get("face_detector_size")))
        self.det_size.setEnabled(s.get("face_detector_model") == "scrfd")
        self.det_score.set_value(round(float(s.get("face_detector_score")) * 100))

        self.out_folder.setText(str(s.output_dir))
        self.img_format.set_value(s.get("output_image_format"))
        self.img_quality.set_value(s.get("output_image_quality"))
        self.vid_quality.set_value(s.get("output_video_quality"))
        self.encoder.set_value(s.get("output_video_encoder"))
        self.keep_audio.set_value(s.get("keep_audio"))

        self.device.set_value(s.get("device"))
        self.gpu.set_value(int(s.get("gpu_device_id")))
        self.workers.set_value(s.get("execution_workers"))
        self.max_models.set_value(s.get("max_loaded_models"))
        self._loading = False
