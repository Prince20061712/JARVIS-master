#!/usr/bin/env python3
"""
Enhanced Learning System Module
Learns from interactions using ML techniques and improves responses
"""

import json
import datetime
import re
import hashlib
import pickle
import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional, Any
import os
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

@dataclass
class Interaction:
    user_input: str
    bot_response: str
    timestamp: str
    feedback: Optional[int] = None
    correction: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class EnhancedLearningSystem:
    def __init__(self, learning_dir="learning_data"):
        self.learning_dir = learning_dir
        os.makedirs(learning_dir, exist_ok=True)
        
        # Learning files
        self.interactions_file = os.path.join(learning_dir, "interactions.jsonl")
        self.patterns_file = os.path.join(learning_dir, "patterns.pkl")
        self.vectorizer_file = os.path.join(learning_dir, "vectorizer.pkl")
        self.context_memory_file = os.path.join(learning_dir, "context_memory.json")
        
        # Initialize data structures
        self.interactions: List[Interaction] = []
        self.response_patterns = defaultdict(list)
        self.context_patterns = defaultdict(list)
        self.user_profiles = defaultdict(dict)
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.response_texts = []
        
        # Learning parameters
        self.min_confidence_threshold = 0.3
        self.learning_rate = 0.1
        self.context_window_size = 5
        
        # Statistics
        self.stats = {
            "total_interactions": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "user_corrections": 0,
            "auto_learned_patterns": 0,
            "context_aware_responses": 0,
            "personalized_responses": 0
        }
        
        # Load existing data
        self.load_learning_data()
        self.initialize_nlp()
    
    def initialize_nlp(self):
        """Initialize NLP components"""
        try:
            # Try to load existing vectorizer
            if os.path.exists(self.vectorizer_file):
                with open(self.vectorizer_file, 'rb') as f:
                    self.tfidf_vectorizer = pickle.load(f)
        except:
            pass
        
        if self.tfidf_vectorizer is None:
            self.tfidf_vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=1000
            )
    
    def load_learning_data(self):
        """Load all learning data"""
        # Load interactions
        if os.path.exists(self.interactions_file):
            with open(self.interactions_file, 'r') as f:
                for line in f:
                    data = json.loads(line.strip())
                    self.interactions.append(Interaction(**data))
        
        # Load patterns
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, 'rb') as f:
                    patterns_data = pickle.load(f)
                    self.response_patterns = patterns_data.get('response_patterns', defaultdict(list))
                    self.context_patterns = patterns_data.get('context_patterns', defaultdict(list))
            except:
                pass
        
        # Load user profiles
        if os.path.exists(self.context_memory_file):
            try:
                with open(self.context_memory_file, 'r') as f:
                    data = json.load(f)
                    self.user_profiles = defaultdict(dict, data.get('user_profiles', {}))
                    self.stats.update(data.get('stats', self.stats))
            except:
                pass
    
    def save_learning_data(self):
        """Save all learning data"""
        # Save interactions (append mode)
        with open(self.interactions_file, 'a') as f:
            # Only save new interactions
            pass  # We'll handle this differently in record_interaction
        
        # Save patterns
        patterns_data = {
            'response_patterns': dict(self.response_patterns),
            'context_patterns': dict(self.context_patterns),
            'last_updated': datetime.datetime.now().isoformat()
        }
        with open(self.patterns_file, 'wb') as f:
            pickle.dump(patterns_data, f)
        
        # Save context memory and user profiles
        context_data = {
            'user_profiles': dict(self.user_profiles),
            'stats': self.stats,
            'last_updated': datetime.datetime.now().isoformat()
        }
        with open(self.context_memory_file, 'w') as f:
            json.dump(context_data, f, indent=2)
        
        # Save vectorizer if it has been fitted
        if hasattr(self.tfidf_vectorizer, 'vocabulary_'):
            with open(self.vectorizer_file, 'wb') as f:
                pickle.dump(self.tfidf_vectorizer, f)
    
    def record_interaction(self, user_input: str, bot_response: str, 
                          user_id: str = "default", context: Dict = None,
                          metadata: Dict = None) -> str:
        """Record an interaction"""
        interaction_id = hashlib.md5(
            f"{user_input}{bot_response}{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        interaction = Interaction(
            user_input=user_input,
            bot_response=bot_response,
            timestamp=datetime.datetime.now().isoformat(),
            context=context or {},
            metadata=metadata or {}
        )
        
        # Add to interactions list
        self.interactions.append(interaction)
        
        # Update user profile
        self._update_user_profile(user_id, user_input, bot_response)
        
        # Save to file
        with open(self.interactions_file, 'a') as f:
            json_str = json.dumps({
                'user_input': user_input,
                'bot_response': bot_response,
                'timestamp': interaction.timestamp,
                'context': interaction.context,
                'metadata': interaction.metadata
            })
            f.write(json_str + '\n')
        
        self.stats["total_interactions"] += 1
        
        # Try to auto-learn patterns
        self._auto_learn_patterns(user_input, bot_response, context)
        
        return interaction_id
    
    def _auto_learn_patterns(self, user_input: str, bot_response: str, context: Dict = None):
        """Automatically learn patterns from successful interactions"""
        # Extract semantic patterns
        patterns = self._extract_semantic_patterns(user_input)
        
        # Learn response patterns
        for pattern in patterns:
            if bot_response not in self.response_patterns[pattern]:
                self.response_patterns[pattern].append({
                    'response': bot_response,
                    'confidence': 1.0,
                    'count': 1,
                    'last_used': datetime.datetime.now().isoformat()
                })
        
        # Learn context patterns
        if context:
            context_key = self._generate_context_key(context)
            if bot_response not in self.context_patterns[context_key]:
                self.context_patterns[context_key].append(bot_response)
        
        self.stats["auto_learned_patterns"] += 1
    
    def _extract_semantic_patterns(self, text: str) -> List[str]:
        """Extract semantic patterns from text"""
        patterns = []
        text_lower = text.lower().strip()
        
        # 1. Intent patterns
        intents = self._detect_intent(text_lower)
        patterns.extend([f"intent:{intent}" for intent in intents])
        
        # 2. Entity patterns
        entities = self._extract_entities(text_lower)
        patterns.extend([f"entity:{entity}" for entity in entities])
        
        # 3. Question type patterns
        if text_lower.endswith('?'):
            q_type = self._detect_question_type(text_lower)
            patterns.append(f"question:{q_type}")
        
        # 4. Semantic keyphrases
        keyphrases = self._extract_keyphrases(text_lower)
        patterns.extend([f"keyphrase:{kp}" for kp in keyphrases])
        
        # 5. Full text hash (for exact or near-exact matches)
        text_hash = hashlib.md5(text_lower.encode()).hexdigest()[:8]
        patterns.append(f"hash:{text_hash}")
        
        return patterns
    
    def _detect_intent(self, text: str) -> List[str]:
        """Detect user intent"""
        intents = []
        
        intent_patterns = {
            "greeting": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
            "farewell": ["bye", "goodbye", "see you", "take care"],
            "question": ["what", "who", "where", "when", "why", "how", "which", "can you", "could you"],
            "command": ["play", "open", "close", "search", "find", "get", "show", "tell", "set", "create"],
            "explanation": ["explain", "describe", "tell me about", "what is", "who is"],
            "comparison": ["compare", "difference between", "vs", "versus"],
            "opinion": ["what do you think", "opinion", "believe", "feel about"],
            "help": ["help", "assist", "support", "how to", "can you help"],
            "thanks": ["thank", "thanks", "appreciate"],
            "apology": ["sorry", "apologize", "my bad"],
            "confirmation": ["yes", "correct", "right", "that's right"],
            "negation": ["no", "wrong", "incorrect", "not"]
        }
        
        for intent, keywords in intent_patterns.items():
            if any(keyword in text for keyword in keywords):
                intents.append(intent)
        
        return intents if intents else ["general"]
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text (simplified)"""
        entities = []
        
        # Common entity patterns
        entity_patterns = [
            (r'\b\d{4}\b', 'year'),  # Years
            (r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', 'proper_noun'),  # Proper nouns
            (r'\b\d+(?:\.\d+)?\b', 'number'),  # Numbers
            (r'#[A-Za-z0-9_]+', 'hashtag'),  # Hashtags
            (r'@[A-Za-z0-9_]+', 'mention'),  # Mentions
        ]
        
        for pattern, label in entity_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                entities.append(f"{label}:{match}")
        
        return entities
    
    def _detect_question_type(self, text: str) -> str:
        """Detect question type"""
        if text.startswith(('what is', 'what are', 'what was', 'what were')):
            return "definition"
        elif text.startswith(('who is', 'who are', 'who was', 'who were')):
            return "person"
        elif text.startswith(('where is', 'where are')):
            return "location"
        elif text.startswith(('when is', 'when was', 'when are', 'when were')):
            return "time"
        elif text.startswith(('why is', 'why are', 'why was', 'why were')):
            return "reason"
        elif text.startswith(('how is', 'how are', 'how was', 'how were', 'how to', 'how can', 'how do')):
            return "method"
        elif text.startswith(('which', 'can you', 'could you', 'would you')):
            return "choice"
        else:
            return "general"
    
    def _extract_keyphrases(self, text: str, max_phrases: int = 3) -> List[str]:
        """Extract key phrases from text"""
        # Simple keyphrase extraction based on word importance
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        word_freq = Counter(words)
        
        # Remove stop words
        for stop_word in stop_words:
            if stop_word in word_freq:
                del word_freq[stop_word]
        
        # Get top phrases (could be enhanced with n-grams)
        keyphrases = [word for word, freq in word_freq.most_common(max_phrases)]
        
        return keyphrases
    
    def _generate_context_key(self, context: Dict) -> str:
        """Generate a key from context"""
        context_items = []
        if 'time_of_day' in context:
            context_items.append(f"time:{context['time_of_day']}")
        if 'conversation_topic' in context:
            context_items.append(f"topic:{context['conversation_topic']}")
        if 'user_mood' in context:
            context_items.append(f"mood:{context['user_mood']}")
        
        return "|".join(context_items) if context_items else "general"
    
    def _update_user_profile(self, user_id: str, user_input: str, bot_response: str):
        """Update user profile with interaction"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "interaction_count": 0,
                "preferred_topics": defaultdict(int),
                "response_preferences": defaultdict(int),
                "last_interaction": None,
                "interaction_history": []
            }
        
        profile = self.user_profiles[user_id]
        profile["interaction_count"] += 1
        profile["last_interaction"] = datetime.datetime.now().isoformat()
        
        # Extract topics from interaction
        topics = self._extract_keyphrases(user_input.lower() + " " + bot_response.lower())
        for topic in topics:
            profile["preferred_topics"][topic] += 1
        
        # Record response preference (simplified)
        response_type = self._categorize_response(bot_response)
        profile["response_preferences"][response_type] += 1
        
        # Keep limited history
        profile["interaction_history"].append({
            "input": user_input[:100],  # Truncate
            "response": bot_response[:100],
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        # Keep only last 50 interactions
        if len(profile["interaction_history"]) > 50:
            profile["interaction_history"] = profile["interaction_history"][-50:]
    
    def _categorize_response(self, response: str) -> str:
        """Categorize response type"""
        response_lower = response.lower()
        
        if any(word in response_lower for word in ["yes", "correct", "right", "agree"]):
            return "affirmative"
        elif any(word in response_lower for word in ["no", "wrong", "incorrect", "disagree"]):
            return "negative"
        elif response_lower.endswith("?"):
            return "question"
        elif len(response.split()) > 20:
            return "detailed"
        elif len(response.split()) < 10:
            return "concise"
        else:
            return "neutral"
    
    def get_learned_response(self, user_input: str, user_id: str = "default", 
                           context: Dict = None) -> Tuple[Optional[str], float]:
        """Get response from learned patterns with confidence score"""
        best_response = None
        best_confidence = 0.0
        
        # 1. Try exact pattern matching
        patterns = self._extract_semantic_patterns(user_input)
        for pattern in patterns:
            if pattern in self.response_patterns:
                for pattern_data in self.response_patterns[pattern]:
                    confidence = pattern_data['confidence']
                    if confidence > best_confidence and confidence >= self.min_confidence_threshold:
                        best_response = pattern_data['response']
                        best_confidence = confidence
        
        # 2. Try context-aware matching
        if context and best_confidence < 0.7:
            context_key = self._generate_context_key(context)
            if context_key in self.context_patterns and self.context_patterns[context_key]:
                context_response = np.random.choice(self.context_patterns[context_key])
                if best_confidence < 0.6:
                    best_response = context_response
                    best_confidence = 0.6
                    self.stats["context_aware_responses"] += 1
        
        # 3. Try user-personalized responses
        if user_id in self.user_profiles and best_confidence < 0.5:
            user_profile = self.user_profiles[user_id]
            # Check for similar past interactions
            for interaction in user_profile["interaction_history"][-10:]:
                if self._calculate_similarity(user_input, interaction["input"]) > 0.7:
                    if interaction["response"]:
                        best_response = interaction["response"]
                        best_confidence = 0.5
                        self.stats["personalized_responses"] += 1
                        break
        
        return best_response, best_confidence
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity"""
        # Simple cosine similarity using TF-IDF
        try:
            if not hasattr(self.tfidf_vectorizer, 'vocabulary_'):
                # Fit vectorizer if not already fitted
                all_texts = [text1, text2] + [i.user_input for i in self.interactions[-100:]]
                self.tfidf_vectorizer.fit(all_texts)
            
            vectors = self.tfidf_vectorizer.transform([text1, text2])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return similarity
        except:
            # Fallback to simple word overlap
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            if not words1 or not words2:
                return 0.0
            return len(words1.intersection(words2)) / len(words1.union(words2))
    
    def record_feedback(self, interaction_id: str, feedback_score: int, 
                       user_id: str = "default"):
        """Record user feedback (1-5 scale)"""
        # Find interaction (simplified - in production, use database)
        if feedback_score >= 3:
            self.stats["successful_responses"] += 1
        else:
            self.stats["failed_responses"] += 1
        
        # Update user profile with feedback
        if user_id in self.user_profiles:
            self.user_profiles[user_id]["last_feedback"] = {
                "score": feedback_score,
                "timestamp": datetime.datetime.now().isoformat()
            }
        
        self.save_learning_data()
    
    def record_correction(self, user_input: str, wrong_response: str, 
                         correct_response: str, user_id: str = "default"):
        """Record a correction and learn from it"""
        correction_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_input": user_input,
            "wrong_response": wrong_response,
            "correct_response": correct_response,
            "user_id": user_id
        }
        
        # Update patterns with correction
        patterns = self._extract_semantic_patterns(user_input)
        
        # Remove wrong response from patterns
        for pattern in patterns:
            if pattern in self.response_patterns:
                self.response_patterns[pattern] = [
                    p for p in self.response_patterns[pattern] 
                    if p['response'] != wrong_response
                ]
        
        # Add correct response with high confidence
        self.learn_response(user_input, correct_response, confidence=0.9)
        
        self.stats["user_corrections"] += 1
        self.save_learning_data()
        
        return correction_data
    
    def learn_response(self, user_input: str, response: str, confidence: float = 1.0):
        """Explicitly learn a response"""
        patterns = self._extract_semantic_patterns(user_input)
        
        for pattern in patterns:
            # Check if response already exists for this pattern
            response_exists = False
            for pattern_data in self.response_patterns[pattern]:
                if pattern_data['response'] == response:
                    # Update confidence and count
                    pattern_data['confidence'] = min(1.0, pattern_data['confidence'] + self.learning_rate)
                    pattern_data['count'] += 1
                    pattern_data['last_used'] = datetime.datetime.now().isoformat()
                    response_exists = True
                    break
            
            if not response_exists:
                self.response_patterns[pattern].append({
                    'response': response,
                    'confidence': confidence,
                    'count': 1,
                    'last_used': datetime.datetime.now().isoformat()
                })
        
        self.save_learning_data()
        return True
    
    def get_learning_statistics(self) -> Dict:
        """Get comprehensive learning statistics"""
        total_patterns = sum(len(responses) for responses in self.response_patterns.values())
        total_users = len(self.user_profiles)
        
        # Calculate average confidence
        all_confidences = []
        for responses in self.response_patterns.values():
            for response_data in responses:
                all_confidences.append(response_data['confidence'])
        
        avg_confidence = np.mean(all_confidences) if all_confidences else 0
        
        return {
            "total_learned_patterns": total_patterns,
            "unique_patterns": len(self.response_patterns),
            "context_patterns": len(self.context_patterns),
            "total_users": total_users,
            "total_interactions": len(self.interactions),
            "average_confidence": round(avg_confidence, 3),
            "success_rate": (
                (self.stats["successful_responses"] / 
                 max(1, self.stats["successful_responses"] + self.stats["failed_responses"])) * 100
            ) if (self.stats["successful_responses"] + self.stats["failed_responses"]) > 0 else 0,
            **self.stats
        }
    
    def get_user_profile(self, user_id: str = "default") -> Optional[Dict]:
        """Get user profile"""
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id].copy()
            
            # Calculate favorite topics
            topics = profile.get("preferred_topics", {})
            if topics:
                favorite_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]
                profile["favorite_topics"] = [topic for topic, count in favorite_topics]
            
            # Calculate response preferences
            prefs = profile.get("response_preferences", {})
            if prefs:
                total = sum(prefs.values())
                profile["response_style"] = max(prefs.items(), key=lambda x: x[1])[0] if total > 0 else "neutral"
            
            return profile
        return None
    
    def forget_pattern(self, pattern: str = None, response: str = None):
        """Forget/remove a pattern or response"""
        if pattern and pattern in self.response_patterns:
            if response:
                # Remove specific response from pattern
                self.response_patterns[pattern] = [
                    p for p in self.response_patterns[pattern] 
                    if p['response'] != response
                ]
                if not self.response_patterns[pattern]:
                    del self.response_patterns[pattern]
            else:
                # Remove entire pattern
                del self.response_patterns[pattern]
        
        self.save_learning_data()
        return True
    
    def export_learning_data(self, format: str = "json") -> Dict:
        """Export learning data for analysis"""
        data = {
            "statistics": self.get_learning_statistics(),
            "patterns_summary": {
                "total_patterns": sum(len(responses) for responses in self.response_patterns.values()),
                "pattern_categories": Counter(
                    [p.split(':')[0] for p in self.response_patterns.keys() if ':' in p]
                ),
                "top_patterns": sorted(
                    [(p, len(r)) for p, r in self.response_patterns.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            },
            "user_summary": {
                "total_users": len(self.user_profiles),
                "active_users": sum(1 for p in self.user_profiles.values() 
                                  if p.get("interaction_count", 0) > 5),
                "interactions_per_user": {
                    user_id: profile.get("interaction_count", 0)
                    for user_id, profile in list(self.user_profiles.items())[:5]
                }
            }
        }
        
        return data
    
    def reset_learning(self, keep_users: bool = False):
        """Reset learning data (with option to keep user profiles)"""
        self.response_patterns = defaultdict(list)
        self.context_patterns = defaultdict(list)
        
        if not keep_users:
            self.user_profiles = defaultdict(dict)
        
        self.interactions = []
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=1000
        )
        
        # Reset stats but keep structure
        self.stats = {k: 0 for k in self.stats.keys()}
        
        self.save_learning_data()
        return True


# Example usage with integration
if __name__ == "__main__":
    print("Testing Enhanced Learning System...")
    
    # Initialize system
    learning_system = EnhancedLearningSystem()
    
    # Record some interactions
    interactions = [
        ("Hello, how are you?", "I'm doing great! How can I help you today?", "greeting"),
        ("What's the weather like?", "I don't have access to real-time weather data, but you can check your local weather app.", "weather_query"),
        ("Tell me about artificial intelligence", "Artificial Intelligence is the simulation of human intelligence in machines.", "explanation"),
        ("Who is Elon Musk?", "Elon Musk is a business magnate and investor.", "person_query"),
        ("Thank you for your help!", "You're welcome! Happy to assist.", "thanks")
    ]
    
    for user_input, response, context in interactions:
        interaction_id = learning_system.record_interaction(
            user_input=user_input,
            bot_response=response,
            context={"conversation_topic": context}
        )
        print(f"Recorded interaction: {user_input[:30]}...")
    
    # Test learned response
    test_query = "Hello there!"
    learned_response, confidence = learning_system.get_learned_response(test_query)
    print(f"\nTest query: {test_query}")
    print(f"Learned response: {learned_response}")
    print(f"Confidence: {confidence:.2f}")
    
    # Get statistics
    stats = learning_system.get_learning_statistics()
    print(f"\nLearning Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Export data
    export_data = learning_system.export_learning_data()
    print(f"\nExported data keys: {list(export_data.keys())}")