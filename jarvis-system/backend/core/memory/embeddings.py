import numpy as np
from typing import List, Union

# Try to import sentence_transformers, handle failure for CI/minimal envs
try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance.model = None
        return cls._instance

    def __init__(self):
        if self.model is None and HAS_TRANSFORMERS:
            # Load a small efficient model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def encode(self, text: Union[str, List[str]]) -> np.ndarray:
        if not HAS_TRANSFORMERS or not self.model:
            # Fallback for environments without the library
            # Return random vector or zero vector of dim 384
            if isinstance(text, str):
                return np.zeros(384)
            return np.zeros((len(text), 384))
        
        return self.model.encode(text)
