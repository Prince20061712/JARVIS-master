"""
Cognitive Layer - Handles core knowledge processing, RAG, and context retrieval
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
from enum import Enum
import json
import hashlib
from collections import defaultdict
import re

logger = logging.getLogger(__name__)


class KnowledgeDomain(Enum):
    """Academic knowledge domains"""
    MATHEMATICS = "mathematics"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    COMPUTER_SCIENCE = "computer_science"
    ENGINEERING = "engineering"
    GENERAL = "general"


class DifficultyLevel(Enum):
    """Difficulty levels for content"""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4


@dataclass
class KnowledgeChunk:
    """Represents a chunk of knowledge with metadata"""
    id: str
    content: str
    domain: KnowledgeDomain
    difficulty: DifficultyLevel
    prerequisites: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    embedding: Optional[np.ndarray] = None
    source: str = ""
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    last_accessed: Optional[datetime] = None


@dataclass
class CognitiveContext:
    """Context information for cognitive processing"""
    query: str
    domain: Optional[KnowledgeDomain] = None
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    preferred_language: str = "en"
    include_examples: bool = True
    max_results: int = 5


@dataclass
class RAGResult:
    """Result from Retrieval-Augmented Generation"""
    chunks: List[KnowledgeChunk]
    query: str
    relevance_scores: List[float]
    execution_time_ms: float
    total_chunks_found: int
    context_window: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    suggested_domains: List[KnowledgeDomain] = field(default_factory=list)


class CognitiveLayer:
    """
    Handles core knowledge processing and RAG operations.
    Implements sophisticated retrieval with semantic search and context awareness.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Knowledge base storage
        self.knowledge_base: Dict[str, KnowledgeChunk] = {}
        self.domain_index: Dict[KnowledgeDomain, List[str]] = defaultdict(list)
        self.concept_graph: Dict[str, Set[str]] = defaultdict(set)
        
        # Cache for frequently accessed chunks
        self.cache: Dict[str, Tuple[KnowledgeChunk, datetime]] = {}
        self.cache_ttl = timedelta(minutes=30)
        self.cache_max_size = 1000
        
        # Embedding cache
        self.embedding_cache: Dict[str, np.ndarray] = {}
        
        # Performance metrics
        self.metrics = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_response_time': 0.0,
            'domain_distribution': defaultdict(int)
        }
        
        # Initialize with sample knowledge base
        self._initialize_knowledge_base()
        
        logger.info(f"Cognitive Layer initialized with {len(self.knowledge_base)} knowledge chunks")
    
    def _initialize_knowledge_base(self):
        """Initialize the knowledge base with core educational content"""
        # Mathematics
        self.add_knowledge_chunk(
            content="Calculus is the mathematical study of continuous change. It has two major branches: differential calculus and integral calculus.",
            domain=KnowledgeDomain.MATHEMATICS,
            difficulty=DifficultyLevel.INTERMEDIATE,
            related_concepts=["limits", "derivatives", "integrals", "functions"],
            source="Core Mathematics"
        )
        
        self.add_knowledge_chunk(
            content="Derivatives measure the rate of change of a function. The derivative of f(x) with respect to x is the function f'(x) = lim(h→0) [f(x+h) - f(x)]/h",
            domain=KnowledgeDomain.MATHEMATICS,
            difficulty=DifficultyLevel.ADVANCED,
            prerequisites=["limits"],
            related_concepts=["rate of change", "slope", "tangent lines"],
            source="Calculus Fundamentals"
        )
        
        # Physics
        self.add_knowledge_chunk(
            content="Newton's Second Law states that force equals mass times acceleration (F = ma). This fundamental principle relates the net force acting on an object to its mass and acceleration.",
            domain=KnowledgeDomain.PHYSICS,
            difficulty=DifficultyLevel.BEGINNER,
            related_concepts=["force", "mass", "acceleration", "mechanics"],
            source="Classical Mechanics"
        )
        
        # Computer Science
        self.add_knowledge_chunk(
            content="Machine Learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
            domain=KnowledgeDomain.COMPUTER_SCIENCE,
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisites=["programming basics", "statistics"],
            related_concepts=["AI", "neural networks", "deep learning", "data science"],
            source="AI Fundamentals"
        )
    
    async def process(self, 
                     context: CognitiveContext,
                     force_refresh: bool = False) -> RAGResult:
        """
        Process a query using RAG and cognitive reasoning
        
        Args:
            context: Cognitive context with query and parameters
            force_refresh: Ignore cache and force fresh retrieval
            
        Returns:
            RAGResult with relevant knowledge chunks
        """
        start_time = datetime.now()
        self.metrics['total_queries'] += 1
        
        try:
            # Preprocess query
            processed_query = self._preprocess_query(context.query)
            
            # Check cache
            if not force_refresh:
                cached_result = self._check_cache(processed_query, context)
                if cached_result:
                    self.metrics['cache_hits'] += 1
                    return cached_result
            
            self.metrics['cache_misses'] += 1
            
            # Perform multi-stage retrieval
            relevant_chunks = await self._retrieve_relevant_chunks(processed_query, context)
            
            # Score and rank chunks
            scored_chunks = self._score_chunks(relevant_chunks, processed_query, context)
            
            # Apply domain filtering if specified
            if context.domain:
                scored_chunks = [
                    (chunk, score) for chunk, score in scored_chunks 
                    if chunk.domain == context.domain
                ]
            
            # Select top chunks
            top_chunks = self._select_top_chunks(scored_chunks, context.max_results)
            
            # Build context window
            context_window = self._build_context_window(top_chunks)
            
            # Update usage statistics
            self._update_usage_stats(top_chunks)
            
            # Cache the result
            result = RAGResult(
                chunks=[chunk for chunk, _ in top_chunks],
                query=context.query,
                relevance_scores=[score for _, score in top_chunks],
                execution_time_ms=self._calculate_elapsed_ms(start_time),
                total_chunks_found=len(relevant_chunks),
                context_window=context_window,
                suggested_domains=self._suggest_domains(processed_query)
            )
            
            self._cache_result(processed_query, context, result)
            
            # Update metrics
            self.metrics['domain_distribution'][context.domain.value if context.domain else 'general'] += 1
            
            logger.info(f"RAG query processed in {result.execution_time_ms:.2f}ms, found {len(result.chunks)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Error in cognitive processing: {str(e)}", exc_info=True)
            return RAGResult(
                chunks=[],
                query=context.query,
                relevance_scores=[],
                execution_time_ms=self._calculate_elapsed_ms(start_time),
                total_chunks_found=0,
                context_window="",
                metadata={"error": str(e)}
            )
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess query for better retrieval"""
        # Remove special characters
        query = re.sub(r'[^\w\s]', ' ', query)
        
        # Convert to lowercase
        query = query.lower()
        
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Extract key terms (remove common stop words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are'}
        terms = [term for term in query.split() if term not in stop_words]
        
        return ' '.join(terms)
    
    def _check_cache(self, query: str, context: CognitiveContext) -> Optional[RAGResult]:
        """Check if query result is in cache"""
        cache_key = self._generate_cache_key(query, context)
        
        if cache_key in self.cache:
            chunk, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return chunk
            else:
                del self.cache[cache_key]
        
        return None
    
    def _cache_result(self, query: str, context: CognitiveContext, result: RAGResult):
        """Cache a query result"""
        cache_key = self._generate_cache_key(query, context)
        
        # Manage cache size
        if len(self.cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[cache_key] = (result, datetime.now())
    
    def _generate_cache_key(self, query: str, context: CognitiveContext) -> str:
        """Generate cache key from query and context"""
        key_data = f"{query}:{context.domain}:{context.difficulty.value}:{context.max_results}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def _retrieve_relevant_chunks(self, 
                                       query: str, 
                                       context: CognitiveContext) -> List[KnowledgeChunk]:
        """Retrieve relevant knowledge chunks using multiple strategies"""
        relevant_chunks = []
        
        # Strategy 1: Keyword matching
        keyword_chunks = self._keyword_retrieval(query)
        relevant_chunks.extend(keyword_chunks)
        
        # Strategy 2: Semantic search (simulated with keyword matching for now)
        # In production, this would use actual embeddings
        semantic_chunks = self._semantic_retrieval(query, context)
        relevant_chunks.extend(semantic_chunks)
        
        # Strategy 3: Graph-based retrieval using concept relationships
        graph_chunks = self._graph_retrieval(query)
        relevant_chunks.extend(graph_chunks)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_chunks = []
        for chunk in relevant_chunks:
            if chunk.id not in seen:
                seen.add(chunk.id)
                unique_chunks.append(chunk)
        
        return unique_chunks
    
    def _keyword_retrieval(self, query: str) -> List[KnowledgeChunk]:
        """Retrieve chunks based on keyword matching"""
        query_terms = set(query.lower().split())
        relevant_chunks = []
        
        for chunk in self.knowledge_base.values():
            chunk_terms = set(chunk.content.lower().split())
            # Check for overlap
            if query_terms & chunk_terms:
                relevant_chunks.append(chunk)
        
        return relevant_chunks
    
    def _semantic_retrieval(self, query: str, context: CognitiveContext) -> List[KnowledgeChunk]:
        """Retrieve chunks based on semantic similarity"""
        # Simplified semantic retrieval
        # In production, this would use embedding similarity
        relevant_chunks = []
        
        for chunk in self.knowledge_base.values():
            # Check domain match
            if context.domain and chunk.domain != context.domain:
                continue
            
            # Check difficulty level
            if chunk.difficulty.value > context.difficulty.value + 1:
                continue
            
            # Check for related concepts
            query_terms = set(query.lower().split())
            if any(concept in query for concept in chunk.related_concepts):
                relevant_chunks.append(chunk)
        
        return relevant_chunks
    
    def _graph_retrieval(self, query: str) -> List[KnowledgeChunk]:
        """Retrieve chunks using concept graph relationships"""
        query_terms = set(query.lower().split())
        relevant_chunks = []
        visited = set()
        
        # Find starting nodes
        start_nodes = []
        for term in query_terms:
            if term in self.concept_graph:
                start_nodes.append(term)
        
        # BFS to find related chunks
        for start in start_nodes:
            queue = [start]
            while queue and len(relevant_chunks) < 10:
                node = queue.pop(0)
                if node in visited:
                    continue
                visited.add(node)
                
                # Find chunks containing this concept
                for chunk in self.knowledge_base.values():
                    if node in chunk.content.lower() and chunk.id not in [c.id for c in relevant_chunks]:
                        relevant_chunks.append(chunk)
                    
                    # Add related concepts to queue
                    if node in self.concept_graph:
                        queue.extend(list(self.concept_graph[node]))
        
        return relevant_chunks
    
    def _score_chunks(self, 
                     chunks: List[KnowledgeChunk], 
                     query: str, 
                     context: CognitiveContext) -> List[Tuple[KnowledgeChunk, float]]:
        """Score chunks based on multiple relevance factors"""
        scored_chunks = []
        query_terms = set(query.lower().split())
        
        for chunk in chunks:
            score = 0.0
            
            # Keyword match score
            chunk_terms = set(chunk.content.lower().split())
            keyword_overlap = len(query_terms & chunk_terms)
            if keyword_overlap > 0:
                score += keyword_overlap * 0.3
            
            # Domain match score
            if context.domain and chunk.domain == context.domain:
                score += 0.2
            
            # Difficulty appropriateness
            difficulty_diff = abs(chunk.difficulty.value - context.difficulty.value)
            score += max(0, 0.2 - (difficulty_diff * 0.05))
            
            # Recency bonus
            days_old = (datetime.now() - chunk.timestamp).days
            if days_old < 30:
                score += 0.1
            elif days_old < 90:
                score += 0.05
            
            # Usage frequency bonus (popular content)
            if chunk.usage_count > 10:
                score += 0.1
            elif chunk.usage_count > 5:
                score += 0.05
            
            # Confidence score
            score *= chunk.confidence
            
            scored_chunks.append((chunk, score))
        
        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks
    
    def _select_top_chunks(self, 
                          scored_chunks: List[Tuple[KnowledgeChunk, float]], 
                          max_results: int) -> List[Tuple[KnowledgeChunk, float]]:
        """Select top chunks with diversity consideration"""
        if not scored_chunks:
            return []
        
        selected = []
        seen_domains = set()
        
        for chunk, score in scored_chunks:
            # Ensure domain diversity
            if chunk.domain not in seen_domains or len(selected) < max_results // 2:
                selected.append((chunk, score))
                seen_domains.add(chunk.domain)
            
            if len(selected) >= max_results:
                break
        
        return selected
    
    def _build_context_window(self, chunks: List[Tuple[KnowledgeChunk, float]]) -> str:
        """Build a coherent context window from selected chunks"""
        if not chunks:
            return ""
        
        # Combine chunks with separators
        context_parts = []
        for chunk, score in chunks:
            context_parts.append(f"[Source: {chunk.source}, Relevance: {score:.2f}]")
            context_parts.append(chunk.content)
            context_parts.append("---")
        
        return "\n".join(context_parts)
    
    def _suggest_domains(self, query: str) -> List[KnowledgeDomain]:
        """Suggest relevant domains based on query"""
        domain_keywords = {
            KnowledgeDomain.MATHEMATICS: ['math', 'calculus', 'algebra', 'geometry', 'equation'],
            KnowledgeDomain.PHYSICS: ['physics', 'force', 'energy', 'motion', 'quantum'],
            KnowledgeDomain.CHEMISTRY: ['chemistry', 'chemical', 'reaction', 'molecule', 'atom'],
            KnowledgeDomain.BIOLOGY: ['biology', 'cell', 'organism', 'evolution', 'dna'],
            KnowledgeDomain.COMPUTER_SCIENCE: ['computer', 'programming', 'algorithm', 'data', 'software'],
            KnowledgeDomain.ENGINEERING: ['engineering', 'design', 'system', 'mechanical', 'electrical']
        }
        
        suggested = []
        query_lower = query.lower()
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                suggested.append(domain)
        
        return suggested[:3]  # Return top 3 suggestions
    
    def _update_usage_stats(self, chunks: List[Tuple[KnowledgeChunk, float]]):
        """Update usage statistics for chunks"""
        for chunk, _ in chunks:
            chunk.usage_count += 1
            chunk.last_accessed = datetime.now()
    
    def _calculate_elapsed_ms(self, start_time: datetime) -> float:
        """Calculate elapsed time in milliseconds"""
        elapsed = datetime.now() - start_time
        return elapsed.total_seconds() * 1000
    
    def add_knowledge_chunk(self,
                           content: str,
                           domain: KnowledgeDomain,
                           difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
                           prerequisites: List[str] = None,
                           related_concepts: List[str] = None,
                           source: str = "",
                           confidence: float = 1.0) -> str:
        """Add a new knowledge chunk to the base"""
        chunk_id = hashlib.md5(f"{content}:{datetime.now()}".encode()).hexdigest()[:16]
        
        chunk = KnowledgeChunk(
            id=chunk_id,
            content=content,
            domain=domain,
            difficulty=difficulty,
            prerequisites=prerequisites or [],
            related_concepts=related_concepts or [],
            source=source,
            confidence=confidence
        )
        
        self.knowledge_base[chunk_id] = chunk
        self.domain_index[domain].append(chunk_id)
        
        # Update concept graph
        for concept in related_concepts or []:
            self.concept_graph[concept.lower()].add(concept.lower())
            # Add bidirectional relationships
            for other in related_concepts or []:
                if other != concept:
                    self.concept_graph[concept.lower()].add(other.lower())
        
        logger.info(f"Added knowledge chunk {chunk_id} to {domain.value} domain")
        return chunk_id
    
    def get_learning_path(self, 
                         target_concept: str,
                         current_level: DifficultyLevel) -> List[KnowledgeChunk]:
        """Generate a learning path for a target concept"""
        path = []
        
        # Find chunks related to target concept
        relevant_chunks = []
        for chunk in self.knowledge_base.values():
            if target_concept.lower() in chunk.content.lower() or \
               any(target_concept.lower() in concept.lower() for concept in chunk.related_concepts):
                relevant_chunks.append(chunk)
        
        # Sort by difficulty
        relevant_chunks.sort(key=lambda x: x.difficulty.value)
        
        # Filter based on current level
        path = [chunk for chunk in relevant_chunks 
                if chunk.difficulty.value >= current_level.value]
        
        return path[:10]  # Return top 10 chunks
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        total_chunks = len(self.knowledge_base)
        total_cache_hits = self.metrics['cache_hits']
        total_queries = self.metrics['total_queries']
        
        cache_hit_rate = total_cache_hits / total_queries if total_queries > 0 else 0
        
        return {
            "total_knowledge_chunks": total_chunks,
            "total_queries": total_queries,
            "cache_hit_rate": cache_hit_rate,
            "domain_distribution": dict(self.metrics['domain_distribution']),
            "cache_size": len(self.cache),
            "concept_graph_size": len(self.concept_graph)
        }