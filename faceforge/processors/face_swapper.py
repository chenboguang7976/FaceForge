"""Face Swapping module.

Implements various face swap architectures including Inswapper (InsightFace),
InStyleSwapper, SimSwap, GhostFace, CSCS, etc.
"""
import numpy as np
import torch
from typing import Dict, Any, Tuple

from faceforge.core.models_processor import ModelsProcessor

class FaceSwapper:
    """Handles execution of different face swap models."""

    def __init__(self, models_processor: ModelsProcessor):
        self.mp = models_processor

    def _l2norm(self, x):
        """L2 normalization for embeddings."""
        return np.linalg.norm(x)

    def calc_inswapper_latent(self, source_embedding: np.ndarray) -> np.ndarray:
        """Calculate latent vector for Inswapper based on ArcFace embedding."""
        if self.mp.emap is None:
            raise ValueError("emap.npy is required for Inswapper. Please download it to the models folder.")
            
        n_e = source_embedding / self._l2norm(source_embedding)
        latent = n_e.reshape((1, -1))
        latent = np.dot(latent, self.mp.emap)
        latent /= np.linalg.norm(latent)
        return latent

    def run_inswapper(self, image: torch.Tensor, embedding: torch.Tensor, output: torch.Tensor):
        """Run Inswapper128 face swap model.
        
        Args:
            image: Target face image crop tensor (1, 3, 128, 128)
            embedding: Source face embedding latent tensor (1, 512)
            output: Tensor to store the swapped face
        """
        inputs = {
            'target': image,
            'source': embedding
        }
        outputs = {
            'output': output
        }
        self.mp.run_with_iobinding('Inswapper128', inputs, outputs)

    def run_iss_swapper(self, image: torch.Tensor, embedding: torch.Tensor, output: torch.Tensor, version: str = "A"):
        """Run InStyleSwapper256 face swap model (Versions A, B, C)."""
        model_name = f'InStyleSwapper256 Version {version}'
        inputs = {
            'target': image,
            'source': embedding
        }
        outputs = {
            'output': output
        }
        self.mp.run_with_iobinding(model_name, inputs, outputs)

    def calc_swapper_latent_simswap(self, source_embedding: np.ndarray) -> np.ndarray:
        """Calculate latent vector for SimSwap."""
        latent = source_embedding.reshape(1, -1)
        latent = latent / np.linalg.norm(latent, axis=1, keepdims=True)
        return latent

    def run_simswap512(self, image: torch.Tensor, embedding: torch.Tensor, output: torch.Tensor):
        """Run SimSwap512 face swap model."""
        inputs = {
            'input': image,
            'onnx::Gemm_1': embedding
        }
        outputs = {
            'output': output
        }
        self.mp.run_with_iobinding('SimSwap512', inputs, outputs)

    def run_ghostface(self, image: torch.Tensor, embedding: torch.Tensor, output: torch.Tensor, version: str = "v2"):
        """Run GhostFace face swap model (v1, v2, v3)."""
        model_name = f'GhostFace{version.replace("-", "")}'
        
        # GhostFace versions have different output tensor names
        output_name_map = {
            'GhostFacev1': '781',
            'GhostFacev2': '1165',
            'GhostFacev3': '1549'
        }
        output_name = output_name_map.get(model_name, 'output')
        
        inputs = {
            'target': image,
            'source': embedding
        }
        outputs = {
            output_name: output
        }
        self.mp.run_with_iobinding(model_name, inputs, outputs)

    def run_cscs(self, image: torch.Tensor, embedding: torch.Tensor, output: torch.Tensor):
        """Run CSCS Cross-Subject Face Swap model."""
        inputs = {
            'input_1': image,
            'input_2': embedding
        }
        outputs = {
            'output': output
        }
        self.mp.run_with_iobinding('CSCS', inputs, outputs)
