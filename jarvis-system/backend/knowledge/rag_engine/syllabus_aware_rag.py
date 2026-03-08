"""
Syllabus-aware RAG engine with contextual retrieval and intelligent filtering
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
import numpy as np
from collections import defaultdict

from .document_processor import DocumentProcessor
from .embedding_manager import EmbeddingManager
from .query_enhancer import QueryEnhancer, EnhancedQuery
from ..syllabus.syllabus_parser import SyllabusParser
from ..syllabus.topic_extractor import TopicExtractor
from ..syllabus.difficulty_mapper import DifficultyMapper

@dataclass
class RetrievalResult:
    """Represents a retrieval result with metadata"""
    text: str
    chunk_id: str
    document_id: str
    score: float
    topic: Optional[str] = None
    difficulty: float = 0.5
    estimated_time: int = 5  # minutes
    prerequisites: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class SyllabusAwareRAG:
    """
    Advanced RAG engine with syllabus awareness, contextual retrieval,
    and intelligent result filtering
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize syllabus-aware RAG engine
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Initialize components
        self.document_processor = DocumentProcessor(self.config.get('document_processor', {}))
        self.embedding_manager = EmbeddingManager(self.config.get('embedding_manager', {}))
        self.query_enhancer = QueryEnhancer(self.config.get('query_enhancer', {}))
        
        # Syllabus components
        self.syllabus_parser = SyllabusParser(self.config.get('syllabus_parser', {}))
        self.topic_extractor = TopicExtractor(self.config.get('topic_extractor', {}))
        self.difficulty_mapper = DifficultyMapper(self.config.get('difficulty_mapper', {}))
        
        # Storage
        self.documents = {}  # document_id -> document
        self.chunks = {}  # chunk_id -> chunk
        self.topic_index = defaultdict(list)  # topic -> list of chunk_ids
        self.difficulty_index = defaultdict(list)  # difficulty_level -> chunk_ids
        
        # Syllabus data
        self.current_syllabus = None
        self.topic_hierarchy = {}
        self.prerequisite_graph = {}
        
        # Retrieval settings
        self.max_context_length = self.config.get('max_context_length', 4000)
        self.default_chunks_to_retrieve = self.config.get('default_chunks_to_retrieve', 5)
        self.relevance_threshold = self.config.get('relevance_threshold', 0.6)
        
        self.logger = logging.getLogger(__name__)
    
    async def retrieve_context(
        self,
        query: str,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[str, List[RetrievalResult]]:
        """
        Retrieve relevant context for query with syllabus awareness
        
        Args:
            query: User query
            subject: Subject context
            topic: Specific topic
            difficulty_level: Desired difficulty level
            user_context: User context (history, performance, etc.)
            **kwargs: Additional arguments
            
        Returns:
            Tuple of (context_string, retrieval_results)
        """
        # 1. Enhance query
        enhanced_query = self.query_enhancer.enhance_query(
            query,
            subject=subject,
            context=user_context
        )
        
        # 2. Get query embedding
        query_embedding = self.embedding_manager.get_embeddings(
            enhanced_query.expanded + [enhanced_query.original],
            use_cache=True
        )
        
        # 3. Determine search scope based on syllabus
        search_scope = self._determine_search_scope(
            subject,
            topic,
            enhanced_query.domain,
            user_context
        )
        
        # 4. Perform multi-strategy retrieval
        retrieval_results = await self._multi_strategy_retrieval(
            query=query,
            enhanced_query=enhanced_query,
            query_embedding=query_embedding,
            search_scope=search_scope,
            subject=subject,
            **kwargs
        )
        
        # 5. Apply syllabus-aware filtering
        filtered_results = self._syllabus_filtering(
            retrieval_results,
            subject=subject,
            topic=topic,
            difficulty_level=difficulty_level,
            user_context=user_context
        )
        
        # 6. Rerank results
        reranked_results = self._rerank_results(
            filtered_results,
            enhanced_query,
            user_context
        )
        
        # 7. Format context
        context_string = self._format_context(
            reranked_results,
            enhanced_query,
            max_length=self.max_context_length
        )
        
        return context_string, reranked_results
    
    async def _multi_strategy_retrieval(
        self,
        query: str,
        enhanced_query: EnhancedQuery,
        query_embedding: np.ndarray,
        search_scope: Dict[str, Any],
        subject: Optional[str] = None,
        **kwargs
    ) -> List[RetrievalResult]:
        """
        Perform retrieval using multiple strategies
        """
        all_results = []
        
        # Strategy 1: Dense retrieval (semantic search)
        if self.embedding_manager.vector_store:
            dense_results = self._dense_retrieval(
                query_embedding,
                k=kwargs.get('dense_k', 10),
                index_name=subject or 'default'
            )
            all_results.extend(dense_results)
        
        # Strategy 2: Keyword-based retrieval
        keyword_results = self._keyword_retrieval(
            enhanced_query.keywords,
            k=kwargs.get('keyword_k', 5)
        )
        all_results.extend(keyword_results)
        
        # Strategy 3: Syllabus-aware retrieval
        if search_scope.get('topics'):
            syllabus_results = await self._syllabus_aware_retrieval(
                query,
                enhanced_query,
                search_scope['topics'],
                k=kwargs.get('syllabus_k', 5)
            )
            all_results.extend(syllabus_results)
        
        # Strategy 4: Contextual retrieval based on user history
        if search_scope.get('user_history'):
            contextual_results = self._contextual_retrieval(
                query_embedding,
                search_scope['user_history'],
                k=kwargs.get('contextual_k', 3)
            )
            all_results.extend(contextual_results)
        
        # Remove duplicates (by chunk_id)
        seen = set()
        unique_results = []
        for result in all_results:
            if result.chunk_id not in seen:
                seen.add(result.chunk_id)
                unique_results.append(result)
        
        return unique_results
    
    def _dense_retrieval(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        index_name: str = 'default'
    ) -> List[RetrievalResult]:
        """Dense retrieval using vector similarity"""
        results = []
        
        try:
            # Use multiple query embeddings (original + expansions)
            if query_embedding.ndim == 2:
                # Average the embeddings
                query_emb = np.mean(query_embedding, axis=0)
            else:
                query_emb = query_embedding
            
            # Perform search
            similar_items, scores = self.embedding_manager.similarity_search(
                query_emb,
                k=k,
                index_name=index_name,
                return_scores=True
            )
            
            # Convert to RetrievalResult objects
            for item, score in zip(similar_items, scores):
                if score >= self.relevance_threshold:
                    chunk = self.chunks.get(item.get('chunk_id'))
                    if chunk:
                        results.append(RetrievalResult(
                            text=chunk.text,
                            chunk_id=chunk.chunk_id,
                            document_id=item.get('document_id', ''),
                            score=float(score),
                            topic=item.get('topic'),
                            difficulty=item.get('difficulty', 0.5),
                            estimated_time=item.get('estimated_time', 5),
                            prerequisites=item.get('prerequisites', []),
                            metadata=item
                        ))
        except Exception as e:
            self.logger.error(f"Error in dense retrieval: {e}")
        
        return results
    
    def _keyword_retrieval(
        self,
        keywords: List[str],
        k: int = 5
    ) -> List[RetrievalResult]:
        """Keyword-based retrieval using BM25 or similar"""
        results = []
        
        # Simple keyword matching
        keyword_matches = defaultdict(float)
        
        for chunk_id, chunk in self.chunks.items():
            chunk_text_lower = chunk.text.lower()
            score = 0
            
            for keyword in keywords:
                if keyword.lower() in chunk_text_lower:
                    # Weight by keyword importance
                    score += 1.0 / (len(keywords) * (keywords.index(keyword) + 1))
            
            if score > 0:
                keyword_matches[chunk_id] = score
        
        # Sort by score
        sorted_matches = sorted(
            keyword_matches.items(),
            key=lambda x: x[1],
            reverse=True
        )[:k]
        
        for chunk_id, score in sorted_matches:
            chunk = self.chunks[chunk_id]
            results.append(RetrievalResult(
                text=chunk.text,
                chunk_id=chunk_id,
                document_id=chunk.metadata.get('document_id', ''),
                score=score,
                topic=chunk.metadata.get('topic'),
                difficulty=chunk.metadata.get('difficulty', 0.5),
                estimated_time=chunk.metadata.get('estimated_time', 5),
                prerequisites=chunk.metadata.get('prerequisites', []),
                metadata=chunk.metadata
            ))
        
        return results
    
    async def _syllabus_aware_retrieval(
        self,
        query: str,
        enhanced_query: EnhancedQuery,
        topics: List[str],
        k: int = 5
    ) -> List[RetrievalResult]:
        """Retrieve content specific to syllabus topics"""
        results = []
        
        for topic in topics:
            # Get chunks for this topic
            topic_chunks = self.topic_index.get(topic, [])
            
            if topic_chunks:
                # Get embeddings for topic chunks
                chunk_texts = [self.chunks[chunk_id].text for chunk_id in topic_chunks]
                
                if chunk_texts:
                    # Compute similarity with query
                    chunk_embeddings = self.embedding_manager.get_embeddings(
                        chunk_texts,
                        use_cache=True
                    )
                    
                    query_emb = self.embedding_manager.get_embeddings(query)
                    
                    # Calculate similarities
                    similarities = np.dot(chunk_embeddings, query_emb) / (
                        np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(query_emb)
                    )
                    
                    # Get top-k for this topic
                    top_indices = np.argsort(similarities)[-min(k, len(chunk_texts)):][::-1]
                    
                    for idx in top_indices:
                        chunk_id = topic_chunks[idx]
                        chunk = self.chunks[chunk_id]
                        score = float(similarities[idx])
                        
                        if score >= self.relevance_threshold:
                            results.append(RetrievalResult(
                                text=chunk.text,
                                chunk_id=chunk_id,
                                document_id=chunk.metadata.get('document_id', ''),
                                score=score,
                                topic=topic,
                                difficulty=chunk.metadata.get('difficulty', 0.5),
                                estimated_time=chunk.metadata.get('estimated_time', 5),
                                prerequisites=chunk.metadata.get('prerequisites', []),
                                metadata=chunk.metadata
                            ))
        
        # Sort by score and return top-k overall
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]
    
    def _contextual_retrieval(
        self,
        query_embedding: np.ndarray,
        user_history: List[str],
        k: int = 3
    ) -> List[RetrievalResult]:
        """Retrieve based on user's historical context"""
        results = []
        
        if user_history:
            # Get embeddings for user's historical content
            history_embeddings = self.embedding_manager.get_embeddings(
                user_history,
                use_cache=True
            )
            
            # Average history embeddings
            avg_history_emb = np.mean(history_embeddings, axis=0)
            
            # Combine with query embedding (weighted)
            combined_emb = 0.7 * query_embedding + 0.3 * avg_history_emb
            
            # Perform search with combined embedding
            similar_items, scores = self.embedding_manager.similarity_search(
                combined_emb,
                k=k,
                return_scores=True
            )
            
            for item, score in zip(similar_items, scores):
                chunk = self.chunks.get(item.get('chunk_id'))
                if chunk:
                    results.append(RetrievalResult(
                        text=chunk.text,
                        chunk_id=chunk.chunk_id,
                        document_id=item.get('document_id', ''),
                        score=float(score),
                        topic=item.get('topic'),
                        difficulty=item.get('difficulty', 0.5),
                        estimated_time=item.get('estimated_time', 5),
                        prerequisites=item.get('prerequisites', []),
                        metadata={**item, 'contextual': True}
                    ))
        
        return results
    
    def _syllabus_filtering(
        self,
        results: List[RetrievalResult],
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Apply syllabus-aware filtering to retrieval results"""
        filtered = []
        
        # Get user's current position in syllabus
        current_position = None
        if user_context:
            current_position = user_context.get('current_topic')
        
        for result in results:
            # Filter by subject
            if subject and result.metadata.get('subject') != subject:
                continue
            
            # Filter by topic
            if topic and result.topic != topic:
                # Check if topic is related (subtopic)
                if not self._is_related_topic(result.topic, topic):
                    continue
            
            # Filter by difficulty
            if difficulty_level:
                result_difficulty = self.difficulty_mapper.get_level(result.difficulty)
                if result_difficulty != difficulty_level:
                    continue
            
            # Check prerequisites
            if current_position and result.prerequisites:
                if not self._prerequisites_met(result.prerequisites, current_position):
                    # Still include but mark as advanced
                    result.metadata['prerequisites_missing'] = True
            
            filtered.append(result)
        
        return filtered
    
    def _rerank_results(
        self,
        results: List[RetrievalResult],
        enhanced_query: EnhancedQuery,
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Rerank results based on multiple factors"""
        
        for result in results:
            # Base score from retrieval
            final_score = result.score
            
            # Factor 1: Query intent match
            if enhanced_query.intent == QueryIntent.DEFINITIONAL:
                # Prefer chunks with definitions
                if 'definition' in result.text.lower() or 'is defined as' in result.text.lower():
                    final_score *= 1.2
            
            elif enhanced_query.intent == QueryIntent.PROCEDURAL:
                # Prefer chunks with steps or procedures
                if any(word in result.text.lower() for word in ['step', 'first', 'then', 'finally']):
                    final_score *= 1.2
            
            # Factor 2: Difficulty match with user level
            if user_context and 'user_level' in user_context:
                user_level = user_context['user_level']
                difficulty_diff = abs(result.difficulty - user_level)
                if difficulty_diff < 0.2:
                    final_score *= 1.1
                elif difficulty_diff > 0.5:
                    final_score *= 0.9
            
            # Factor 3: Recency (if available)
            if 'timestamp' in result.metadata:
                age = datetime.now() - datetime.fromisoformat(result.metadata['timestamp'])
                if age.days < 30:  # Recent content
                    final_score *= 1.05
            
            # Factor 4: Authority (if available)
            if 'source_authority' in result.metadata:
                final_score *= (1 + result.metadata['source_authority'] * 0.1)
            
            result.score = final_score
        
        # Sort by final score
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def _format_context(
        self,
        results: List[RetrievalResult],
        enhanced_query: EnhancedQuery,
        max_length: int = 4000
    ) -> str:
        """Format retrieval results into context string"""
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for i, result in enumerate(results, 1):
            # Add header
            header = f"[{i}] "
            if result.topic:
                header += f"Topic: {result.topic} "
            if result.difficulty:
                header += f"(Difficulty: {result.difficulty:.2f})"
            header += "\n"
            
            # Add content
            content = result.text.strip()
            
            # Add metadata
            if result.estimated_time:
                content += f"\n[Estimated reading time: {result.estimated_time} minutes]"
            
            # Check length
            entry = f"{header}{content}\n\n"
            entry_length = len(entry)
            
            if current_length + entry_length <= max_length:
                context_parts.append(entry)
                current_length += entry_length
            else:
                # Truncate if necessary
                remaining = max_length - current_length
                if remaining > 100:  # Only add if we can include meaningful content
                    truncated = content[:remaining-50] + "..."
                    entry = f"{header}{truncated}\n\n"
                    context_parts.append(entry)
                break
        
        return "".join(context_parts)
    
    def _determine_search_scope(
        self,
        subject: Optional[str],
        topic: Optional[str],
        domain: str,
        user_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Determine the scope for searching"""
        scope = {
            'subjects': [subject] if subject else [],
            'topics': [],
            'domains': [domain],
            'user_history': []
        }
        
        # Add topic if specified
        if topic:
            scope['topics'].append(topic)
            
            # Add related topics from syllabus
            if self.topic_hierarchy:
                related = self._get_related_topics(topic)
                scope['topics'].extend(related[:3])  # Limit to 3 related topics
        
        # Add topics from user history
        if user_context and 'viewed_topics' in user_context:
            scope['user_history'] = user_context['viewed_topics'][-5:]  # Last 5 topics
        
        return scope
    
    def _get_related_topics(self, topic: str) -> List[str]:
        """Get related topics from syllabus hierarchy"""
        related = []
        
        if topic in self.topic_hierarchy:
            # Get siblings
            for parent, children in self.topic_hierarchy.items():
                if topic in children:
                    related.extend([c for c in children if c != topic])
                    break
            
            # Get parent
            for parent, children in self.topic_hierarchy.items():
                if topic in children:
                    related.append(parent)
                    break
        
        return related
    
    def _is_related_topic(self, topic1: Optional[str], topic2: str) -> bool:
        """Check if two topics are related"""
        if not topic1:
            return False
        
        if topic1 == topic2:
            return True
        
        # Check hierarchy
        if topic1 in self.topic_hierarchy.get(topic2, []):
            return True
        
        if topic2 in self.topic_hierarchy.get(topic1, []):
            return True
        
        return False
    
    def _prerequisites_met(
        self,
        prerequisites: List[str],
        current_position: str
    ) -> bool:
        """Check if prerequisites are met based on current position"""
        # Simple implementation - in production, use prerequisite graph
        return all(p in current_position for p in prerequisites)
    
    async def index_document(
        self,
        document_path: str,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        **kwargs
    ) -> str:
        """Index a document into the RAG system"""
        # Process document
        processed = self.document_processor.process_document(
            document_path,
            **kwargs
        )
        
        document_id = processed['document_id']
        self.documents[document_id] = processed
        
        # Extract topics if not provided
        if not topic and processed['metadata'].get('topics'):
            topics = processed['metadata']['topics']
        elif topic:
            topics = [topic]
        else:
            # Extract topics from content
            topics = self.topic_extractor.extract_topics(
                processed['processed_text']
            )
        
        # Get difficulty estimates
        difficulties = self.difficulty_mapper.estimate_difficulty(
            processed['processed_text'],
            topics
        )
        
        # Process chunks
        chunk_texts = []
        chunk_metadata = []
        
        for chunk in processed['chunks']:
            chunk_id = chunk.chunk_id
            self.chunks[chunk_id] = chunk
            
            # Add topic and difficulty to metadata
            chunk_topic = self._assign_topic(chunk.text, topics)
            chunk_difficulty = difficulties.get(chunk_topic, 0.5)
            
            chunk.metadata.update({
                'document_id': document_id,
                'subject': subject,
                'topic': chunk_topic,
                'difficulty': chunk_difficulty,
                'timestamp': datetime.now().isoformat()
            })
            
            # Update indices
            if chunk_topic:
                self.topic_index[chunk_topic].append(chunk_id)
            
            difficulty_level = self.difficulty_mapper.get_level(chunk_difficulty)
            self.difficulty_index[difficulty_level].append(chunk_id)
            
            # Prepare for embedding
            chunk_texts.append(chunk.text)
            chunk_metadata.append(chunk.metadata)
        
        # Generate embeddings
        embeddings = self.embedding_manager.get_embeddings(
            chunk_texts,
            use_cache=True
        )
        
        # Build/update vector store
        if self.embedding_manager.vector_store is None:
            self.embedding_manager.build_vector_store(
                embeddings,
                chunk_metadata,
                index_name=subject or 'default'
            )
        else:
            # Add to existing store (simplified - in production, handle incremental updates)
            pass
        
        self.logger.info(f"Indexed document {document_id} with {len(chunk_texts)} chunks")
        return document_id
    
    def _assign_topic(self, text: str, topics: List[str]) -> Optional[str]:
        """Assign the most relevant topic to a chunk"""
        if not topics:
            return None
        
        # Simple keyword matching
        text_lower = text.lower()
        topic_scores = {}
        
        for topic in topics:
            score = text_lower.count(topic.lower())
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores.items(), key=lambda x: x[1])[0]
        
        return topics[0]  # Default to first topic
    
    async def load_syllabus(self, syllabus_path: str):
        """Load syllabus data"""
        self.current_syllabus = await self.syllabus_parser.parse(syllabus_path)
        self.topic_hierarchy = self.current_syllabus.get('topic_hierarchy', {})
        self.prerequisite_graph = self.current_syllabus.get('prerequisites', {})
        
        self.logger.info(f"Loaded syllabus with {len(self.topic_hierarchy)} topics")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG system"""
        return {
            'documents': len(self.documents),
            'chunks': len(self.chunks),
            'topics': len(self.topic_index),
            'vector_store_size': len(self.embedding_manager.vector_store_index) if self.embeddingManager.vector_store_index else 0,
            'cache_size': len(self.embedding_manager.embedding_cache),
            'syllabus_loaded': self.current_syllabus is not None
        }