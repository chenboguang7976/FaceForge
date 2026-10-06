"""End-to-end frame pipeline: detect → select → swap → mask → paste → enhance."""
from __future__ import annotations

from dataclasses import dataclass, field, replace

import cv2
import numpy as np

from faceforge.core.face import Face
from faceforge.core.models_processor import ModelsProcessor
from faceforge.processors.face_detector import FaceDetector
from faceforge.processors.face_enhancer import ENHANCERS, FaceEnhancer
from faceforge.processors.face_landmarker import LANDMARKER, FaceLandmarker
from faceforge.processors.face_mask import OCCLUSION_MODEL, REGION_MODEL, FaceMasker
from faceforge.processors.face_recognizer import RECOGNIZER, FaceRecognizer, average_embedding
from faceforge.processors.face_swapper import SWAPPERS, TEMPLATE, FaceSwapper
from faceforge.processors.utils.face_align import match_color, paste_back, warp_face

SELECT_ALL = "all"
SELECT_LARGEST = "largest"
SELECT_REFERENCE = "reference"


@dataclass(frozen=True)
class ProcessOptions:
    """Immutable snapshot of the settings used for one job, so changing the UI
    while a video renders can't produce half-and-half results."""
    detector: str = "scrfd"
    detector_size: int = 640
    detector_score: float = 0.5
    landmarker: bool = False
    swapper: str = "inswapper_128"
    pixel_boost: int = 128
    selector: str = SELECT_ALL
    reference_distance: float = 0.6
    mask_blur: float = 0.3
    mask_padding: tuple[int, int, int, int] = (0, 0, 0, 0)
    mask_occlusion: bool = False
    mask_region: bool = False
    color_match: bool = False
    swap_enabled: bool = True
    enhancer: str | None = None
    enhancer_blend: float = 0.8
    codeformer_fidelity: float = 0.7

    @classmethod
    def from_settings(cls, s) -> "ProcessOptions":
        return cls(
            detector=s.get("face_detector_model"),
            detector_size=int(s.get("face_detector_size")),
            detector_score=float(s.get("face_detector_score")),
            landmarker=bool(s.get("face_landmarker")),
            swapper=s.get("face_swapper_model"),
            pixel_boost=int(s.get("face_swapper_pixel_boost")),
            selector=s.get("face_selector_mode"),
            reference_distance=float(s.get("reference_face_distance")),
            mask_blur=float(s.get("face_mask_blur")),
            mask_padding=tuple(int(v) for v in s.get("face_mask_padding")),
            mask_occlusion=bool(s.get("face_mask_occlusion")),
            mask_region=bool(s.get("face_mask_region")),
            color_match=bool(s.get("face_color_match")),
            swap_enabled=bool(s.get("face_swap_enabled")),
            enhancer=s.get("face_enhancer_model") if s.get("face_enhancer_enabled") else None,
            enhancer_blend=float(s.get("face_enhancer_blend")) / 100.0,
            codeformer_fidelity=float(s.get("codeformer_fidelity")),
        )

    def with_(self, **changes) -> "ProcessOptions":
        return replace(self, **changes)


@dataclass
class SwapContext:
    """Per-job inputs: the source identity and (optionally) the target to replace."""
    source_embedding: np.ndarray | None = None
    reference_embedding: np.ndarray | None = None
    _prepared: dict = field(default_factory=dict)


class FacePipeline:
    def __init__(self, models: ModelsProcessor):
        self.models = models
        self.detector = FaceDetector(models)
        self.landmarker = FaceLandmarker(models)
        self.recognizer = FaceRecognizer(models)
        self.swapper = FaceSwapper(models)
        self.enhancer = FaceEnhancer(models)
        self.masker = FaceMasker(models)

    # ---------------------------------------------------------------- planning
    @staticmethod
    def required_models(options: ProcessOptions) -> list[str]:
        keys = [options.detector]
        if options.landmarker:
            keys.append(LANDMARKER)
        if options.swap_enabled:
            keys += [RECOGNIZER, options.swapper]
            if options.mask_occlusion:
                keys.append(OCCLUSION_MODEL)
            if options.mask_region:
                keys.append(REGION_MODEL)
        elif options.selector == SELECT_REFERENCE:
            keys.append(RECOGNIZER)
        if options.enhancer:
            keys.append(options.enhancer)
        return keys

    def prepare(self, options: ProcessOptions) -> None:
        """Pin the job's models so the LRU cache never evicts them mid-video."""
        self.models.pin(self.required_models(options))

    # ---------------------------------------------------------------- analysis
    def detect(self, frame: np.ndarray, options: ProcessOptions, with_embeddings: bool = False) -> list[Face]:
        faces = self.detector.detect(frame, options.detector, options.detector_size, options.detector_score)
        if options.landmarker:
            self.landmarker.refine(frame, faces)
        if with_embeddings:
            self.recognizer.embed_all(frame, faces)
        return faces

    def source_embedding(self, images: list[np.ndarray], options: ProcessOptions) -> np.ndarray | None:
        """Identity from the largest face of each source photo, averaged."""
        embeddings = []
        for image in images:
            faces = self.detect(image, options)
            if faces:
                largest = max(faces, key=lambda f: f.area)
                embeddings.append(self.recognizer.embed(image, largest))
        return average_embedding(embeddings)

    def _select(self, frame: np.ndarray, faces: list[Face], options: ProcessOptions,
                ctx: SwapContext) -> list[Face]:
        if not faces:
            return []
        if options.selector == SELECT_LARGEST:
            return [max(faces, key=lambda f: f.area)]
        if options.selector == SELECT_REFERENCE and ctx.reference_embedding is not None:
            self.recognizer.embed_all(frame, faces)
            return [f for f in faces if f.distance(ctx.reference_embedding) < options.reference_distance]
        return faces

    # ------------------------------------------------------------------ frame
    def _swap_face(self, frame: np.ndarray, face: Face, source: np.ndarray, options: ProcessOptions) -> None:
        size = self.swapper.crop_size(options.swapper, options.pixel_boost)
        crop, matrix = warp_face(frame, face.kps, TEMPLATE, size)
        swapped, model_mask = self.swapper.swap(options.swapper, crop, source)

        mask = self.masker.box(size, options.mask_blur, options.mask_padding)
        if model_mask is not None:
            mask = np.minimum(mask, cv2.GaussianBlur(model_mask, (0, 0), size / 128))
        if options.mask_occlusion:
            mask = np.minimum(mask, self.masker.occlusion(crop))
        if options.mask_region:
            mask = np.minimum(mask, self.masker.region(crop))
        if options.color_match:
            swapped = match_color(swapped, crop, mask)
        paste_back(frame, swapped, mask, matrix)

    def process_frame(self, frame: np.ndarray, ctx: SwapContext, options: ProcessOptions) -> np.ndarray:
        """Return a processed copy of ``frame`` (BGR uint8). Thread-safe."""
        faces = self.detect(frame, options)
        targets = self._select(frame, faces, options, ctx)
        if not targets:
            return frame
        result = frame.copy()

        if options.swap_enabled and ctx.source_embedding is not None:
            key = options.swapper
            source = ctx._prepared.get(key)
            if source is None:
                source = self.swapper.prepare_source(key, ctx.source_embedding)
                ctx._prepared[key] = source
            for face in targets:
                self._swap_face(result, face, source, options)

        if options.enhancer:
            for face in targets:
                self.enhancer.enhance(result, face, options.enhancer, options.enhancer_blend,
                                      options.codeformer_fidelity)
        return result


__all__ = ["FacePipeline", "ProcessOptions", "SwapContext", "SELECT_ALL", "SELECT_LARGEST",
           "SELECT_REFERENCE", "SWAPPERS", "ENHANCERS"]
