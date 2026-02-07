#!/usr/bin/env python3
"""
Memory System Module
Handles conversation memory and recall
"""

import json
import datetime
import hashlib
from collections import deque

class MemorySystem:
    def __init__(self, memory_file="jarvis_memory.json", max_conversations=100):
        self.memory_file = memory_file
        self.max_conversations = max_conversations
        self.conversation_history = deque(maxlen=max_conversations)
        self.important_memories = []
        self.user_preferences = {}
        self.load_memory()
        
    def load_memory(self):
        """Load memory from file"""
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
                self.conversation_history = deque(data.get("conversations", []), 
                                                 maxlen=self.max_conversations)
                self.important_memories = data.get("important_memories", [])
                self.user_preferences = data.get("user_preferences", {})
        except (FileNotFoundError, json.JSONDecodeError):
            self.save_memory()
    
    def save_memory(self):
        """Save memory to file"""
        data = {
            "conversations": list(self.conversation_history),
            "important_memories": self.important_memories,
            "user_preferences": self.user_preferences,
            "last_updated": datetime.datetime.now().isoformat()
        }
        with open(self.memory_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def remember_conversation(self, user_input, jarvis_response, importance=0):
        """Store a conversation in memory"""
        conversation_id = hashlib.md5(f"{user_input}{datetime.datetime.now()}".encode()).hexdigest()[:8]
        
        memory_entry = {
            "id": conversation_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "user_input": user_input,
            "jarvis_response": jarvis_response,
            "importance": importance,
            "tags": self._extract_tags(user_input)
        }
        
        self.conversation_history.append(memory_entry)
        
        # Mark as important if needed
        if importance >= 3:
            self.important_memories.append(memory_entry)
            # Keep only last 20 important memories
            if len(self.important_memories) > 20:
                self.important_memories.pop(0)
        
        self.save_memory()
        return conversation_id
    
    def _extract_tags(self, text):
        """Extract keywords/tags from text"""
        tags = []
        important_keywords = ["important", "remember", "don't forget", "note", 
                            "save this", "keep in mind", "crucial", "essential"]
        
        text_lower = text.lower()
        for keyword in important_keywords:
            if keyword in text_lower:
                tags.append("important")
                break
        
        # Add topic tags
        topics = {
            "work": ["work", "job", "office", "project"],
            "personal": ["personal", "family", "friend", "home"],
            "technical": ["code", "program", "tech", "computer", "system"],
            "entertainment": ["music", "movie", "game", "fun", "entertain"],
            "learning": ["study", "learn", "research", "education"]
        }
        
        for topic, keywords in topics.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(topic)
                break
        
        return tags
    
    def recall_conversation(self, query="", limit=5):
        """Recall conversations matching query"""
        if not query:
            # Return recent conversations
            return list(self.conversation_history)[-limit:]
        
        query_lower = query.lower()
        results = []
        
        for memory in reversed(list(self.conversation_history)):
            if (query_lower in memory["user_input"].lower() or 
                query_lower in memory["jarvis_response"].lower()):
                results.append(memory)
                if len(results) >= limit:
                    break
        
        return results
    
    def recall_important(self):
        """Recall important memories"""
        return self.important_memories[-5:] if self.important_memories else []
    
    def update_preference(self, key, value):
        """Update user preference"""
        self.user_preferences[key] = {
            "value": value,
            "updated": datetime.datetime.now().isoformat()
        }
        self.save_memory()
    
    def get_preference(self, key, default=None):
        """Get user preference"""
        return self.user_preferences.get(key, {}).get("value", default)
    
    def get_conversation_summary(self, days=7):
        """Get summary of recent conversations"""
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        
        recent_convos = []
        for conv in self.conversation_history:
            conv_time = datetime.datetime.fromisoformat(conv["timestamp"])
            if conv_time >= cutoff:
                recent_convos.append(conv)
        
        topics = {}
        for conv in recent_convos:
            for tag in conv.get("tags", []):
                topics[tag] = topics.get(tag, 0) + 1
        
        return {
            "total_conversations": len(recent_convos),
            "top_topics": dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]),
            "most_important": [c for c in recent_convos if c.get("importance", 0) >= 3][:3]
        }
    