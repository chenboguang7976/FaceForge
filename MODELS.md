# 📦 FaceForge — Model Documentation

This document describes all AI models used by FaceForge. Models are **not included** in the repository due to their large file sizes (~25GB total). You must download them separately.

## 📁 Directory Structure

```
models/
├── inswapper_128.fp16.onnx              # Face Swap (required)
├── InStyleSwapper256_Version_A.fp16.onnx # Face Swap variant
├── InStyleSwapper256_Version_B.fp16.onnx
├── InStyleSwapper256_Version_C.fp16.onnx
├── simswap_512_unofficial.onnx          # SimSwap
├── simswap_arcface_model.onnx
├── ghost_1_256.onnx                     # GhostFace v1
├── ghost_256_unet_2.onnx               # GhostFace v2
├── ghost_256_unet_3.onnx               # GhostFace v3
├── ghost_arcface_backbone.onnx
├── cscs_256.onnx                        # CSCS swap
├── cscs_arcface_model.onnx
├── cscs_id_adapter.onnx
├── uniface_256.onnx                     # UniFace swap
├── blendswap_256.onnx                   # BlendSwap
├── hyperswap_1a_256.onnx                # HyperSwap
├── hyperswap_1b_256.onnx
├── hyperswap_1c_256.onnx
├── hififace_unofficial_256.onnx         # HiFiFace
├── arcface_w600k_r50.onnx              # ArcFace recognition
├── w600k_r50.onnx
├── w600k_r50_fp16.onnx
│
├── # Face Detection
├── retinaface_10g.onnx                  # RetinaFace (recommended)
├── scrfd_2.5g.onnx                      # SCRFD lightweight
├── yoloface_8n.onnx                     # YOLOv8 face
├── yunet_2023mar.onnx                   # YuNet
│
├── # Face Landmarks
├── 1k3d68.onnx                          # 3D 68-point landmarks
├── 2d106det.onnx                        # 106-point landmarks
├── 2dfan4.onnx                          # 68-point FAN
├── face_landmarker_68_5.onnx            # MediaPipe landmarks
├── face_landmarks_detector_Nx3x256x256.onnx
├── landmark.onnx                        # 203-point landmarks
├── face_blendshapes_Nx146x2.onnx        # 478-point blendshapes
│
├── # Face Enhancement
├── gfpgan_1.4.onnx                      # GFPGAN v1.4 (recommended)
├── gfpgan_1.3.onnx
├── gfpgan_1.2.onnx
├── codeformer.onnx                      # CodeFormer
├── GPEN-BFR-256.onnx                    # GPEN 256px
├── GPEN-BFR-512.onnx                    # GPEN 512px
├── GPEN-BFR-1024.onnx                   # GPEN 1024px
├── GPEN-BFR-2048.onnx                   # GPEN 2048px
├── RestoreFormerPlusPlus.onnx           # RestoreFormer++
├── VQFRv2.onnx                          # VQFR v2
│
├── # Face Masking & Parsing
├── face_occluder.onnx                   # Occlusion mask
├── face_parser.onnx                     # Face parsing (BiSeNet)
├── bisenet_resnet_34.onnx               # BiSeNet ResNet34
├── faceparser_fp16.onnx
├── xseg_1.onnx                          # XSeg masks
├── xseg_2.onnx
├── xseg_3.onnx
├── dfl_xseg.onnx                        # DeepFaceLab XSeg
│
├── # Face Editing
├── gender_age.onnx                      # Gender/age detection
├── fairface.onnx                        # Fair face attributes
├── styleganex_age.onnx                  # Age modification
│
├── # Frame Enhancement (Super Resolution)
├── RealESRGAN_x2plus.fp16.onnx          # RealESRGAN 2x
├── RealESRGAN_x4plus.fp16.onnx          # RealESRGAN 4x
├── real_esrgan_x4.onnx
├── real_esrgan_x8.onnx                  # RealESRGAN 8x
├── BSRGANx2.fp16.onnx                   # BSRGAN 2x
├── BSRGANx4.fp16.onnx                   # BSRGAN 4x
├── 4x-UltraSharp.fp16.onnx             # UltraSharp 4x
├── 4x-UltraMix_Smooth.fp16.onnx        # UltraMix 4x
├── span_kendata_x4.onnx                 # SPAN 4x (lightweight)
├── nomos8k_sc_x4.onnx                   # Nomos 4x
├── lsdir_x4.onnx                        # LSDIR 4x
├── swin2_sr_x4.onnx                     # SwinIR 4x
├── siax_x4.onnx                         # SiAx 4x
├── real_hatgan_x4.onnx                  # Real-HAT 4x
├── remacri_x4.onnx                      # Remacri 4x
├── clear_reality_x4.onnx               # Clear Reality 4x
│
├── # Colorization
├── ddcolor.onnx                         # DDColor
├── ddcolor_artistic.onnx
├── deoldify.onnx                        # Deoldify
├── deoldify_artistic.onnx
├── deoldify_stable.onnx
│
├── # Voice / Audio
├── uvr_mdxnet.onnx                      # Voice extraction
├── voice_extractor.onnx
├── kim_vocal_1.onnx                     # Kim vocal separation
├── kim_vocal_2.onnx
├── wav2lip_96.onnx                      # Wav2Lip
├── wav2lip_gan_96.onnx                  # Wav2Lip GAN
│
├── # Live Portrait
├── liveportrait_onnx/
│   ├── appearance_feature_extractor.onnx
│   ├── motion_extractor.onnx
│   ├── warping_spade-fix.onnx
│   ├── warping_spade-fix_vm.onnx
│   ├── stitching.onnx
│   ├── stitching_eye.onnx
│   ├── stitching_lip.onnx
│   ├── 2d106det.onnx
│   ├── retinaface_det_static.onnx
│   ├── grid_sample_3d_plugin.dll        # Windows plugin
│   ├── libgrid_sample_3d_plugin.so      # Linux plugin
│   └── lip_array.pkl
│
├── # NSFW Detection
├── yolo_11m_nsfw.onnx
│
├── # DFM Models (DeepFaceLive format)
├── dfm_models/
│   └── *.dfm                            # Place .dfm models here
│
├── # Support models
├── res50.onnx                           # ResNet50 backbone
├── ViT-B-16.pt                          # CLIP ViT-B/16
├── peppa_wutz.onnx                      # Fun face models
└── peppapig_teacher_Nx3x256x256.onnx
```

---

## 🏷️ Model Categories & Details

### 1. Face Swap Models

| Model | File | Size | Resolution | Description |
|-------|------|------|------------|-------------|
| **Inswapper 128** | `inswapper_128.fp16.onnx` | 265 MB | 128×128 | InsightFace official, best overall quality |
| **InStyleSwapper A/B/C** | `InStyleSwapper256_Version_*.fp16.onnx` | 264 MB each | 256×256 | Style-preserving variants |
| **SimSwap 512** | `simswap_512_unofficial.onnx` | 228 MB | 512×512 | High-resolution swap |
| **GhostFace v1/v2/v3** | `ghost_*_256.onnx` | 491-816 MB | 256×256 | Progressive quality levels |
| **CSCS** | `cscs_256.onnx` | 704 MB | 256×256 | Cross-subject consistency |
| **UniFace** | `uniface_256.onnx` | 388 MB | 256×256 | Unified face swap |
| **BlendSwap** | `blendswap_256.onnx` | 1585 MB | 256×256 | Blend-based swap |
| **HyperSwap** | `hyperswap_1*_256.onnx` | 384 MB each | 256×256 | Hyper-network swap |

**Required companion models:**
- `arcface_w600k_r50.onnx` — ArcFace embedding for Inswapper/ISS
- `simswap_arcface_model.onnx` — ArcFace for SimSwap
- `ghost_arcface_backbone.onnx` — ArcFace for GhostFace
- `cscs_arcface_model.onnx` + `cscs_id_adapter.onnx` — For CSCS

### 2. Face Detection Models

| Model | File | Size | Speed | Accuracy |
|-------|------|------|-------|----------|
| **RetinaFace** | `retinaface_10g.onnx` | 16 MB | Medium | ★★★★★ |
| **SCRFD** | `scrfd_2.5g.onnx` | 3 MB | Fast | ★★★★ |
| **YOLOv8 Face** | `yoloface_8n.onnx` | 12 MB | Fastest | ★★★★ |
| **YuNet** | `yunet_2023mar.onnx` | 0.2 MB | Fastest | ★★★ |

### 3. Face Enhancement Models

| Model | File | Size | Resolution | Quality |
|-------|------|------|------------|---------|
| **GFPGAN 1.4** | `gfpgan_1.4.onnx` | 325 MB | 512×512 | ★★★★★ |
| **CodeFormer** | `codeformer.onnx` | 359 MB | 512×512 | ★★★★★ |
| **GPEN-BFR 512** | `GPEN-BFR-512.onnx` | 271 MB | 512×512 | ★★★★ |
| **RestoreFormer++** | `RestoreFormerPlusPlus.onnx` | 282 MB | 512×512 | ★★★★ |
| **VQFR v2** | `VQFRv2.onnx` | 343 MB | 512×512 | ★★★★ |

### 4. Frame Enhancement Models

| Model | File | Scale | Size |
|-------|------|-------|------|
| **RealESRGAN x4** | `RealESRGAN_x4plus.fp16.onnx` | 4× | 32 MB |
| **RealESRGAN x2** | `RealESRGAN_x2plus.fp16.onnx` | 2× | 32 MB |
| **BSRGAN x4** | `BSRGANx4.fp16.onnx` | 4× | 32 MB |
| **UltraSharp x4** | `4x-UltraSharp.fp16.onnx` | 4× | 32 MB |
| **SPAN x4** | `span_kendata_x4.onnx` | 4× | 1.6 MB |

### 5. Live Portrait Models

All files should be in `models/liveportrait_onnx/`:

| Model | File | Size | Purpose |
|-------|------|------|---------|
| Motion Extractor | `motion_extractor.onnx` | 107 MB | Head pose & expression |
| Feature Extractor | `appearance_feature_extractor.onnx` | 3.2 MB | Appearance features |
| Warping | `warping_spade-fix_vm.onnx` | 402 MB | Image warping |
| Stitching | `stitching.onnx` | 0.2 MB | Face stitching |
| Eye Retarget | `stitching_eye.onnx` | 0.6 MB | Eye control |
| Lip Retarget | `stitching_lip.onnx` | 0.1 MB | Lip control |

---

## ⬇️ Download Sources

Models can be downloaded from the following sources:

1. **VisoMaster Assets**: https://github.com/visomaster/visomaster-assets/releases
2. **InsightFace**: https://github.com/deepinsight/insightface
3. **HuggingFace**: Search for model names on https://huggingface.co

### Minimum Required Models
To get started with basic face swap, you need at minimum:
1. `inswapper_128.fp16.onnx` — Face swap engine
2. `arcface_w600k_r50.onnx` or `w600k_r50_fp16.onnx` — Face embedding
3. `retinaface_10g.onnx` — Face detection
4. `2d106det.onnx` or `1k3d68.onnx` — Face landmarks
5. `gfpgan_1.4.onnx` — Face enhancement (optional but recommended)

---

## 🔧 For Developers / AI Assistants

### How Models Are Loaded

Models are loaded on-demand via `faceforge/core/models_processor.py`:

```python
# Model loading pattern
session = onnxruntime.InferenceSession(
    model_path,
    providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
)

# Inference uses IO binding for GPU-direct memory access
io_binding = session.io_binding()
io_binding.bind_input(name='input', device_type='cuda', ...)
io_binding.bind_output(name='output', device_type='cuda', ...)
session.run_with_iobinding(io_binding)
```

### Model Registry

All models are registered in `faceforge/core/models_data.py`. Each model entry contains:
- `model_name`: Internal identifier
- `local_path`: Path relative to `models/` directory  
- `hash`: SHA256 hash for integrity verification
- `url`: Optional download URL

### Adding a New Model

1. Add model entry to `models_data.py`
2. Create processor method in the appropriate processor class
3. Add UI controls in `faceforge/ui/widgets/parameter_panel.py`
4. Update this documentation

### Input/Output Formats

Most models expect:
- **Input**: `torch.Tensor` on GPU, shape `(1, 3, H, W)`, float32, range [0, 1] or [-1, 1]
- **Output**: Same format as input

Common resolutions:
- Face swap: 128×128, 256×256, 512×512
- Face enhancement: 256×256, 512×512, 1024×1024
- Frame enhancement: Dynamic (tile-based processing)

---

## 📋 Model File Hashes (SHA256)

For integrity verification, compare downloaded file hashes:

| File | SHA256 |
|------|--------|
| `inswapper_128.fp16.onnx` | `6d51a9278a1f650cffefc18ba53f38bf2769bf4bbff89267822cf72945f8a38b` |
| `InStyleSwapper256_Version_A.fp16.onnx` | `0e0ef024b935abca69fd367a385200ed46b83a3cc618287ffe89440e2cc646da` |
| `InStyleSwapper256_Version_B.fp16.onnx` | `0870b6c75eaea239bdd72b6c6d0910cb285310736e356c17a2cd67a961738116` |
| `InStyleSwapper256_Version_C.fp16.onnx` | `6eaefc04cfb1461222ab72a814ad5b5673ab1af4267f7eb9054e308797567cde` |

> Use `python -c "import hashlib; print(hashlib.sha256(open('model.onnx','rb').read()).hexdigest())"` to verify.
