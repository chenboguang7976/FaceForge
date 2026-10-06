"""Design tokens and the generated Qt stylesheet (dark / light)."""
from __future__ import annotations

import sys

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

TOKENS = {
    "dark": {
        "bg": "#0d0e12", "surface": "#15171d", "surface2": "#1b1e26", "surface3": "#232733",
        "border": "#2a2f3b", "border_strong": "#3a4050",
        "text": "#e9ebf1", "muted": "#9aa1b0", "faint": "#6b7282",
        "accent": "#7c5cff", "accent_hover": "#8f75ff", "accent_press": "#6a4cf0",
        "accent_soft": "rgba(124, 92, 255, 0.16)", "on_accent": "#ffffff",
        "success": "#22c55e", "warning": "#f59e0b", "danger": "#ef4444",
        "preview_bg": "#08090c",
    },
    "light": {
        "bg": "#f3f4f8", "surface": "#ffffff", "surface2": "#f6f7fa", "surface3": "#eceef3",
        "border": "#e1e4ea", "border_strong": "#cdd2db",
        "text": "#151821", "muted": "#5c6474", "faint": "#8a91a0",
        "accent": "#6a4cf0", "accent_hover": "#7c5cff", "accent_press": "#5a3de0",
        "accent_soft": "rgba(106, 76, 240, 0.12)", "on_accent": "#ffffff",
        "success": "#16a34a", "warning": "#d97706", "danger": "#dc2626",
        "preview_bg": "#e6e8ee",
    },
}


def font_families() -> list[str]:
    # Latin/Vietnamese first, then a CJK fallback so 中文 renders crisply.
    if sys.platform == "win32":
        return ["Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI"]
    if sys.platform == "darwin":
        return [".AppleSystemUIFont", "Helvetica Neue", "PingFang SC"]
    return ["Inter", "Noto Sans", "Ubuntu", "DejaVu Sans", "Noto Sans CJK SC", "WenQuanYi Micro Hei"]


def stylesheet(t: dict, chevron: str = "", chevron_up: str = "") -> str:
    return f"""
* {{ outline: none; }}
QWidget {{ color: {t['text']}; font-size: 10pt; }}
QMainWindow, QDialog {{ background: {t['bg']}; }}
QWidget#AppRoot {{ background: {t['bg']}; }}
QToolTip {{ background: {t['surface3']}; color: {t['text']}; border: 1px solid {t['border_strong']};
            padding: 6px 8px; border-radius: 6px; }}

/* Panels & cards */
QFrame#Panel {{ background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 16px; }}
QFrame#Card {{ background: {t['surface2']}; border: 1px solid {t['border']}; border-radius: 12px; }}
QFrame#HeaderBar {{ background: transparent; }}
QLabel#AppTitle {{ font-size: 15pt; font-weight: 700; }}
QLabel#EditionBadge {{ background: {t['accent_soft']}; color: {t['accent_hover']}; border-radius: 9px;
                       padding: 2px 9px; font-size: 8pt; font-weight: 700; letter-spacing: 1px; }}
QLabel#SectionTitle {{ font-size: 10.5pt; font-weight: 650; }}
QLabel#Muted, QLabel#Hint {{ color: {t['muted']}; }}
QLabel#Hint {{ font-size: 8.5pt; }}
QLabel#Value {{ color: {t['muted']}; }}
QLabel#Warning {{ color: {t['warning']}; }}

/* Buttons */
QPushButton, QToolButton {{ background: {t['surface3']}; border: 1px solid {t['border']}; border-radius: 10px;
                            padding: 0 16px; min-height: 34px; color: {t['text']}; }}
QPushButton:hover, QToolButton:hover {{ border-color: {t['border_strong']}; background: {t['surface2']}; }}
QPushButton:pressed, QToolButton:pressed {{ background: {t['surface']}; }}
QPushButton:disabled, QToolButton:disabled {{ color: {t['faint']}; background: {t['surface2']}; }}
QPushButton#Primary {{ background: {t['accent']}; border: 1px solid {t['accent']}; color: {t['on_accent']};
                       font-weight: 650; padding: 9px 20px; }}
QPushButton#Primary:hover {{ background: {t['accent_hover']}; border-color: {t['accent_hover']}; }}
QPushButton#Primary:pressed {{ background: {t['accent_press']}; }}
QPushButton#Primary:disabled {{ background: {t['surface3']}; border-color: {t['border']}; color: {t['faint']}; }}
QPushButton#Danger:hover {{ border-color: {t['danger']}; color: {t['danger']}; }}
QToolButton#Flag {{ background: transparent; border: 2px solid transparent; border-radius: 8px; padding: 3px; min-height: 0; }}
QToolButton#Flag:hover {{ border-color: {t['border_strong']}; }}
QToolButton#Flag:checked {{ border-color: {t['accent']}; background: {t['accent_soft']}; }}

/* Inputs */
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {{ background: {t['surface2']}; border: 1px solid {t['border']};
    border-radius: 8px; padding: 0 12px; min-height: 34px; max-height: 34px; selection-background-color: {t['accent']}; }}
QComboBox {{ padding-right: 30px; }}
QComboBox:hover, QSpinBox:hover, QLineEdit:hover {{ border-color: {t['border_strong']}; }}
QComboBox:focus, QSpinBox:focus, QLineEdit:focus {{ border-color: {t['accent']}; }}
QComboBox::drop-down {{ border: none; width: 30px; subcontrol-origin: padding; subcontrol-position: center right; }}
QComboBox::down-arrow {{ image: url({chevron}); width: 12px; height: 12px; }}
QComboBox::down-arrow:on {{ image: url({chevron_up}); }}
QComboBox QAbstractItemView {{ background: {t['surface']}; border: 1px solid {t['border_strong']};
    padding: 4px; outline: none; selection-background-color: {t['accent_soft']}; selection-color: {t['text']}; }}
QComboBox QAbstractItemView::item {{ min-height: 30px; padding: 0 8px; border-radius: 6px; }}
QSpinBox {{ padding: 0 8px; qproperty-alignment: AlignCenter; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: 0; border: none; }}

/* Sliders */
QSlider::groove:horizontal {{ height: 4px; background: {t['surface3']}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {t['accent']}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: #ffffff; border: 2px solid {t['accent']}; width: 12px; height: 12px;
                              margin: -6px 0; border-radius: 8px; }}
QSlider::handle:horizontal:hover {{ background: {t['accent_hover']}; }}
QSlider::groove:horizontal:disabled {{ background: {t['surface2']}; }}
QSlider::sub-page:horizontal:disabled {{ background: {t['border_strong']}; }}
QSlider::handle:horizontal:disabled {{ border-color: {t['border_strong']}; }}

/* Check boxes rendered as switches by ToggleSwitch; plain ones stay simple */
QCheckBox {{ spacing: 8px; }}

/* Progress */
QProgressBar {{ background: {t['surface3']}; border: none; border-radius: 3px; max-height: 6px; min-height: 6px;
                text-align: center; color: transparent; }}
QProgressBar::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {t['accent']}, stop:1 #4fc3f7);
                       border-radius: 3px; }}

/* Scroll areas */
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {t['surface3']}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {t['border_strong']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {t['surface3']}; border-radius: 4px; min-width: 30px; }}

/* Splitter, status bar, menus */
QSplitter::handle {{ background: transparent; }}
QStatusBar {{ background: {t['surface']}; border-top: 1px solid {t['border']}; color: {t['muted']}; }}
QStatusBar {{ min-height: 30px; }}
QStatusBar::item {{ border: none; }}
QStatusBar QLabel {{ color: {t['muted']}; padding: 0 6px; }}
QLabel#Chip {{ background: {t['surface3']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 2px 10px;
               color: {t['text']}; font-size: 8.5pt; }}
QMenu {{ background: {t['surface']}; border: 1px solid {t['border_strong']}; border-radius: 10px; padding: 4px; }}
QMenu::item {{ padding: 6px 18px; border-radius: 6px; }}
QMenu::item:selected {{ background: {t['accent_soft']}; }}

/* Lists & tables (model manager) */
QTableWidget {{ background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 12px;
                gridline-color: transparent; alternate-background-color: {t['surface2']}; }}
QHeaderView::section {{ background: {t['surface2']}; border: none; border-bottom: 1px solid {t['border']};
                        padding: 6px; color: {t['muted']}; font-weight: 600; }}
QTableWidget::item {{ padding: 4px; }}
QTableWidget::item:selected {{ background: {t['accent_soft']}; color: {t['text']}; }}
"""


def _chevrons(name: str, color: str) -> tuple[str, str]:
    """QSS can only load arrow images from files, so write tiny SVGs once."""
    from faceforge.helpers.paths import temp_dir

    folder = temp_dir() / "ui"
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for suffix, d in (("down", "M3 4.5l3 3 3-3"), ("up", "M3 7.5l3-3 3 3")):
        path = folder / f"chevron_{name}_{suffix}.svg"
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12"><path d="{d}" fill="none" '
               f'stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
        try:
            if not path.exists() or path.read_text("utf-8") != svg:
                path.write_text(svg, "utf-8")
        except OSError:
            return "", ""
        paths.append(path.as_posix())
    return paths[0], paths[1]


class ThemeManager:
    def __init__(self) -> None:
        self.name = "dark"

    @property
    def tokens(self) -> dict:
        return TOKENS[self.name]

    def apply(self, app: QApplication, name: str = "dark") -> None:
        self.name = name if name in TOKENS else "dark"
        t = self.tokens
        app.setStyle("Fusion")
        font = QFont()
        font.setFamilies(font_families())
        font.setPointSizeF(10)
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        app.setFont(font)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(t["bg"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(t["surface2"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(t["surface"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(t["text"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(t["text"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(t["surface3"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(t["text"]))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(t["accent"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(t["on_accent"]))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(t["faint"]))
        app.setPalette(palette)
        down, up = _chevrons(self.name, t["muted"])
        app.setStyleSheet(stylesheet(t, down, up))


theme = ThemeManager()
