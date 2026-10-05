"""Theme and styling management for FaceForge."""
import os
from typing import Optional

from PySide6.QtWidgets import QApplication

class ThemeManager:
    """Manages light and dark themes using QSS."""

    def __init__(self):
        self.current_theme = "dark"
        # Assuming run.py is in root, stylesheets are relative to module
        self.style_dir = os.path.join(os.path.dirname(__file__), "styles")

    def apply_theme(self, app: QApplication, theme_name: str = "dark") -> bool:
        """Apply a stylesheet to the application."""
        self.current_theme = theme_name
        qss_file = os.path.join(self.style_dir, f"{theme_name}.qss")
        
        if not os.path.exists(qss_file):
            print(f"[ThemeManager] Stylesheet not found: {qss_file}")
            # Try fallback to dark theme
            if theme_name != "dark":
                return self.apply_theme(app, "dark")
            return False

        try:
            with open(qss_file, "r", encoding="utf-8") as f:
                style = f.read()
            app.setStyleSheet(style)
            return True
        except Exception as e:
            print(f"[ThemeManager] Error applying theme: {e}")
            return False
