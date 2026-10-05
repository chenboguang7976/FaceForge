"""ONNX Runtime model manager and inference session handler.

Handles loading, caching, and running ONNX models efficiently on CPU/GPU
using onnxruntime and optional TensorRT acceleration.
"""
import threading
import os
from typing import Dict, Any, Optional
import numpy as np

try:
    import onnxruntime
except ImportError:
    onnxruntime = None

import torch

from faceforge.config import Settings
from faceforge.core.models_data import get_model_data, MODELS_DIR

# Suppress verbose ONNX warnings
if onnxruntime:
    onnxruntime.set_default_logger_severity(4)
    onnxruntime.log_verbosity_level = -1


class ModelsProcessor:
    """Manages AI model lifecycle, memory, and execution providers."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one model manager exists."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelsProcessor, cls).__new__(cls)
        return cls._instance

    def __init__(self, settings: Settings):
        if hasattr(self, "initialized") and self.initialized:
            return

        self.settings = settings
        self.device = self.settings.get("device", "cuda")
        self.models: Dict[str, Any] = {}
        self.model_lock = threading.RLock()
        
        # Setup Execution Providers
        if self.device == "cuda":
            self.providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        else:
            self.providers = ['CPUExecutionProvider']

        self.syncvec = None
        if self.device == "cuda":
            if torch.cuda.is_available():
                self.syncvec = torch.empty((1, 1), dtype=torch.float32, device="cuda")
            else:
                print("[Warning] CUDA configured but torch cannot access GPU. Falling back to CPU.")
                self.device = "cpu"
                self.providers = ['CPUExecutionProvider']

        # Pre-calculated transformation matrix for Inswapper
        self.emap = np.load(os.path.join(MODELS_DIR, "emap.npy")) if os.path.exists(os.path.join(MODELS_DIR, "emap.npy")) else None

        self.initialized = True

    def get_model(self, model_name: str) -> Optional[Any]:
        """Get a loaded model by name, loading it if necessary."""
        with self.model_lock:
            if model_name not in self.models or self.models[model_name] is None:
                self.load_model(model_name)
            return self.models.get(model_name)

    def load_model(self, model_name: str) -> bool:
        """Load an ONNX model into memory."""
        if not onnxruntime:
            print("[Error] onnxruntime not installed.")
            return False

        model_data = get_model_data(model_name)
        if not model_data:
            print(f"[Error] Model {model_name} not found in registry.")
            return False

        model_path = model_data["local_path"]
        if not os.path.exists(model_path):
            print(f"[Error] Model file not found: {model_path}. Please download it to the models directory.")
            return False

        try:
            print(f"Loading model: {model_name} onto {self.device}...")
            
            # Create ONNX session options
            session_options = onnxruntime.SessionOptions()
            session_options.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            # Load the model
            session = onnxruntime.InferenceSession(
                model_path,
                sess_options=session_options,
                providers=self.providers
            )
            
            with self.model_lock:
                self.models[model_name] = session
                
            return True
        except Exception as e:
            print(f"[Error] Failed to load {model_name}: {e}")
            return False

    def clear_model(self, model_name: str):
        """Remove a model from memory to free VRAM/RAM."""
        with self.model_lock:
            if model_name in self.models:
                del self.models[model_name]
                self.models[model_name] = None
        
        # Force garbage collection
        import gc
        gc.collect()
        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()

    def clear_all_models(self):
        """Clear all loaded models."""
        with self.model_lock:
            for name in list(self.models.keys()):
                del self.models[name]
            self.models.clear()
            
        import gc
        gc.collect()
        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()

    def synchronize(self):
        """Synchronize execution streams (useful for GPU)."""
        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.synchronize()
        elif self.device != "cpu" and self.syncvec is not None:
            self.syncvec.cpu()

    # Convenience wrapper for IO Binding
    def run_with_iobinding(self, model_name: str, inputs: Dict[str, torch.Tensor], outputs: Dict[str, torch.Tensor]):
        """Run a model using efficient IOBinding (Zero-copy GPU transfer)."""
        model = self.get_model(model_name)
        if not model:
            return False
            
        io_binding = model.io_binding()
        
        # Bind inputs
        for name, tensor in inputs.items():
            io_binding.bind_input(
                name=name,
                device_type=self.device,
                device_id=0,
                element_type=np.float32,
                shape=tuple(tensor.shape),
                buffer_ptr=tensor.data_ptr()
            )
            
        # Bind outputs
        for name, tensor in outputs.items():
            io_binding.bind_output(
                name=name,
                device_type=self.device,
                device_id=0,
                element_type=np.float32,
                shape=tuple(tensor.shape),
                buffer_ptr=tensor.data_ptr()
            )
            
        self.synchronize()
        model.run_with_iobinding(io_binding)
        return True
