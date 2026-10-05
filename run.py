#!/usr/bin/env python3
"""FaceForge — AI Face Swap & Enhancement Tool

Entry point for the application.
"""
import sys
import os

# Ensure the project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Launch FaceForge application."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon

    from faceforge.ui.main_window import MainWindow
    from faceforge.config import Settings

    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("FaceForge")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("FaceForge")

    # Load settings
    settings = Settings()

    # Apply theme
    from faceforge.ui.theme import ThemeManager
    theme_manager = ThemeManager()
    theme_manager.apply_theme(app, settings.get("theme", "dark"))

    # Create and show main window
    window = MainWindow(settings)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
