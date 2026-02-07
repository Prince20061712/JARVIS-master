from typing import List, Dict, Any, Optional
import numpy as np
import pickle
from sqlalchemy import desc

from core.memory.db import get_db, init_db
from core.memory.models import Conversation, Fact
from core.memory.embeddings import EmbeddingService

class LongTermMemory:
    def __init__(self):
        init_db()
        self.encoder = EmbeddingService()

    def store_conversation(self, role: str, content: str, metadata: Dict = None):
        """Stores a conversation turn."""
        embedding = self.encoder.encode(content)
        
        db = next(get_db())
        try:
            record = Conversation(
                role=role,
                content=content,
                embedding=embedding,
                metadata_=metadata or {}
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

    def store_fact(self, topic: str, content: str, confidence: float = 1.0):
        """Stores a fact."""
        embedding = self.encoder.encode(content)
        
        db = next(get_db())
        try:
            record = Fact(
                topic=topic,
                content=content,
                confidence=confidence,
                embedding=embedding
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

    def search_similar(self, query: str, limit: int = 5, threshold: float = 0.5) -> List[Dict]:
        """
        Semantic search for conversations/facts.
        """
        query_vec = self.encoder.encode(query)
        
        db = next(get_db())
        results = []
        try:
            # 1. Search Conversations
            conversations = db.query(Conversation).order_by(desc(Conversation.timestamp)).limit(50).all()
            for item in conversations:
                if item.embedding is None: continue
                # Handle binary pickle if needed (TypeDecorator usually handles it)
                vec = pickle.loads(item.embedding) if isinstance(item.embedding, bytes) else item.embedding
                
                sim = self._cosine_similarity(query_vec, vec)
                if sim >= threshold:
                    results.append({
                        "id": item.id,
                        "content": item.content,
                        "score": sim,
                        "type": "conversation",
                        "metadata": item.metadata_
                    })

            # 2. Search Facts
            facts = db.query(Fact).all()
            for item in facts:
                if item.embedding is None: continue
                vec = pickle.loads(item.embedding) if isinstance(item.embedding, bytes) else item.embedding
                
                sim = self._cosine_similarity(query_vec, vec)
                if sim >= threshold:
                    results.append({
                        "id": item.id,
                        "content": item.content,
                        "score": sim,
                        "type": "fact",
                        "metadata": {"topic": item.topic}
                    })
            
            # Sort by score
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:limit]
        finally:
            db.close()

    def _cosine_similarity(self, vec_a, vec_b):
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return np.dot(vec_a, vec_b) / (norm_a * norm_b)
