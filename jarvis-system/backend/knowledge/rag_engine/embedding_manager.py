"""
Advanced embedding manager with multiple model support, caching, and batching
"""

import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
import hashlib
import pickle
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta
import json
from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hnswlib

# sentence-transformers will try to import cached_download from huggingface_hub
# which was removed in recent releases.  Provide a clear error if the environment
# has an incompatible hub version and hint at the required pin in requirements.
try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    msg = str(e)
    if 'cached_download' in msg or 'huggingface_hub' in msg:
        raise ImportError(
            "Failed to import SentenceTransformer due to incompatible "
            "huggingface_hub version.\n"
            "Please install a compatible release (e.g. `huggingface_hub<0.17`). "
            "Updating `requirements/rag.txt` and reinstalling the RAG dependencies "
            "typically resolves this issue."
        ) from e
    raise

import torch
from sklearn.decomposition import PCA
from sklearn.preprocessing import normalize

class EmbeddingManager:
    """
    Advanced embedding manager with multiple model support, caching, and vector search
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize embedding manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.cache_dir = Path(self.config.get('cache_dir', './cache/embeddings'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Model configuration
        self.model_name = self.config.get('model_name', 'all-MiniLM-L6-v2')
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.batch_size = self.config.get('batch_size', 32)
        self.max_length = self.config.get('max_length', 512)
        self.normalize_embeddings = self.config.get('normalize_embeddings', True)
        
        # Cache configuration
        self.cache_ttl = self.config.get('cache_ttl', 86400)  # 24 hours
        self.memory_cache_size = self.config.get('memory_cache_size', 10000)
        
        # Initialize model
        self.model = None
        self._load_model()
        
        # Initialize in-memory caches
        self.embedding_cache = {}  # LRU cache
        self.dimension = None
        
        # Vector store configuration
        self.vector_store = None
        self.vector_store_index = {}
        self.vector_store_metadata = {}
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=self.config.get('max_workers', 4))
        
        # Dimension reduction
        self.pca = None
        self.reduced_dimension = self.config.get('reduced_dimension', None)
        
        self.logger = logging.getLogger(__name__)
        
    def _load_model(self):
        """Load the embedding model"""
        try:
            self.logger.info(f"Loading model {self.model_name} on {self.device}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.dimension = self.model.get_sentence_embedding_dimension()
            
            # Test embedding to verify
            test_emb = self.model.encode(["test"], convert_to_numpy=True)
            self.logger.info(f"Model loaded. Embedding dimension: {self.dimension}")
            
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            raise
    
    def get_embeddings(
        self,
        texts: Union[str, List[str]],
        use_cache: bool = True,
        batch_processing: bool = True,
        **kwargs
    ) -> np.ndarray:
        """
        Get embeddings for text(s)
        
        Args:
            texts: Single text or list of texts
            use_cache: Whether to use cache
            batch_processing: Whether to use batch processing
            **kwargs: Additional arguments
            
        Returns:
            Numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
            single = True
        else:
            single = False
        
        if not texts:
            return np.array([])
        
        # Check cache first
        if use_cache:
            cached_embeddings, texts_to_process = self._get_from_cache(texts)
        else:
            cached_embeddings = {}
            texts_to_process = texts
        
        # Process remaining texts
        if texts_to_process:
            if batch_processing and len(texts_to_process) > 1:
                new_embeddings = self._get_embeddings_batch(texts_to_process, **kwargs)
            else:
                new_embeddings = self._get_embeddings_sequential(texts_to_process, **kwargs)
            
            # Update cache
            if use_cache:
                self._update_cache(texts_to_process, new_embeddings)
            
            # Combine with cached results
            all_embeddings = []
            for text in texts:
                if text in cached_embeddings:
                    all_embeddings.append(cached_embeddings[text])
                else:
                    idx = texts_to_process.index(text)
                    all_embeddings.append(new_embeddings[idx])
            
            result = np.array(all_embeddings)
        else:
            result = np.array([cached_embeddings[t] for t in texts])
        
        # Normalize if required
        if self.normalize_embeddings:
            result = normalize(result, norm='l2')
        
        # Apply dimension reduction if configured
        if self.reduced_dimension and self.reduced_dimension < self.dimension:
            result = self._reduce_dimensions(result)
        
        return result[0] if single else result
    
    def _get_embeddings_batch(self, texts: List[str], **kwargs) -> np.ndarray:
        """Get embeddings in batches"""
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            try:
                # Truncate texts if needed
                truncated_batch = [self._truncate_text(t, self.max_length) for t in batch]
                
                # Get embeddings
                embeddings = self.model.encode(
                    truncated_batch,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    **kwargs
                )
                all_embeddings.append(embeddings)
                
            except Exception as e:
                self.logger.error(f"Error in batch embedding: {e}")
                # Fallback to sequential for this batch
                for text in batch:
                    try:
                        emb = self.model.encode([text], convert_to_numpy=True)
                        all_embeddings.append(emb)
                    except:
                        all_embeddings.append(np.zeros(self.dimension))
        
        return np.vstack(all_embeddings)
    
    def _get_embeddings_sequential(self, texts: List[str], **kwargs) -> np.ndarray:
        """Get embeddings sequentially"""
        embeddings = []
        for text in texts:
            try:
                truncated = self._truncate_text(text, self.max_length)
                emb = self.model.encode([truncated], convert_to_numpy=True)[0]
                embeddings.append(emb)
            except Exception as e:
                self.logger.error(f"Error getting embedding: {e}")
                embeddings.append(np.zeros(self.dimension))
        
        return np.array(embeddings)
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to max tokens (approximate)"""
        words = text.split()
        if len(words) > max_length:
            return ' '.join(words[:max_length])
        return text
    
    def _get_from_cache(self, texts: List[str]) -> Tuple[Dict[str, np.ndarray], List[str]]:
        """
        Get embeddings from cache
        
        Returns:
            Tuple of (cached_embeddings_dict, texts_to_process_list)
        """
        cached = {}
        to_process = []
        
        for text in texts:
            # Check memory cache first
            if text in self.embedding_cache:
                cached[text] = self.embedding_cache[text]
                continue
            
            # Check disk cache
            cache_key = self._get_cache_key(text)
            cache_path = self.cache_dir / f"{cache_key}.pkl"
            
            if cache_path.exists():
                try:
                    with open(cache_path, 'rb') as f:
                        data = pickle.load(f)
                        # Check if cache is still valid
                        if datetime.now().timestamp() - data['timestamp'] < self.cache_ttl:
                            cached[text] = data['embedding']
                            # Update memory cache
                            self._update_memory_cache(text, data['embedding'])
                        else:
                            cache_path.unlink()  # Remove expired cache
                            to_process.append(text)
                except:
                    to_process.append(text)
            else:
                to_process.append(text)
        
        return cached, to_process
    
    def _update_cache(self, texts: List[str], embeddings: np.ndarray):
        """Update cache with new embeddings"""
        for text, embedding in zip(texts, embeddings):
            # Update memory cache
            self._update_memory_cache(text, embedding)
            
            # Update disk cache
            cache_key = self._get_cache_key(text)
            cache_path = self.cache_dir / f"{cache_key}.pkl"
            
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump({
                        'text': text,
                        'embedding': embedding,
                        'timestamp': datetime.now().timestamp()
                    }, f)
            except Exception as e:
                self.logger.error(f"Error writing cache: {e}")
    
    def _update_memory_cache(self, text: str, embedding: np.ndarray):
        """Update memory cache with LRU logic"""
        if len(self.embedding_cache) >= self.memory_cache_size:
            # Simple LRU: remove first item
            self.embedding_cache.pop(next(iter(self.embedding_cache)))
        
        self.embedding_cache[text] = embedding
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def build_vector_store(
        self,
        embeddings: np.ndarray,
        metadata: List[Dict[str, Any]],
        index_name: str = "default",
        space: str = 'cosine',
        ef_construction: int = 200,
        M: int = 16
    ):
        """
        Build HNSW vector store for similarity search
        
        Args:
            embeddings: Numpy array of embeddings
            metadata: List of metadata dictionaries
            index_name: Name of the index
            space: Distance space ('l2', 'ip', 'cosine')
            ef_construction: Construction parameter
            M: Number of bi-directional links
        """
        num_elements = len(embeddings)
        dim = embeddings.shape[1]
        
        # Initialize index
        index = hnswlib.Index(space=space, dim=dim)
        index.init_index(max_elements=num_elements, ef_construction=ef_construction, M=M)
        
        # Add items
        index.add_items(embeddings, list(range(num_elements)))
        
        # Set default ef
        index.set_ef(min(num_elements, 100))
        
        # Store
        self.vector_store = index
        self.vector_store_index[index_name] = index
        self.vector_store_metadata[index_name] = metadata
        
        self.logger.info(f"Built vector store with {num_elements} items")
    
    def similarity_search(
        self,
        query: Union[str, np.ndarray],
        index_name: str = "default",
        k: int = 5,
        return_scores: bool = True,
        **kwargs
    ) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], List[float]]]:
        """
        Perform similarity search
        
        Args:
            query: Query text or embedding
            index_name: Name of the index to search
            k: Number of results to return
            return_scores: Whether to return similarity scores
            **kwargs: Additional arguments
            
        Returns:
            List of metadata for similar items, optionally with scores
        """
        if index_name not in self.vector_store_index:
            raise ValueError(f"Index {index_name} not found")
        
        index = self.vector_store_index[index_name]
        metadata = self.vector_store_metadata[index_name]
        
        # Get query embedding if text
        if isinstance(query, str):
            query_emb = self.get_embeddings(query)
        else:
            query_emb = query
        
        # Ensure query is 2D
        if query_emb.ndim == 1:
            query_emb = query_emb.reshape(1, -1)
        
        # Search
        labels, distances = index.knn_query(query_emb, k=min(k, len(metadata)))
        
        # Get results
        results = []
        for idx, label in enumerate(labels[0]):
            if label < len(metadata):
                result = metadata[label].copy()
                if return_scores:
                    result['similarity_score'] = 1 - distances[0][idx]  # Convert distance to similarity
                results.append(result)
        
        if return_scores:
            scores = [r.pop('similarity_score') for r in results]
            return results, scores
        else:
            return results
    
    def save_vector_store(self, path: Union[str, Path], index_name: str = "default"):
        """Save vector store to disk"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if index_name in self.vector_store_index:
            index = self.vector_store_index[index_name]
            metadata = self.vector_store_metadata[index_name]
            
            # Save index
            index.save_index(str(path.with_suffix('.bin')))
            
            # Save metadata
            with open(path.with_suffix('.json'), 'w') as f:
                json.dump(metadata, f)
    
    def load_vector_store(self, path: Union[str, Path], index_name: str = "default"):
        """Load vector store from disk"""
        path = Path(path)
        
        if not path.with_suffix('.bin').exists():
            raise FileNotFoundError(f"Index file not found: {path}.bin")
        
        # Load metadata
        with open(path.with_suffix('.json'), 'r') as f:
            metadata = json.load(f)
        
        # Initialize index
        dim = len(metadata[0]['embedding']) if 'embedding' in metadata[0] else self.dimension
        index = hnswlib.Index(space='cosine', dim=dim)
        
        # Load index
        index.load_index(str(path.with_suffix('.bin')))
        
        # Store
        self.vector_store_index[index_name] = index
        self.vector_store_metadata[index_name] = metadata
    
    def _reduce_dimensions(self, embeddings: np.ndarray) -> np.ndarray:
        """Reduce embedding dimensions using PCA"""
        if self.pca is None:
            self.pca = PCA(n_components=self.reduced_dimension)
            return self.pca.fit_transform(embeddings)
        else:
            return self.pca.transform(embeddings)
    
    @lru_cache(maxsize=1000)
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        emb1 = self.get_embeddings(text1)
        emb2 = self.get_embeddings(text2)
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)
    
    def clear_cache(self):
        """Clear all caches"""
        self.embedding_cache.clear()
        self.compute_similarity.cache_clear()
        
        # Optionally clear disk cache
        if self.config.get('clear_disk_cache', False):
            for cache_file in self.cache_dir.glob('*.pkl'):
                cache_file.unlink()