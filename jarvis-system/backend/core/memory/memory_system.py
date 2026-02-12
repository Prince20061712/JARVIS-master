#!/usr/bin/env python3
"""
Enhanced Memory System Module
Handles conversation memory with semantic search, embeddings, and advanced recall
"""

import json
import datetime
import hashlib
import pickle
import numpy as np
from collections import deque, defaultdict
from typing import Dict, List, Optional, Tuple, Any
import os
from dataclasses import dataclass
import re
from enum import Enum
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

class MemoryType(Enum):
    CONVERSATION = "conversation"
    FACT = "fact"
    PREFERENCE = "preference"
    TASK = "task"
    EVENT = "event"
    RELATIONSHIP = "relationship"
    SKILL = "skill"

class MemoryPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class MemoryEntry:
    id: str
    content: str
    memory_type: MemoryType
    priority: MemoryPriority
    timestamp: str
    embeddings: Optional[np.ndarray] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    related_memories: Optional[List[str]] = None
    access_count: int = 0
    last_accessed: Optional[str] = None
    decay_factor: float = 0.95

class EnhancedMemorySystem:
    def __init__(self, memory_dir="memory_data", max_memories=10000):
        self.memory_dir = memory_dir
        os.makedirs(memory_dir, exist_ok=True)
        
        # Memory storage files
        self.memory_file = os.path.join(memory_dir, "memories.pkl")
        self.index_file = os.path.join(memory_dir, "memory_index.json")
        self.embeddings_file = os.path.join(memory_dir, "embeddings.npy")
        self.vectorizer_file = os.path.join(memory_dir, "vectorizer.pkl")
        
        # Initialize memory structures
        self.memories: Dict[str, MemoryEntry] = {}  # id -> MemoryEntry
        self.memory_index = defaultdict(list)  # tag -> memory_ids
        self.conversation_flow = deque(maxlen=1000)
        self.user_profiles = defaultdict(dict)
        self.vectorizer = None
        self.embeddings_matrix = None
        
        # Memory configuration
        self.max_memories = max_memories
        self.memory_decay_rate = 0.001
        self.consolidation_threshold = 100
        
        # Statistics
        self.stats = {
            "total_memories": 0,
            "memories_by_type": defaultdict(int),
            "total_recalls": 0,
            "successful_recalls": 0,
            "failed_recalls": 0,
            "memory_decays": 0,
            "consolidations": 0
        }
        
        # Load existing memory
        self.load_memory()
        self.initialize_nlp()
    
    def initialize_nlp(self):
        """Initialize NLP components for semantic search"""
        try:
            if os.path.exists(self.vectorizer_file):
                with open(self.vectorizer_file, 'rb') as f:
                    self.vectorizer = pickle.load(f)
        except:
            pass
        
        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 3),
                max_features=5000
            )
    
    def load_memory(self):
        """Load all memory data"""
        try:
            # Load memory entries
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'rb') as f:
                    memory_data = pickle.load(f)
                    self.memories = memory_data.get('memories', {})
                    self.memory_index = defaultdict(list, memory_data.get('index', {}))
                    self.stats = memory_data.get('stats', self.stats)
            
            # Load conversation flow
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r') as f:
                    index_data = json.load(f)
                    self.conversation_flow = deque(
                        index_data.get('conversation_flow', []),
                        maxlen=1000
                    )
                    self.user_profiles = defaultdict(dict, index_data.get('user_profiles', {}))
            
            # Load embeddings if they exist
            if os.path.exists(self.embeddings_file):
                self.embeddings_matrix = np.load(self.embeddings_file)
        except Exception as e:
            print(f"Error loading memory: {e}")
    
    def save_memory(self):
        """Save all memory data"""
        try:
            # Save memory entries
            memory_data = {
                'memories': self.memories,
                'index': dict(self.memory_index),
                'stats': self.stats,
                'last_saved': datetime.datetime.now().isoformat()
            }
            with open(self.memory_file, 'wb') as f:
                pickle.dump(memory_data, f)
            
            # Save index and conversation flow
            index_data = {
                'conversation_flow': list(self.conversation_flow),
                'user_profiles': dict(self.user_profiles),
                'last_updated': datetime.datetime.now().isoformat()
            }
            with open(self.index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
            
            # Save vectorizer if trained
            if hasattr(self.vectorizer, 'vocabulary_'):
                with open(self.vectorizer_file, 'wb') as f:
                    pickle.dump(self.vectorizer, f)
        except Exception as e:
            print(f"Error saving memory: {e}")
    
    def create_memory(self, content: str, memory_type: MemoryType = MemoryType.CONVERSATION,
                     priority: MemoryPriority = MemoryPriority.MEDIUM,
                     metadata: Dict = None, tags: List[str] = None) -> str:
        """Create a new memory entry"""
        # Generate unique ID
        memory_id = hashlib.sha256(
            f"{content}{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Extract tags if not provided
        if tags is None:
            tags = self._extract_tags(content)
        
        # Generate embeddings
        embeddings = self._generate_embeddings(content)
        
        # Create memory entry
        memory = MemoryEntry(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            priority=priority,
            timestamp=datetime.datetime.now().isoformat(),
            embeddings=embeddings,
            metadata=metadata or {},
            tags=tags,
            related_memories=[],
            access_count=0,
            decay_factor=self._calculate_decay_factor(priority)
        )
        
        # Store memory
        self.memories[memory_id] = memory
        
        # Update index
        for tag in tags:
            self.memory_index[tag].append(memory_id)
        
        # Update statistics
        self.stats["total_memories"] += 1
        self.stats["memories_by_type"][memory_type.value] += 1
        
        # Check if consolidation needed
        if self.stats["total_memories"] % self.consolidation_threshold == 0:
            self._consolidate_memories()
        
        self.save_memory()
        return memory_id
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract semantic tags from text"""
        text_lower = text.lower()
        tags = []
        
        # Semantic categories
        categories = {
            "greeting": ["hello", "hi", "hey", "good morning", "good afternoon"],
            "question": ["what", "who", "where", "when", "why", "how"],
            "command": ["play", "open", "close", "search", "find", "get"],
            "emotion": ["happy", "sad", "angry", "excited", "tired", "bored"],
            "topic_tech": ["computer", "program", "code", "ai", "machine learning"],
            "topic_science": ["science", "physics", "chemistry", "biology"],
            "topic_news": ["news", "current", "recent", "today"],
            "personal": ["i", "me", "my", "mine", "personally"],
            "urgent": ["urgent", "important", "critical", "asap", "now"],
            "future": ["tomorrow", "later", "next week", "future", "plan"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(category)
        
        # Extract named entities (simplified)
        named_entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        for entity in named_entities[:3]:  # Limit to top 3
            if len(entity.split()) <= 3:  # Avoid long phrases
                tags.append(f"entity:{entity.lower()}")
        
        # Extract key phrases using TF-IDF
        if hasattr(self.vectorizer, 'vocabulary_'):
            try:
                vector = self.vectorizer.transform([text_lower])
                feature_names = self.vectorizer.get_feature_names_out()
                scores = vector.toarray()[0]
                top_indices = scores.argsort()[-3:][::-1]
                for idx in top_indices:
                    if scores[idx] > 0:
                        tags.append(f"keyphrase:{feature_names[idx]}")
            except:
                pass
        
        return list(set(tags))  # Remove duplicates
    
    def _generate_embeddings(self, text: str) -> Optional[np.ndarray]:
        """Generate embeddings for text (simplified - use sentence transformers in production)"""
        try:
            # Simple TF-IDF based embeddings
            if not hasattr(self.vectorizer, 'vocabulary_'):
                # Fit on existing content
                all_texts = [text] + [m.content for m in self.memories.values()][-100:]
                self.vectorizer.fit(all_texts)
            
            vector = self.vectorizer.transform([text]).toarray()[0]
            return vector
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return None
    
    def _calculate_decay_factor(self, priority: MemoryPriority) -> float:
        """Calculate memory decay factor based on priority"""
        decay_factors = {
            MemoryPriority.CRITICAL: 0.99,  # Decays very slowly
            MemoryPriority.HIGH: 0.95,
            MemoryPriority.MEDIUM: 0.90,
            MemoryPriority.LOW: 0.85  # Decays faster
        }
        return decay_factors.get(priority, 0.90)
    
    def remember_conversation(self, user_input: str, bot_response: str,
                            user_id: str = "default", importance: int = 0) -> str:
        """Store a conversation in memory with enhanced features"""
        # Create combined content
        conversation_content = f"User: {user_input}\nAssistant: {bot_response}"
        
        # Determine priority based on importance and content analysis
        priority = self._determine_conversation_priority(user_input, bot_response, importance)
        
        # Extract metadata
        metadata = {
            "user_id": user_id,
            "importance_score": importance,
            "input_length": len(user_input),
            "response_length": len(bot_response),
            "has_question": "?" in user_input,
            "has_command": any(cmd in user_input.lower() for cmd in ["play", "open", "close", "search"])
        }
        
        # Create memory
        memory_id = self.create_memory(
            content=conversation_content,
            memory_type=MemoryType.CONVERSATION,
            priority=priority,
            metadata=metadata,
            tags=self._extract_conversation_tags(user_input, bot_response)
        )
        
        # Add to conversation flow
        self.conversation_flow.append({
            "memory_id": memory_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "user_id": user_id,
            "user_input_preview": user_input[:50]
        })
        
        # Update user profile
        self._update_user_conversation_history(user_id, memory_id, user_input)
        
        return memory_id
    
    def _determine_conversation_priority(self, user_input: str, bot_response: str,
                                       importance: int) -> MemoryPriority:
        """Determine priority of a conversation memory"""
        priority_score = importance
        
        # Content-based priority boosting
        priority_indicators = {
            "important": 2,
            "remember": 2,
            "don't forget": 2,
            "crucial": 3,
            "critical": 3,
            "urgent": 3,
            "password": 3,
            "secret": 3,
            "personal": 1
        }
        
        combined_text = (user_input + " " + bot_response).lower()
        for indicator, boost in priority_indicators.items():
            if indicator in combined_text:
                priority_score += boost
        
        # Length-based priority (longer conversations might be more important)
        if len(user_input) > 100 or len(bot_response) > 100:
            priority_score += 1
        
        # Determine priority level
        if priority_score >= 5:
            return MemoryPriority.CRITICAL
        elif priority_score >= 3:
            return MemoryPriority.HIGH
        elif priority_score >= 1:
            return MemoryPriority.MEDIUM
        else:
            return MemoryPriority.LOW
    
    def _extract_conversation_tags(self, user_input: str, bot_response: str) -> List[str]:
        """Extract conversation-specific tags"""
        tags = []
        combined = user_input.lower() + " " + bot_response.lower()
        
        # Add conversation-specific tags
        if "?" in user_input:
            tags.append("contains_question")
        
        if any(word in combined for word in ["thank", "thanks", "appreciate"]):
            tags.append("gratitude")
        
        if any(word in combined for word in ["sorry", "apologize", "forgive"]):
            tags.append("apology")
        
        if len(bot_response.split()) > 50:
            tags.append("detailed_response")
        
        # Add emotional tags
        emotions = {
            "positive": ["happy", "great", "wonderful", "excellent", "good"],
            "negative": ["sad", "bad", "terrible", "awful", "unhappy"],
            "neutral": ["okay", "fine", "alright", "neutral"]
        }
        
        for emotion, keywords in emotions.items():
            if any(keyword in combined for keyword in keywords):
                tags.append(f"emotion_{emotion}")
                break
        
        return tags
    
    def _update_user_conversation_history(self, user_id: str, memory_id: str, user_input: str):
        """Update user's conversation history"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "total_conversations": 0,
                "conversation_history": [],
                "preferred_topics": defaultdict(int),
                "conversation_patterns": defaultdict(int),
                "last_interaction": None
            }
        
        profile = self.user_profiles[user_id]
        profile["total_conversations"] += 1
        profile["last_interaction"] = datetime.datetime.now().isoformat()
        
        # Add to history (limit to 100)
        profile["conversation_history"].append({
            "memory_id": memory_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "preview": user_input[:30]
        })
        if len(profile["conversation_history"]) > 100:
            profile["conversation_history"].pop(0)
        
        # Update topics
        tags = self._extract_tags(user_input)
        for tag in tags:
            if "topic_" in tag or "entity:" in tag:
                profile["preferred_topics"][tag] += 1
        
        # Update conversation patterns
        if "?" in user_input:
            profile["conversation_patterns"]["asks_questions"] += 1
        if len(user_input.split()) > 20:
            profile["conversation_patterns"]["detailed_queries"] += 1
    
    def recall_memories(self, query: str = "", memory_type: str = None,
                       limit: int = 5, similarity_threshold: float = 0.3,
                       user_id: str = None) -> List[Dict]:
        """Recall memories with semantic search"""
        self.stats["total_recalls"] += 1
        
        if not query and not memory_type:
            # Return recent memories
            recent_memories = list(self.memories.values())[-limit:]
            self._update_access_stats(recent_memories)
            return self._format_memories(recent_memories)
        
        # Filter by memory type if specified
        candidate_memories = []
        for memory in self.memories.values():
            if memory_type and memory.memory_type.value != memory_type:
                continue
            if user_id and memory.metadata.get("user_id") != user_id:
                continue
            candidate_memories.append(memory)
        
        if not query:
            # Return filtered memories
            self._update_access_stats(candidate_memories[-limit:])
            return self._format_memories(candidate_memories[-limit:])
        
        # Perform semantic search
        query_embedding = self._generate_embeddings(query)
        if query_embedding is None:
            # Fallback to keyword search
            results = self._keyword_search(query, candidate_memories, limit)
            self.stats["failed_recalls"] += 1
            return results
        
        # Calculate similarities
        similarities = []
        for memory in candidate_memories:
            if memory.embeddings is not None:
                similarity = cosine_similarity(
                    query_embedding.reshape(1, -1),
                    memory.embeddings.reshape(1, -1)
                )[0][0]
                
                # Apply decay adjustment
                decay_adjustment = self._calculate_decay_adjustment(memory)
                adjusted_similarity = similarity * decay_adjustment
                
                # Apply priority boost
                priority_boost = self._get_priority_boost(memory.priority)
                final_similarity = adjusted_similarity * priority_boost
                
                similarities.append((memory, final_similarity))
        
        # Sort by similarity and filter by threshold
        similarities.sort(key=lambda x: x[1], reverse=True)
        filtered_results = [
            memory for memory, similarity in similarities
            if similarity >= similarity_threshold
        ][:limit]
        
        self._update_access_stats(filtered_results)
        self.stats["successful_recalls"] += 1
        
        return self._format_memories(filtered_results)
    
    def _keyword_search(self, query: str, memories: List[MemoryEntry], limit: int) -> List[Dict]:
        """Fallback keyword search"""
        query_lower = query.lower()
        results = []
        
        for memory in reversed(memories):
            if (query_lower in memory.content.lower() or 
                any(query_lower in tag for tag in memory.tags or [])):
                results.append(memory)
                if len(results) >= limit:
                    break
        
        return self._format_memories(results)
    
    def _calculate_decay_adjustment(self, memory: MemoryEntry) -> float:
        """Calculate decay adjustment for memory relevance"""
        # Base decay based on age
        try:
            memory_age = datetime.datetime.now() - datetime.datetime.fromisoformat(memory.timestamp)
            days_old = memory_age.days
            
            # Exponential decay: memory.decay_factor^days_old
            decay = memory.decay_factor ** min(days_old, 365)  # Cap at 1 year
            
            # Access count boost (frequently accessed memories decay slower)
            access_boost = min(1.0, memory.access_count * 0.01)
            
            return decay * (1.0 + access_boost)
        except:
            return 1.0
    
    def _get_priority_boost(self, priority: MemoryPriority) -> float:
        """Get priority-based relevance boost"""
        boosts = {
            MemoryPriority.CRITICAL: 1.5,
            MemoryPriority.HIGH: 1.3,
            MemoryPriority.MEDIUM: 1.1,
            MemoryPriority.LOW: 1.0
        }
        return boosts.get(priority, 1.0)
    
    def _update_access_stats(self, memories: List[MemoryEntry]):
        """Update access statistics for memories"""
        for memory in memories:
            memory.access_count += 1
            memory.last_accessed = datetime.datetime.now().isoformat()
    
    def _format_memories(self, memories: List[MemoryEntry]) -> List[Dict]:
        """Format memories for output"""
        formatted = []
        for memory in memories:
            formatted.append({
                "id": memory.id,
                "content": memory.content,
                "type": memory.memory_type.value,
                "priority": memory.priority.value,
                "timestamp": memory.timestamp,
                "tags": memory.tags or [],
                "access_count": memory.access_count,
                "last_accessed": memory.last_accessed,
                "metadata": memory.metadata or {}
            })
        return formatted
    
    def recall_conversation_context(self, user_id: str = "default", 
                                   window_size: int = 10) -> List[Dict]:
        """Recall conversation context for a user"""
        context_memories = []
        user_conversations = []
        
        # Get user's recent conversations from flow
        for entry in reversed(self.conversation_flow):
            if entry.get("user_id") == user_id:
                memory_id = entry.get("memory_id")
                if memory_id in self.memories:
                    user_conversations.append(self.memories[memory_id])
                if len(user_conversations) >= window_size:
                    break
        
        return self._format_memories(user_conversations)
    
    def update_preference(self, user_id: str, key: str, value: Any, 
                         priority: MemoryPriority = MemoryPriority.MEDIUM):
        """Update user preference as a memory"""
        content = f"User preference: {key} = {value}"
        
        # Create or update preference memory
        pref_memory_id = f"pref_{user_id}_{key}"
        
        if pref_memory_id in self.memories:
            # Update existing preference
            self.memories[pref_memory_id].content = content
            self.memories[pref_memory_id].timestamp = datetime.datetime.now().isoformat()
            self.memories[pref_memory_id].priority = priority
        else:
            # Create new preference memory
            metadata = {
                "user_id": user_id,
                "preference_key": key,
                "preference_value": value
            }
            tags = ["preference", f"user:{user_id}", f"key:{key}"]
            
            self.create_memory(
                content=content,
                memory_type=MemoryType.PREFERENCE,
                priority=priority,
                metadata=metadata,
                tags=tags
            )
        
        # Update user profile
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {"preferences": {}}
        
        if "preferences" not in self.user_profiles[user_id]:
            self.user_profiles[user_id]["preferences"] = {}
        
        self.user_profiles[user_id]["preferences"][key] = {
            "value": value,
            "updated": datetime.datetime.now().isoformat(),
            "priority": priority.value
        }
        
        self.save_memory()
    
    def get_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        """Get user preference"""
        if user_id in self.user_profiles:
            prefs = self.user_profiles[user_id].get("preferences", {})
            if key in prefs:
                return prefs[key].get("value", default)
        return default
    
    def remember_fact(self, fact: str, source: str = None, 
                     tags: List[str] = None) -> str:
        """Remember a fact with metadata"""
        metadata = {
            "source": source,
            "fact_type": "general",
            "verified": False
        }
        
        return self.create_memory(
            content=fact,
            memory_type=MemoryType.FACT,
            priority=MemoryPriority.MEDIUM,
            metadata=metadata,
            tags=tags or ["fact", "knowledge"]
        )
    
    def remember_event(self, event_description: str, event_time: str = None,
                      participants: List[str] = None, location: str = None) -> str:
        """Remember an event"""
        metadata = {
            "event_time": event_time or datetime.datetime.now().isoformat(),
            "participants": participants or [],
            "location": location,
            "event_type": "general"
        }
        
        tags = ["event", "temporal"]
        if participants:
            for participant in participants[:3]:
                tags.append(f"participant:{participant.lower()}")
        
        return self.create_memory(
            content=event_description,
            memory_type=MemoryType.EVENT,
            priority=MemoryPriority.HIGH,
            metadata=metadata,
            tags=tags
        )
    
    def get_memory_statistics(self) -> Dict:
        """Get comprehensive memory statistics"""
        total_memories = len(self.memories)
        
        # Calculate memory health
        recent_access_count = sum(1 for m in self.memories.values() 
                                if m.last_accessed and 
                                (datetime.datetime.now() - 
                                 datetime.datetime.fromisoformat(m.last_accessed)).days < 7)
        
        memory_health = (recent_access_count / max(1, total_memories)) * 100
        
        # Calculate average priority
        avg_priority = np.mean([m.priority.value for m in self.memories.values()]) \
            if self.memories else 0
        
        return {
            "total_memories": total_memories,
            "memories_by_type": dict(self.stats["memories_by_type"]),
            "memory_health_percentage": round(memory_health, 2),
            "average_priority": round(avg_priority, 2),
            "total_users": len(self.user_profiles),
            "conversation_flow_size": len(self.conversation_flow),
            "recall_success_rate": (
                (self.stats["successful_recalls"] / 
                 max(1, self.stats["total_recalls"])) * 100
            ) if self.stats["total_recalls"] > 0 else 0,
            **self.stats
        }
    
    def get_conversation_summary(self, days: int = 7, user_id: str = None) -> Dict:
        """Get detailed conversation summary"""
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        
        relevant_memories = []
        for memory in self.memories.values():
            if memory.memory_type != MemoryType.CONVERSATION:
                continue
            
            memory_time = datetime.datetime.fromisoformat(memory.timestamp)
            if memory_time < cutoff:
                continue
            
            if user_id and memory.metadata.get("user_id") != user_id:
                continue
            
            relevant_memories.append(memory)
        
        # Analyze conversations
        topics = defaultdict(int)
        sentiment_scores = []
        conversation_lengths = []
        
        for memory in relevant_memories:
            # Topic analysis
            for tag in memory.tags or []:
                if "topic_" in tag or "entity:" in tag:
                    topics[tag] += 1
            
            # Simple sentiment analysis (basic)
            content_lower = memory.content.lower()
            positive_words = ["good", "great", "happy", "excellent", "thanks"]
            negative_words = ["bad", "terrible", "sad", "angry", "sorry"]
            
            positive_count = sum(1 for word in positive_words if word in content_lower)
            negative_count = sum(1 for word in negative_words if word in content_lower)
            
            if positive_count > negative_count:
                sentiment_scores.append(1)
            elif negative_count > positive_count:
                sentiment_scores.append(-1)
            else:
                sentiment_scores.append(0)
            
            # Length analysis
            conversation_lengths.append(len(memory.content))
        
        # Calculate statistics
        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
        avg_length = np.mean(conversation_lengths) if conversation_lengths else 0
        
        # Get most active time
        hour_counts = defaultdict(int)
        for memory in relevant_memories:
            hour = datetime.datetime.fromisoformat(memory.timestamp).hour
            hour_counts[hour] += 1
        
        most_active_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else 0
        
        return {
            "total_conversations": len(relevant_memories),
            "top_topics": dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]),
            "average_sentiment": round(avg_sentiment, 2),
            "average_conversation_length": round(avg_length, 2),
            "most_active_hour": most_active_hour,
            "conversations_by_priority": {
                "critical": sum(1 for m in relevant_memories if m.priority == MemoryPriority.CRITICAL),
                "high": sum(1 for m in relevant_memories if m.priority == MemoryPriority.HIGH),
                "medium": sum(1 for m in relevant_memories if m.priority == MemoryPriority.MEDIUM),
                "low": sum(1 for m in relevant_memories if m.priority == MemoryPriority.LOW)
            }
        }
    
    def forget_memory(self, memory_id: str) -> bool:
        """Forget/remove a specific memory"""
        if memory_id in self.memories:
            memory = self.memories[memory_id]
            
            # Remove from index
            for tag in memory.tags or []:
                if tag in self.memory_index and memory_id in self.memory_index[tag]:
                    self.memory_index[tag].remove(memory_id)
            
            # Remove from memories
            del self.memories[memory_id]
            
            # Update stats
            self.stats["total_memories"] -= 1
            self.stats["memories_by_type"][memory.memory_type.value] = max(
                0, self.stats["memories_by_type"][memory.memory_type.value] - 1
            )
            
            self.save_memory()
            return True
        
        return False
    
    def forget_old_memories(self, days_old: int = 30, 
                           keep_priority: MemoryPriority = MemoryPriority.CRITICAL):
        """Forget old memories based on age and priority"""
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days_old)
        forgotten_count = 0
        
        memory_ids_to_remove = []
        for memory_id, memory in self.memories.items():
            memory_time = datetime.datetime.fromisoformat(memory.timestamp)
            if memory_time < cutoff and memory.priority.value < keep_priority.value:
                memory_ids_to_remove.append(memory_id)
        
        for memory_id in memory_ids_to_remove:
            if self.forget_memory(memory_id):
                forgotten_count += 1
        
        return forgotten_count
    
    def _consolidate_memories(self):
        """Consolidate similar memories to reduce redundancy"""
        # This is a simplified version - in production, use clustering algorithms
        memory_list = list(self.memories.values())
        
        # Group by type and tags
        consolidation_candidates = defaultdict(list)
        for memory in memory_list:
            if memory.tags:
                key = f"{memory.memory_type.value}_{sorted(memory.tags)[0]}"
                consolidation_candidates[key].append(memory)
        
        # For each group, keep the highest priority ones
        for key, memories in consolidation_candidates.items():
            if len(memories) > 5:  # Only consolidate large groups
                # Sort by priority and timestamp
                memories.sort(key=lambda m: (m.priority.value, m.timestamp), reverse=True)
                
                # Keep top 3, forget others
                for memory in memories[3:]:
                    if memory.priority != MemoryPriority.CRITICAL:
                        self.forget_memory(memory.id)
        
        self.stats["consolidations"] += 1
    
    def search_memories_semantic(self, query: str, top_k: int = 5) -> List[Dict]:
        """Advanced semantic search using embeddings"""
        if not hasattr(self.vectorizer, 'vocabulary_'):
            return []
        
        query_vector = self.vectorizer.transform([query.lower()]).toarray()[0]
        
        similarities = []
        for memory in self.memories.values():
            if memory.embeddings is not None:
                similarity = cosine_similarity(
                    query_vector.reshape(1, -1),
                    memory.embeddings.reshape(1, -1)
                )[0][0]
                similarities.append((memory, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = [mem for mem, sim in similarities[:top_k]]
        
        return self._format_memories(results)
    
    def export_memory_data(self, format: str = "json") -> Dict:
        """Export memory data for analysis or backup"""
        export_data = {
            "metadata": {
                "export_timestamp": datetime.datetime.now().isoformat(),
                "total_memories": len(self.memories),
                "total_users": len(self.user_profiles)
            },
            "statistics": self.get_memory_statistics(),
            "user_summary": {
                user_id: {
                    "total_conversations": profile.get("total_conversations", 0),
                    "preferred_topics": dict(profile.get("preferred_topics", {})),
                    "last_interaction": profile.get("last_interaction")
                }
                for user_id, profile in list(self.user_profiles.items())[:10]
            },
            "recent_conversations": [
                {
                    "id": memory.id,
                    "preview": memory.content[:100],
                    "timestamp": memory.timestamp,
                    "tags": memory.tags[:5] if memory.tags else []
                }
                for memory in list(self.memories.values())[-10:]
                if memory.memory_type == MemoryType.CONVERSATION
            ]
        }
        
        return export_data


# Example usage
if __name__ == "__main__":
    print("Testing Enhanced Memory System...")
    
    # Initialize system
    memory_system = EnhancedMemorySystem()
    
    # Remember some conversations
    conversations = [
        ("Hello Jarvis, how are you today?", "I'm doing great! How can I assist you?"),
        ("What's the weather like in New York?", "I don't have real-time weather data, but you can check online."),
        ("Remember that I have a meeting tomorrow at 2 PM", "I'll remember your meeting tomorrow at 2 PM."),
        ("What's the capital of France?", "The capital of France is Paris."),
        ("Can you help me with Python programming?", "Sure! I can help with Python programming. What do you need?"),
    ]
    
    for i, (user_input, response) in enumerate(conversations):
        memory_id = memory_system.remember_conversation(
            user_input=user_input,
            bot_response=response,
            user_id="user123",
            importance=i  # Varying importance
        )
        print(f"Remembered: {user_input[:30]}...")
    
    # Test recall
    print("\nTesting recall for 'weather':")
    recalled = memory_system.recall_memories(query="weather", limit=3)
    for mem in recalled:
        print(f"  - {mem['content'][:50]}...")
    
    # Test semantic search
    print("\nTesting semantic search for 'assistance':")
    semantic_results = memory_system.search_memories_semantic("assistance", top_k=2)
    for mem in semantic_results:
        print(f"  - {mem['content'][:50]}...")
    
    # Get statistics
    stats = memory_system.get_memory_statistics()
    print(f"\nMemory Statistics:")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")
    
    # Get conversation summary
    summary = memory_system.get_conversation_summary(days=7)
    print(f"\nConversation Summary (last 7 days):")
    print(f"  Total conversations: {summary['total_conversations']}")
    print(f"  Top topics: {summary['top_topics']}")
    print(f"  Average sentiment: {summary['average_sentiment']}")
    
    # Export data
    export = memory_system.export_memory_data()
    print(f"\nExported data structure: {list(export.keys())}")