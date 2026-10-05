"""Model registry.

Every entry here is wired into the processing pipeline and points at a
verified download (FaceFusion's public model assets). Sizes are exact byte
counts and double as a cheap integrity check after downloading.
"""
from __future__ import annotations

from dataclasses import dataclass

FACEFUSION_ASSETS = "https://github.com/facefusion/facefusion-assets/releases/download"


@dataclass(frozen=True)
class ModelInfo:
    key: str
    file: str
    url: str
    size: int            # bytes
    category: str        # detector | recognizer | swapper | enhancer | mask
    title: str           # display name (not translated; model names are proper nouns)
    low_end_ok: bool = True

    @property
    def size_mb(self) -> int:
        return round(self.size / 2**20)


def _ff(release: str, file: str) -> str:
    return f"{FACEFUSION_ASSETS}/{release}/{file}"


_MODELS = [
    # --- Face detectors -------------------------------------------------------
    ModelInfo("scrfd", "scrfd_2.5g.onnx", _ff("models-3.0.0", "scrfd_2.5g.onnx"),
              3295067, "detector", "SCRFD 2.5G (fast)"),
    ModelInfo("retinaface", "retinaface_10g.onnx", _ff("models-3.0.0", "retinaface_10g.onnx"),
              16926877, "detector", "RetinaFace 10G (accurate)"),
    ModelInfo("yoloface", "yoloface_8n.onnx", _ff("models-3.0.0", "yoloface_8n.onnx"),
              12659761, "detector", "YOLOFace 8n"),
    # --- Face recognition (identity embedding) --------------------------------
    ModelInfo("arcface_w600k_r50", "arcface_w600k_r50.onnx",
              _ff("models-3.0.0", "arcface_w600k_r50.onnx"),
              174388474, "recognizer", "ArcFace W600K R50"),
    # --- Face swappers --------------------------------------------------------
    ModelInfo("inswapper_128", "inswapper_128.onnx", _ff("models-3.0.0", "inswapper_128.onnx"),
              555303150, "swapper", "InSwapper 128 (FP32)"),
    ModelInfo("inswapper_128_fp16", "inswapper_128_fp16.onnx",
              _ff("models-3.0.0", "inswapper_128_fp16.onnx"),
              277680829, "swapper", "InSwapper 128 (FP16)"),
    ModelInfo("hyperswap_1a_256", "hyperswap_1a_256.onnx", _ff("models-3.3.0", "hyperswap_1a_256.onnx"),
              402742682, "swapper", "HyperSwap 1A 256"),
    ModelInfo("hyperswap_1b_256", "hyperswap_1b_256.onnx", _ff("models-3.3.0", "hyperswap_1b_256.onnx"),
              402742682, "swapper", "HyperSwap 1B 256"),
    ModelInfo("hyperswap_1c_256", "hyperswap_1c_256.onnx", _ff("models-3.3.0", "hyperswap_1c_256.onnx"),
              402742682, "swapper", "HyperSwap 1C 256"),
    # --- Face enhancers -------------------------------------------------------
    ModelInfo("gfpgan_1.4", "gfpgan_1.4.onnx", _ff("models-3.0.0", "gfpgan_1.4.onnx"),
              340299087, "enhancer", "GFPGAN 1.4"),
    ModelInfo("codeformer", "codeformer.onnx", _ff("models-3.0.0", "codeformer.onnx"),
              376951650, "enhancer", "CodeFormer"),
    ModelInfo("gpen_bfr_256", "gpen_bfr_256.onnx", _ff("models-3.0.0", "gpen_bfr_256.onnx"),
              75792988, "enhancer", "GPEN-BFR 256 (light)"),
    ModelInfo("gpen_bfr_512", "gpen_bfr_512.onnx", _ff("models-3.0.0", "gpen_bfr_512.onnx"),
              284340240, "enhancer", "GPEN-BFR 512"),
    ModelInfo("restoreformer_plus_plus", "restoreformer_plus_plus.onnx",
              _ff("models-3.0.0", "restoreformer_plus_plus.onnx"),
              294264232, "enhancer", "RestoreFormer++"),
    # --- Masks ----------------------------------------------------------------
    ModelInfo("xseg_1", "xseg_1.onnx", _ff("models-3.1.0", "xseg_1.onnx"),
              70324286, "mask", "XSeg (occlusion)"),
    ModelInfo("bisenet_resnet_34", "bisenet_resnet_34.onnx",
              _ff("models-3.0.0", "bisenet_resnet_34.onnx"),
              93632546, "mask", "BiSeNet ResNet34 (face parsing)"),
]

MODELS: dict[str, ModelInfo] = {m.key: m for m in _MODELS}


def get_model(key: str) -> ModelInfo:
    return MODELS[key]


def models_in(category: str) -> list[ModelInfo]:
    return [m for m in _MODELS if m.category == category]
