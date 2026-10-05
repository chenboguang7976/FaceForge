# 🔥 FaceForge

**Open-source AI Face Swap & Enhancement Tool — Offline, GPU-Accelerated, Desktop App**

FaceForge is a powerful desktop application for AI-powered face swapping, face enhancement, face editing, and video processing. Built with a clean modular architecture, premium Qt6 interface, and ONNX Runtime for fast GPU inference.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Qt](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-green?logo=qt)
![ONNX](https://img.shields.io/badge/Inference-ONNX%20Runtime-orange)
![License](https://img.shields.io/badge/License-GPLv3-red)

---

## ✨ Features

### 🎭 Face Swap
- **Inswapper 128** — High quality face swap (InsightFace)
- **InStyleSwapper 256** — Style-preserving swap (Versions A/B/C)
- **SimSwap 512** — SimSwap architecture
- **GhostFace v1/v2/v3** — Ghost face swap network
- **CSCS 256** — Cross-Subject face swap
- **DeepFaceLive (DFM)** — Real-time face swap models
- **UniFace / HyperSwap / BlendSwap** — Additional swap models

### ✨ Face Enhancement
- **GFPGAN v1.2/1.3/1.4** — Generative face restoration
- **CodeFormer** — Code-based face restoration with fidelity control
- **GPEN-BFR** — GAN Prior face restoration (256/512/1024/2048)
- **RestoreFormer++** — Transformer-based restoration
- **VQFR v2** — Vector-quantized face restoration

### 🎨 Face Editing (Live Portrait)
- **Expression control** — Eyebrow, eye, mouth manipulation
- **Head pose** — Pitch, yaw, roll adjustment
- **Eye gaze** — Horizontal/vertical gaze direction
- **Age modification** — AI-powered age adjustment
- **Expression restoration** — Preserve original expressions

### 🖼️ Frame Enhancement
- **RealESRGAN** x2/x4/x8 — Real-world super resolution
- **BSRGAN** x2/x4 — Blind super resolution
- **UltraSharp / UltraMix** x4 — Sharp upscaling
- **SPAN / SwinIR / SiAx** x4 — Modern SR architectures
- **Real-HAT** x4 — Hybrid attention upscaling

### 🎬 Video & Media
- Video face swap with frame-by-frame processing
- Webcam real-time face swap
- Image batch processing
- Audio preservation during video processing
- Virtual camera output (pyvirtualcam)
- Frame colorization (DDColor, Deoldify)

### 🎵 Audio
- Voice extraction (UVR MDX-Net)
- Lip sync (Wav2Lip / Wav2Lip-GAN)

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **NVIDIA GPU** with CUDA support (recommended) or CPU-only mode
- **FFmpeg** in system PATH

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/FaceForge.git
cd FaceForge

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Download models (see MODELS.md for details)
# Place model files in the ./models/ directory

# Run
python run.py
```

### Models Setup
See **[MODELS.md](MODELS.md)** for complete model documentation, download links, and directory structure.

The `models/` directory is **not included** in this repository due to file sizes (~25GB total). You need to download the models separately.

---

## 📁 Project Structure

```
FaceForge/
├── run.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── MODELS.md              # Model documentation & download guide
├── faceforge/
│   ├── config.py          # Settings & configuration management
│   ├── core/              # Core processing engine
│   │   ├── models_processor.py  # ONNX model loading & inference
│   │   ├── models_data.py       # Model registry & metadata
│   │   ├── video_processor.py   # Video I/O & frame management
│   │   └── frame_worker.py      # Multi-threaded frame processing
│   ├── processors/        # AI processing modules
│   │   ├── face_detector.py     # Face detection engines
│   │   ├── face_landmark.py     # Facial landmark detection
│   │   ├── face_swapper.py      # Face swap algorithms
│   │   ├── face_enhancer.py     # Face restoration/enhancement
│   │   ├── face_editor.py       # Live Portrait face editing
│   │   ├── face_mask.py         # Face masking & segmentation
│   │   ├── frame_enhancer.py    # Frame upscaling/colorization
│   │   └── utils/               # Processing utilities
│   ├── ui/                # PySide6 Qt6 GUI
│   │   ├── main_window.py       # Main application window
│   │   ├── theme.py             # Theme management
│   │   ├── styles/              # QSS stylesheets
│   │   └── widgets/             # Custom Qt widgets
│   └── helpers/           # Utility modules
│       ├── downloader.py        # Model download utility
│       └── misc.py              # Miscellaneous helpers
└── models/                # Model files (user-provided)
```

---

## ⚙️ Configuration

Settings are stored in `settings.json` and can be configured via the GUI:

| Setting | Description | Default |
|---------|-------------|---------|
| `device` | Processing device | `cuda` |
| `max_threads` | Worker threads | `4` |
| `output_quality` | JPEG output quality | `80` |
| `keep_fps` | Preserve original FPS | `true` |
| `face_detector` | Detection model | `RetinaFace` |
| `face_enhancer` | Enhancement model | `GFPGAN 1.4` |
| `face_swapper` | Swap model | `Inswapper128` |

---

## 🤝 Contributing

Contributions are welcome! Please read the following before contributing:

1. **Backend (Python)**: Processing logic in `faceforge/processors/`
2. **Frontend (Qt)**: UI components in `faceforge/ui/`
3. **Models**: See `MODELS.md` for model integration guide

### Development Setup
```bash
pip install -r requirements.txt
python run.py --debug
```

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0** — see [LICENSE](LICENSE) for details.

### Credits & Acknowledgments
- [InsightFace](https://github.com/deepinsight/insightface) — Face analysis & Inswapper
- [GFPGAN](https://github.com/TencentARC/GFPGAN) — Face restoration
- [CodeFormer](https://github.com/sczhou/CodeFormer) — Face restoration
- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) — Image super resolution
- [LivePortrait](https://github.com/KwaiVGI/LivePortrait) — Portrait animation
- [VisoMaster](https://github.com/visomaster/visomaster) — Original unified tool
- [Rope](https://github.com/Hillobar/Rope) — Video face swap
- [FaceFusion](https://github.com/facefusion/facefusion) — Face processing framework

---

> ⚠️ **Disclaimer**: This tool is intended for research and educational purposes. Users are responsible for ensuring ethical and legal use. Do not use this tool to create misleading or harmful content.
