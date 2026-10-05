"""Model registry and metadata for all AI models.

Defines the complete catalog of models, their paths, hashes,
download URLs, and the mapping between model names and their
companion/dependency models (e.g., ArcFace embedding models).
"""

MODELS_DIR = "./models"
ASSETS_REPO = "https://github.com/visomaster/visomaster-assets/releases/download"

# ─────────────────────────────────────────────────────────────
# TensorRT model list (loaded dynamically if TRT is available)
# ─────────────────────────────────────────────────────────────
try:
    import tensorrt as trt
    TENSORRT_AVAILABLE = True

    MODELS_TRT_LIST = [
        {
            "model_name": "LivePortraitMotionExtractor",
            "local_path": f"{MODELS_DIR}/liveportrait_onnx/motion_extractor.{trt.__version__}.trt",
            "hash": "8cab6d8fe093a07ee59e14bf83b9fbc90732ce7a6c1732b88b59f4457bea6204",
        },
        {
            "model_name": "LivePortraitAppearanceFeatureExtractor",
            "local_path": f"{MODELS_DIR}/liveportrait_onnx/appearance_feature_extractor.{trt.__version__}.trt",
            "hash": "7fea0c28948a5f0d21ae0712301084a0b4a0b1fdef48983840d58d8711da90af",
        },
        {
            "model_name": "LivePortraitStitchingEye",
            "local_path": f"{MODELS_DIR}/liveportrait_onnx/stitching_eye.{trt.__version__}.trt",
            "hash": "266afbccd79f2f5ae277242b19dd9299815b24dc453b22f6fd79fbf8f3a1e593",
        },
        {
            "model_name": "LivePortraitStitchingLip",
            "local_path": f"{MODELS_DIR}/liveportrait_onnx/stitching_lip.{trt.__version__}.trt",
            "hash": "2ac2e57eb2edd5aec70dc45023113e2ccc0495a16579c6c5d56fa30b74edc4f5",
        },
        {
            "model_name": "LivePortraitStitching",
            "local_path": f"{MODELS_DIR}/liveportrait_onnx/stitching.{trt.__version__}.trt",
            "hash": "8448de922a824b7b11eb7f470805ec22cf4ee541f7d66afeb2965094f96fd3ab",
        },
        {
            "model_name": "LivePortraitWarpingSpadeFix",
            "local_path": f"{MODELS_DIR}/liveportrait_onnx/warping_spade-fix_vm.{trt.__version__}.trt",
            "hash": "24acdb6379b28fbefefb6339b3605693e00f1703c21ea5b8fec0215e521f6912",
        },
    ]
except ModuleNotFoundError:
    TENSORRT_AVAILABLE = False
    MODELS_TRT_LIST = []


# ─────────────────────────────────────────────────────────────
# ArcFace model mapping (which swap model needs which ArcFace)
# ─────────────────────────────────────────────────────────────
ARCFACE_MAPPING = {
    "Inswapper128": "Inswapper128ArcFace",
    "InStyleSwapper256 Version A": "Inswapper128ArcFace",
    "InStyleSwapper256 Version B": "Inswapper128ArcFace",
    "InStyleSwapper256 Version C": "Inswapper128ArcFace",
    "DeepFaceLive (DFM)": "Inswapper128ArcFace",
    "SimSwap512": "SimSwapArcFace",
    "GhostFace-v1": "GhostArcFace",
    "GhostFace-v2": "GhostArcFace",
    "GhostFace-v3": "GhostArcFace",
    "CSCS": "CSCSArcFace",
}

# ─────────────────────────────────────────────────────────────
# Detection model mapping
# ─────────────────────────────────────────────────────────────
DETECTION_MODEL_MAPPING = {
    "RetinaFace": "RetinaFace",
    "SCRFD": "SCRFD2.5g",
    "Yolov8": "YoloFace8n",
    "Yunet": "YunetN",
}

# ─────────────────────────────────────────────────────────────
# Landmark model mapping
# ─────────────────────────────────────────────────────────────
LANDMARK_MODEL_MAPPING = {
    "5": "FaceLandmark5",
    "68": "FaceLandmark68",
    "3d68": "FaceLandmark3d68",
    "98": "FaceLandmark98",
    "106": "FaceLandmark106",
    "203": "FaceLandmark203",
    "478": "FaceLandmark478",
}


# ─────────────────────────────────────────────────────────────
# Complete model catalog
# ─────────────────────────────────────────────────────────────
MODELS_LIST = [
    # === Face Swap Models ===
    {
        "model_name": "Inswapper128",
        "local_path": f"{MODELS_DIR}/inswapper_128.fp16.onnx",
        "hash": "6d51a9278a1f650cffefc18ba53f38bf2769bf4bbff89267822cf72945f8a38b",
        "url": f"{ASSETS_REPO}/v0.1.0/inswapper_128.fp16.onnx",
    },
    {
        "model_name": "InStyleSwapper256 Version A",
        "local_path": f"{MODELS_DIR}/InStyleSwapper256_Version_A.fp16.onnx",
        "hash": "0e0ef024b935abca69fd367a385200ed46b83a3cc618287ffe89440e2cc646da",
        "url": f"{ASSETS_REPO}/v0.1.0/InStyleSwapper256_Version_A.fp16.onnx",
    },
    {
        "model_name": "InStyleSwapper256 Version B",
        "local_path": f"{MODELS_DIR}/InStyleSwapper256_Version_B.fp16.onnx",
        "hash": "0870b6c75eaea239bdd72b6c6d0910cb285310736e356c17a2cd67a961738116",
        "url": f"{ASSETS_REPO}/v0.1.0/InStyleSwapper256_Version_B.fp16.onnx",
    },
    {
        "model_name": "InStyleSwapper256 Version C",
        "local_path": f"{MODELS_DIR}/InStyleSwapper256_Version_C.fp16.onnx",
        "hash": "6eaefc04cfb1461222ab72a814ad5b5673ab1af4267f7eb9054e308797567cde",
        "url": f"{ASSETS_REPO}/v0.1.0/InStyleSwapper256_Version_C.fp16.onnx",
    },
    {
        "model_name": "SimSwap512",
        "local_path": f"{MODELS_DIR}/simswap_512_unofficial.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/simswap_512_unofficial.onnx",
    },
    {
        "model_name": "GhostFacev1",
        "local_path": f"{MODELS_DIR}/ghost_1_256.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/ghost_1_256.onnx",
    },
    {
        "model_name": "GhostFacev2",
        "local_path": f"{MODELS_DIR}/ghost_256_unet_2.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/ghost_256_unet_2.onnx",
    },
    {
        "model_name": "GhostFacev3",
        "local_path": f"{MODELS_DIR}/ghost_256_unet_3.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/ghost_256_unet_3.onnx",
    },
    {
        "model_name": "CSCS",
        "local_path": f"{MODELS_DIR}/cscs_256.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/cscs_256.onnx",
    },
    {
        "model_name": "UniFace",
        "local_path": f"{MODELS_DIR}/uniface_256.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/uniface_256.onnx",
    },
    {
        "model_name": "BlendSwap",
        "local_path": f"{MODELS_DIR}/blendswap_256.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/blendswap_256.onnx",
    },
    {
        "model_name": "HyperSwapA",
        "local_path": f"{MODELS_DIR}/hyperswap_1a_256.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/hyperswap_1a_256.onnx",
    },
    {
        "model_name": "HiFiFace",
        "local_path": f"{MODELS_DIR}/hififace_unofficial_256.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/hififace_unofficial_256.onnx",
    },

    # === ArcFace / Embedding Models ===
    {
        "model_name": "Inswapper128ArcFace",
        "local_path": f"{MODELS_DIR}/w600k_r50_fp16.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/w600k_r50_fp16.onnx",
    },
    {
        "model_name": "SimSwapArcFace",
        "local_path": f"{MODELS_DIR}/simswap_arcface_model.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/simswap_arcface_model.onnx",
    },
    {
        "model_name": "GhostArcFace",
        "local_path": f"{MODELS_DIR}/ghost_arcface_backbone.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/ghost_arcface_backbone.onnx",
    },
    {
        "model_name": "CSCSArcFace",
        "local_path": f"{MODELS_DIR}/cscs_arcface_model.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/cscs_arcface_model.onnx",
    },
    {
        "model_name": "CSCSIDArcFace",
        "local_path": f"{MODELS_DIR}/cscs_id_adapter.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/cscs_id_adapter.onnx",
    },

    # === Face Detection ===
    {
        "model_name": "RetinaFace",
        "local_path": f"{MODELS_DIR}/retinaface_10g.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/retinaface_10g.onnx",
    },
    {
        "model_name": "SCRFD2.5g",
        "local_path": f"{MODELS_DIR}/scrfd_2.5g.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/scrfd_2.5g.onnx",
    },
    {
        "model_name": "YoloFace8n",
        "local_path": f"{MODELS_DIR}/yoloface_8n.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/yoloface_8n.onnx",
    },
    {
        "model_name": "YunetN",
        "local_path": f"{MODELS_DIR}/yunet_n_640_640.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/yunet_n_640_640.onnx",
    },

    # === Face Landmarks ===
    {
        "model_name": "FaceLandmark3d68",
        "local_path": f"{MODELS_DIR}/1k3d68.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/1k3d68.onnx",
    },
    {
        "model_name": "FaceLandmark106",
        "local_path": f"{MODELS_DIR}/2d106det.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/2d106det.onnx",
    },
    {
        "model_name": "FaceLandmark68",
        "local_path": f"{MODELS_DIR}/2dfan4.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/2dfan4.onnx",
    },
    {
        "model_name": "FaceLandmark5",
        "local_path": f"{MODELS_DIR}/fan_68_5.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/fan_68_5.onnx",
    },
    {
        "model_name": "FaceLandmark203",
        "local_path": f"{MODELS_DIR}/landmark.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/landmark.onnx",
    },
    {
        "model_name": "FaceLandmark478",
        "local_path": f"{MODELS_DIR}/face_landmarks_detector_Nx3x256x256.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/face_landmarks_detector_Nx3x256x256.onnx",
    },

    # === Face Enhancement ===
    {
        "model_name": "GFPGAN1.4",
        "local_path": f"{MODELS_DIR}/gfpgan_1.4.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/gfpgan_1.4.onnx",
    },
    {
        "model_name": "GFPGAN1.3",
        "local_path": f"{MODELS_DIR}/gfpgan_1.3.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/gfpgan_1.3.onnx",
    },
    {
        "model_name": "GFPGAN1.2",
        "local_path": f"{MODELS_DIR}/gfpgan_1.2.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/gfpgan_1.2.onnx",
    },
    {
        "model_name": "CodeFormer",
        "local_path": f"{MODELS_DIR}/codeformer.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/codeformer.onnx",
    },
    {
        "model_name": "GPENBFR256",
        "local_path": f"{MODELS_DIR}/GPEN-BFR-256.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/GPEN-BFR-256.onnx",
    },
    {
        "model_name": "GPENBFR512",
        "local_path": f"{MODELS_DIR}/GPEN-BFR-512.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/GPEN-BFR-512.onnx",
    },
    {
        "model_name": "GPENBFR1024",
        "local_path": f"{MODELS_DIR}/GPEN-BFR-1024.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/GPEN-BFR-1024.onnx",
    },
    {
        "model_name": "GPENBFR2048",
        "local_path": f"{MODELS_DIR}/GPEN-BFR-2048.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/GPEN-BFR-2048.onnx",
    },
    {
        "model_name": "RestoreFormerPlusPlus",
        "local_path": f"{MODELS_DIR}/RestoreFormerPlusPlus.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/RestoreFormerPlusPlus.onnx",
    },
    {
        "model_name": "VQFRv2",
        "local_path": f"{MODELS_DIR}/VQFRv2.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/VQFRv2.onnx",
    },

    # === Face Masking ===
    {
        "model_name": "FaceOccluder",
        "local_path": f"{MODELS_DIR}/face_occluder.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/face_occluder.onnx",
    },
    {
        "model_name": "FaceParser",
        "local_path": f"{MODELS_DIR}/face_parser.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/face_parser.onnx",
    },
    {
        "model_name": "FaceParserResNet34",
        "local_path": f"{MODELS_DIR}/bisenet_resnet_34.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/bisenet_resnet_34.onnx",
    },
    {
        "model_name": "DFLXSeg",
        "local_path": f"{MODELS_DIR}/dfl_xseg.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/dfl_xseg.onnx",
    },

    # === Frame Enhancement ===
    {
        "model_name": "RealEsrganx2Plus",
        "local_path": f"{MODELS_DIR}/RealESRGAN_x2plus.fp16.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/RealESRGAN_x2plus.fp16.onnx",
    },
    {
        "model_name": "RealEsrganx4Plus",
        "local_path": f"{MODELS_DIR}/RealESRGAN_x4plus.fp16.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/RealESRGAN_x4plus.fp16.onnx",
    },
    {
        "model_name": "BSRGANx2",
        "local_path": f"{MODELS_DIR}/BSRGANx2.fp16.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/BSRGANx2.fp16.onnx",
    },
    {
        "model_name": "BSRGANx4",
        "local_path": f"{MODELS_DIR}/BSRGANx4.fp16.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/BSRGANx4.fp16.onnx",
    },
    {
        "model_name": "UltraSharpx4",
        "local_path": f"{MODELS_DIR}/4x-UltraSharp.fp16.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/4x-UltraSharp.fp16.onnx",
    },
    {
        "model_name": "UltraMixx4",
        "local_path": f"{MODELS_DIR}/4x-UltraMix_Smooth.fp16.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/4x-UltraMix_Smooth.fp16.onnx",
    },
    {
        "model_name": "SPANx4",
        "local_path": f"{MODELS_DIR}/span_kendata_x4.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/span_kendata_x4.onnx",
    },

    # === Colorization ===
    {
        "model_name": "DDColor",
        "local_path": f"{MODELS_DIR}/ddcolor.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/ddcolor.onnx",
    },
    {
        "model_name": "DeoldifyArt",
        "local_path": f"{MODELS_DIR}/deoldify_artistic.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/deoldify_artistic.onnx",
    },
    {
        "model_name": "DeoldifyStable",
        "local_path": f"{MODELS_DIR}/deoldify_stable.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/deoldify_stable.onnx",
    },

    # === Age / Gender ===
    {
        "model_name": "GenderAge",
        "local_path": f"{MODELS_DIR}/gender_age.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/gender_age.onnx",
    },
    {
        "model_name": "FairFace",
        "local_path": f"{MODELS_DIR}/fairface.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/fairface.onnx",
    },

    # === Live Portrait ===
    {
        "model_name": "LivePortraitMotionExtractor",
        "local_path": f"{MODELS_DIR}/liveportrait_onnx/motion_extractor.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/motion_extractor.onnx",
    },
    {
        "model_name": "LivePortraitAppearanceFeatureExtractor",
        "local_path": f"{MODELS_DIR}/liveportrait_onnx/appearance_feature_extractor.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/appearance_feature_extractor.onnx",
    },
    {
        "model_name": "LivePortraitWarpingSpadeFix",
        "local_path": f"{MODELS_DIR}/liveportrait_onnx/warping_spade-fix_vm.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/warping_spade-fix_vm.onnx",
    },
    {
        "model_name": "LivePortraitStitching",
        "local_path": f"{MODELS_DIR}/liveportrait_onnx/stitching.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/stitching.onnx",
    },
    {
        "model_name": "LivePortraitStitchingEye",
        "local_path": f"{MODELS_DIR}/liveportrait_onnx/stitching_eye.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/stitching_eye.onnx",
    },
    {
        "model_name": "LivePortraitStitchingLip",
        "local_path": f"{MODELS_DIR}/liveportrait_onnx/stitching_lip.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/stitching_lip.onnx",
    },

    # === Lip Sync ===
    {
        "model_name": "Wav2Lip",
        "local_path": f"{MODELS_DIR}/wav2lip_96.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/wav2lip_96.onnx",
    },
    {
        "model_name": "Wav2LipGAN",
        "local_path": f"{MODELS_DIR}/wav2lip_gan_96.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/wav2lip_gan_96.onnx",
    },

    # === Voice Extraction ===
    {
        "model_name": "VoiceExtractor",
        "local_path": f"{MODELS_DIR}/voice_extractor.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/voice_extractor.onnx",
    },

    # === Age Modification ===
    {
        "model_name": "StyleGANExAge",
        "local_path": f"{MODELS_DIR}/styleganex_age.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/styleganex_age.onnx",
    },

    # === NSFW Detection ===
    {
        "model_name": "NSFWDetector",
        "local_path": f"{MODELS_DIR}/yolo_11m_nsfw.onnx",
        "hash": "",
        "url": f"{ASSETS_REPO}/v0.1.0/yolo_11m_nsfw.onnx",
    },
]


def get_model_data(model_name: str) -> dict | None:
    """Look up a model entry by name."""
    for entry in MODELS_LIST:
        if entry["model_name"] == model_name:
            return entry
    return None


def get_available_models(category: str = None) -> list[str]:
    """Get list of available model names, optionally filtered by category prefix."""
    names = [m["model_name"] for m in MODELS_LIST]
    if category:
        names = [n for n in names if n.startswith(category)]
    return names
