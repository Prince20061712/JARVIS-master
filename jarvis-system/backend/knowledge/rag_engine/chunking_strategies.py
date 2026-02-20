"""
Advanced chunking strategies for document processing with semantic awareness
"""

import re
import hashlib
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class ChunkingStrategy(Enum):
    """Enum for different chunking strategies"""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    PARAGRAPH = "paragraph"
    SLIDING_WINDOW = "sliding_window"
    HIERARCHICAL = "hierarchical"
    TOPIC_BASED = "topic_based"
    ADAPTIVE = "adaptive"

@dataclass
class Chunk:
    """Represents a document chunk with metadata"""
    text: str
    chunk_id: str
    start_idx: int
    end_idx: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[np.ndarray] = None
    overlaps: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Generate chunk ID if not provided"""
        if not self.chunk_id:
            self.chunk_id = hashlib.md5(
                f"{self.start_idx}:{self.end_idx}:{self.text[:50]}".encode()
            ).hexdigest()[:16]

class ChunkingStrategies:
    """
    Advanced chunking strategies with multiple approaches and smart merging
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize chunking strategies with configuration
        
        Args:
            config: Configuration dictionary with chunking parameters
        """
        self.config = config or {}
        self.default_chunk_size = self.config.get('chunk_size', 512)
        self.default_overlap = self.config.get('chunk_overlap', 50)
        self.min_chunk_size = self.config.get('min_chunk_size', 100)
        self.max_chunk_size = self.config.get('max_chunk_size', 2000)
        
        # Initialize TF-IDF for topic detection
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        self.logger = logging.getLogger(__name__)
        
    def chunk_document(
        self,
        text: str,
        strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Chunk]:
        """
        Chunk document using specified strategy
        
        Args:
            text: Document text to chunk
            strategy: Chunking strategy to use
            metadata: Additional metadata for chunks
            **kwargs: Strategy-specific parameters
            
        Returns:
            List of Chunk objects
        """
        strategy_map = {
            ChunkingStrategy.FIXED_SIZE: self._fixed_size_chunking,
            ChunkingStrategy.SEMANTIC: self._semantic_chunking,
            ChunkingStrategy.PARAGRAPH: self._paragraph_chunking,
            ChunkingStrategy.SLIDING_WINDOW: self._sliding_window_chunking,
            ChunkingStrategy.HIERARCHICAL: self._hierarchical_chunking,
            ChunkingStrategy.TOPIC_BASED: self._topic_based_chunking,
            ChunkingStrategy.ADAPTIVE: self._adaptive_chunking
        }
        
        chunking_func = strategy_map.get(strategy, self._semantic_chunking)
        chunks = chunking_func(text, metadata or {}, **kwargs)
        
        # Post-process chunks
        chunks = self._merge_small_chunks(chunks)
        chunks = self._split_large_chunks(chunks)
        
        return chunks
    
    def _fixed_size_chunking(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
        **kwargs
    ) -> List[Chunk]:
        """Fixed-size chunking with overlap"""
        chunk_size = chunk_size or self.default_chunk_size
        overlap = overlap or self.default_overlap
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            if len(chunk_words) < self.min_chunk_size and i > 0:
                continue
                
            chunk_text = ' '.join(chunk_words)
            chunk = Chunk(
                text=chunk_text,
                chunk_id=f"fixed_{i}",
                start_idx=i,
                end_idx=i + len(chunk_words),
                metadata={
                    **metadata,
                    'strategy': 'fixed_size',
                    'chunk_index': len(chunks),
                    'word_count': len(chunk_words)
                }
            )
            
            # Track overlaps
            if i > 0:
                chunk.overlaps.append(chunks[-1].chunk_id)
                chunks[-1].overlaps.append(chunk.chunk_id)
            
            chunks.append(chunk)
        
        return chunks
    
    def _semantic_chunking(
        self,
        text: str,
        metadata: Dict[str, Any],
        similarity_threshold: float = 0.7,
        **kwargs
    ) -> List[Chunk]:
        """
        Semantic chunking based on topic continuity
        Uses sentence embeddings and similarity to detect topic boundaries
        """
        sentences = sent_tokenize(text)
        if len(sentences) <= 1:
            return [Chunk(
                text=text,
                chunk_id="semantic_0",
                start_idx=0,
                end_idx=len(text),
                metadata={**metadata, 'strategy': 'semantic'}
            )]
        
        # Get sentence embeddings (simplified - in production use actual embeddings)
        sentence_vectors = self._get_sentence_vectors(sentences)
        
        chunks = []
        current_chunk = []
        current_start = 0
        
        for i in range(1, len(sentences)):
            # Calculate similarity between consecutive sentences
            similarity = self._cosine_similarity(
                sentence_vectors[i-1],
                sentence_vectors[i]
            )
            
            current_chunk.append(sentences[i-1])
            
            # If similarity drops below threshold, create chunk boundary
            if similarity < similarity_threshold and len(current_chunk) >= 3:
                chunk_text = ' '.join(current_chunk)
                chunks.append(Chunk(
                    text=chunk_text,
                    chunk_id=f"semantic_{len(chunks)}",
                    start_idx=current_start,
                    end_idx=current_start + len(current_chunk),
                    metadata={
                        **metadata,
                        'strategy': 'semantic',
                        'num_sentences': len(current_chunk),
                        'avg_similarity': similarity
                    }
                ))
                current_chunk = []
                current_start = i
        
        # Add last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(Chunk(
                text=chunk_text,
                chunk_id=f"semantic_{len(chunks)}",
                start_idx=current_start,
                end_idx=len(sentences),
                metadata={
                    **metadata,
                    'strategy': 'semantic',
                    'num_sentences': len(current_chunk)
                }
            ))
        
        return chunks
    
    def _paragraph_chunking(
        self,
        text: str,
        metadata: Dict[str, Any],
        **kwargs
    ) -> List[Chunk]:
        """Chunk by paragraphs with smart merging"""
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for i, para in enumerate(paragraphs):
            para_size = len(para.split())
            
            # If adding this paragraph exceeds max size, create new chunk
            if current_size + para_size > self.max_chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(Chunk(
                    text=chunk_text,
                    chunk_id=f"para_{len(chunks)}",
                    start_idx=i - len(current_chunk),
                    end_idx=i,
                    metadata={
                        **metadata,
                        'strategy': 'paragraph',
                        'num_paragraphs': len(current_chunk),
                        'paragraph_indices': list(range(i - len(current_chunk), i))
                    }
                ))
                current_chunk = []
                current_size = 0
            
            current_chunk.append(para)
            current_size += para_size
        
        # Add last chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(Chunk(
                text=chunk_text,
                chunk_id=f"para_{len(chunks)}",
                start_idx=len(paragraphs) - len(current_chunk),
                end_idx=len(paragraphs),
                metadata={
                    **metadata,
                    'strategy': 'paragraph',
                    'num_paragraphs': len(current_chunk)
                }
            ))
        
        return chunks
    
    def _sliding_window_chunking(
        self,
        text: str,
        metadata: Dict[str, Any],
        window_size: int = 3,
        step_size: int = 1,
        **kwargs
    ) -> List[Chunk]:
        """
        Sliding window chunking for better context preservation
        Useful for processing with overlap at sentence level
        """
        sentences = sent_tokenize(text)
        chunks = []
        
        for i in range(0, len(sentences) - window_size + 1, step_size):
            window_sentences = sentences[i:i + window_size]
            chunk_text = ' '.join(window_sentences)
            
            chunk = Chunk(
                text=chunk_text,
                chunk_id=f"slide_{i}",
                start_idx=i,
                end_idx=i + window_size,
                metadata={
                    **metadata,
                    'strategy': 'sliding_window',
                    'window_index': i,
                    'num_sentences': len(window_sentences)
                }
            )
            
            # Track overlaps with previous chunks
            if i > 0:
                chunk.overlaps.append(chunks[-1].chunk_id)
                chunks[-1].overlaps.append(chunk.chunk_id)
            
            chunks.append(chunk)
        
        return chunks
    
    def _hierarchical_chunking(
        self,
        text: str,
        metadata: Dict[str, Any],
        **kwargs
    ) -> List[Chunk]:
        """
        Create hierarchical chunks (document -> sections -> paragraphs)
        Useful for structured documents
        """
        # First, try to detect sections based on common patterns
        section_patterns = [
            r'(?:^|\n)(?:#{1,3}\s+)(.+?)(?:\n|$)',
            r'(?:^|\n)(?:[A-Z][A-Z\s]+)(?:\n|$)',
            r'(?:^|\n)(?:\d+\.\s+)(.+?)(?:\n|$)'
        ]
        
        sections = []
        current_pos = 0
        
        for pattern in section_patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE))
            if matches:
                for i, match in enumerate(matches):
                    start = match.start()
                    end = match.end() if i == len(matches) - 1 else matches[i + 1].start()
                    
                    section_text = text[start:end].strip()
                    if section_text:
                        sections.append({
                            'text': section_text,
                            'title': match.group(1) if match.groups() else '',
                            'start': start,
                            'end': end
                        })
                break
        
        # If no sections found, treat as single section
        if not sections:
            sections = [{
                'text': text,
                'title': '',
                'start': 0,
                'end': len(text)
            }]
        
        chunks = []
        for section_idx, section in enumerate(sections):
            # Chunk each section into paragraphs
            paragraphs = re.split(r'\n\s*\n', section['text'])
            
            for para_idx, para in enumerate(paragraphs):
                if para.strip():
                    chunk = Chunk(
                        text=para.strip(),
                        chunk_id=f"hier_{section_idx}_{para_idx}",
                        start_idx=section['start'] + para_idx,
                        end_idx=section['start'] + para_idx + 1,
                        metadata={
                            **metadata,
                            'strategy': 'hierarchical',
                            'section_index': section_idx,
                            'section_title': section['title'],
                            'paragraph_index': para_idx,
                            'section_start': section['start'],
                            'section_end': section['end']
                        }
                    )
                    chunks.append(chunk)
        
        return chunks
    
    def _topic_based_chunking(
        self,
        text: str,
        metadata: Dict[str, Any],
        num_topics: int = 5,
        **kwargs
    ) -> List[Chunk]:
        """
        Topic-based chunking using TF-IDF and clustering
        Groups sentences by topic coherence
        """
        sentences = sent_tokenize(text)
        if len(sentences) < num_topics:
            return self._paragraph_chunking(text, metadata)
        
        # Create TF-IDF matrix for sentences
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(sentences)
            
            # Simple clustering based on TF-IDF similarity
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=min(num_topics, len(sentences)), random_state=42)
            clusters = kmeans.fit_predict(tfidf_matrix)
            
            # Group sentences by cluster
            cluster_groups = defaultdict(list)
            for idx, cluster_id in enumerate(clusters):
                cluster_groups[cluster_id].append(idx)
            
            chunks = []
            for cluster_id, sentence_indices in cluster_groups.items():
                if sentence_indices:
                    # Sort indices to maintain order
                    sentence_indices.sort()
                    cluster_sentences = [sentences[i] for i in sentence_indices]
                    chunk_text = ' '.join(cluster_sentences)
                    
                    chunks.append(Chunk(
                        text=chunk_text,
                        chunk_id=f"topic_{cluster_id}",
                        start_idx=min(sentence_indices),
                        end_idx=max(sentence_indices),
                        metadata={
                            **metadata,
                            'strategy': 'topic_based',
                            'cluster_id': cluster_id,
                            'num_sentences': len(cluster_sentences),
                            'sentence_indices': sentence_indices
                        }
                    ))
            
            # Sort chunks by original order
            chunks.sort(key=lambda x: x.start_idx)
            return chunks
            
        except Exception as e:
            self.logger.warning(f"Topic-based chunking failed: {e}. Falling back to semantic chunking.")
            return self._semantic_chunking(text, metadata)
    
    def _adaptive_chunking(
        self,
        text: str,
        metadata: Dict[str, Any],
        **kwargs
    ) -> List[Chunk]:
        """
        Adaptive chunking that selects best strategy based on text characteristics
        """
        text_length = len(text.split())
        
        # Heuristics for strategy selection
        if text_length < self.min_chunk_size * 2:
            # Short text - use fixed size
            return self._fixed_size_chunking(text, metadata)
        
        # Check for paragraph structure
        paragraphs = re.split(r'\n\s*\n', text)
        if len(paragraphs) > 3:
            # Clear paragraph structure - use paragraph chunking
            return self._paragraph_chunking(text, metadata)
        
        # Check for section headers
        has_headers = bool(re.search(r'(?:^|\n)#{1,3}\s+', text, re.MULTILINE))
        if has_headers:
            # Structured document - use hierarchical
            return self._hierarchical_chunking(text, metadata)
        
        # Default to semantic chunking for prose
        return self._semantic_chunking(text, metadata)
    
    def _merge_small_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Merge chunks that are too small"""
        merged = []
        current_chunk = None
        
        for chunk in chunks:
            chunk_size = len(chunk.text.split())
            
            if current_chunk is None:
                current_chunk = chunk
            elif chunk_size < self.min_chunk_size:
                # Merge small chunk with previous
                current_chunk.text += " " + chunk.text
                current_chunk.end_idx = chunk.end_idx
                current_chunk.metadata['merged'] = True
                current_chunk.metadata['original_chunks'] = current_chunk.metadata.get('original_chunks', []) + [chunk.chunk_id]
            else:
                merged.append(current_chunk)
                current_chunk = chunk
        
        if current_chunk:
            merged.append(current_chunk)
        
        return merged
    
    def _split_large_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Split chunks that exceed maximum size"""
        split_chunks = []
        
        for chunk in chunks:
            chunk_size = len(chunk.text.split())
            
            if chunk_size <= self.max_chunk_size:
                split_chunks.append(chunk)
            else:
                # Split large chunk into smaller ones
                sub_chunks = self._fixed_size_chunking(
                    chunk.text,
                    {**chunk.metadata, 'parent_chunk': chunk.chunk_id},
                    chunk_size=self.max_chunk_size // 2
                )
                split_chunks.extend(sub_chunks)
        
        return split_chunks
    
    def _get_sentence_vectors(self, sentences: List[str]) -> List[np.ndarray]:
        """
        Get simple TF-IDF based vectors for sentences
        In production, replace with actual sentence embeddings
        """
        try:
            tfidf = self.tfidf_vectorizer.fit_transform(sentences)
            return [tfidf[i].toarray().flatten() for i in range(len(sentences))]
        except:
            # Fallback to random vectors
            return [np.random.randn(100) for _ in sentences]
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return np.dot(vec1, vec2) / (norm1 * norm2)