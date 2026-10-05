"""Main Application Window for FaceForge."""
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTabWidget, QSplitter,
    QStatusBar, QMenuBar, QMenu
)
from PySide6.QtCore import Qt

from faceforge.config import Settings
from faceforge.core.models_processor import ModelsProcessor

class MainWindow(QMainWindow):
    """Main application window container."""

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        
        # Initialize Core Engines
        self.models_processor = ModelsProcessor(settings)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"FaceForge v1.0.0 - Device: {self.settings.get('device', 'cpu').upper()}")
        self.resize(
            self.settings.get("window_width", 1376),
            self.settings.get("window_height", 768)
        )
        
        # Create Menubar
        self.create_menus()
        
        # Main Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Main Splitter (Left: Controls, Right: Media/Preview)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # --- Left Panel (Controls) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_swap_tab(), "🎭 Face Swap")
        self.tabs.addTab(self.create_enhance_tab(), "✨ Enhance")
        self.tabs.addTab(self.create_settings_tab(), "⚙️ Settings")
        
        left_layout.addWidget(self.tabs)
        splitter.addWidget(left_panel)
        
        # --- Right Panel (Media Preview) ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        preview_label = QLabel("Preview Area\n(Drag & Drop Media Here)")
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setStyleSheet("background-color: #0f0f0f; border: 1px dashed #3d3d3d; border-radius: 8px;")
        right_layout.addWidget(preview_label)
        
        # Playback controls placeholder
        controls_layout = QHBoxLayout()
        btn_play = QPushButton("▶ Play")
        btn_pause = QPushButton("⏸ Pause")
        btn_stop = QPushButton("⏹ Stop")
        controls_layout.addWidget(btn_play)
        controls_layout.addWidget(btn_pause)
        controls_layout.addWidget(btn_stop)
        controls_layout.addStretch()
        right_layout.addLayout(controls_layout)
        
        splitter.addWidget(right_panel)
        
        # Set Splitter Proportions (30% left, 70% right)
        splitter.setSizes([300, 700])
        
        # Status Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

    def create_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Open Media...")
        file_menu.addAction("Save Output As...")
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About FaceForge")

    def create_swap_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Face Swap Controls will go here."))
        layout.addStretch()
        return widget

    def create_enhance_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Enhancement Controls will go here."))
        layout.addStretch()
        return widget
        
    def create_settings_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Application Settings will go here."))
        layout.addStretch()
        return widget

    def closeEvent(self, event):
        """Handle application exit."""
        # Save window geometry
        self.settings.set("window_width", self.width())
        self.settings.set("window_height", self.height())
        self.settings.save()
        
        # Clear VRAM
        self.models_processor.clear_all_models()
        
        event.accept()
