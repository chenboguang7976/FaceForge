# FaceForge models

FaceForge downloads the models it needs automatically, the first time a
feature uses them (or from **Performance → Models…**). Downloads resume if
interrupted and are checked against the exact file size.

All models come from the public [FaceFusion assets](https://github.com/facefusion/facefusion-assets/releases).
Each model keeps the license of its original authors. Check those licenses
before any commercial use.

| Key | File | Size | Used for |
|---|---|---:|---|
| `scrfd` | `scrfd_2.5g.onnx` | 3 MB | Face detection, fast (Lite default) |
| `retinaface` | `retinaface_10g.onnx` | 16 MB | Face detection, accurate (Pro default) |
| `yoloface` | `yoloface_8n.onnx` | 12 MB | Face detection, alternative |
| `2dfan4` | `2dfan4.onnx` | 93 MB | 68-point landmarks: precise alignment, steadier on turned faces (Balanced and up) |
| `arcface_w600k_r50` | `arcface_w600k_r50.onnx` | 166 MB | Face identity (needed for every swap) |
| `inswapper_128` | `inswapper_128.onnx` | 530 MB | Swap, 128 px, FP32 (best on GTX 10xx and CPU) |
| `inswapper_128_fp16` | `inswapper_128_fp16.onnx` | 265 MB | Swap, 128 px, FP16 (RTX / GTX 16xx and newer) |
| `hyperswap_1a_256` | `hyperswap_1a_256.onnx` | 384 MB | Swap, 256 px, newest and most natural (Pro default) |
| `hyperswap_1b_256` | `hyperswap_1b_256.onnx` | 384 MB | HyperSwap variant B |
| `hyperswap_1c_256` | `hyperswap_1c_256.onnx` | 384 MB | HyperSwap variant C |
| `gfpgan_1.4` | `gfpgan_1.4.onnx` | 325 MB | Face restoration |
| `codeformer` | `codeformer.onnx` | 359 MB | Face restoration with a fidelity control |
| `gpen_bfr_256` | `gpen_bfr_256.onnx` | 72 MB | Light face restoration (Lite) |
| `gpen_bfr_512` | `gpen_bfr_512.onnx` | 271 MB | Face restoration |
| `restoreformer_plus_plus` | `restoreformer_plus_plus.onnx` | 281 MB | Face restoration |
| `xseg_1` | `xseg_1.onnx` | 67 MB | Occlusion mask (hands, hair, glasses in front of the face) |
| `bisenet_resnet_34` | `bisenet_resnet_34.onnx` | 89 MB | Face parsing mask (skin, eyes, brows, nose, lips) |

## What each preset downloads

| Preset | Models | Total |
|---|---|---:|
| Fast | SCRFD, ArcFace, InSwapper | ≈ 0.7 GB |
| Balanced | RetinaFace, 2DFAN4, ArcFace, InSwapper, GPEN-256 | ≈ 0.9 GB |
| Quality | RetinaFace, 2DFAN4, ArcFace, HyperSwap 1A, GFPGAN, XSeg | ≈ 1.05 GB |
| Maximum | Quality + BiSeNet | ≈ 1.15 GB |

## Location

- From source: `./models` in the repository.
- Windows / Linux builds: `models` next to the executable (portable), or
  `%LOCALAPPDATA%\FaceForge\models` / `~/.local/share/FaceForge/models` if
  that folder is read-only.
- macOS: `~/Library/Application Support/FaceForge/models`.

You can point to another folder by setting `models_dir` in `settings.json`
or the `FACEFORGE_HOME` environment variable.

## Why the old model list was replaced

FaceForge 1.x listed about 70 models from an archive whose download links
were mostly unverified, plus older architectures (SimSwap, GhostFace, DFM).
FaceForge 2 ships only models that are wired into the pipeline, tested
end to end, and downloadable from a stable source. The registry lives in
`faceforge/core/models_data.py`. Adding a model there makes it appear in
the model manager.
