#!/usr/bin/env python3
"""
Learning System Module
Learns from interactions and improves responses
"""

import json
import datetime
import re
from collections import defaultdict
import numpy as np

class LearningSystem:
    def __init__(self, learning_file="jarvis_learning.json"):
        self.learning_file = learning_file
        self.response_patterns = defaultdict(list)
        self.corrections = []
        self.feedback_history = []
        self.interaction_stats = {
            "total_interactions": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "user_corrections": 0
        }
        self.load_learning()
    
    def load_learning(self):
        """Load learned patterns"""
        try:
            with open(self.learning_file, 'r') as f:
                data = json.load(f)
                self.response_patterns = defaultdict(list, data.get("response_patterns", {}))
                self.corrections = data.get("corrections", [])
                self.feedback_history = data.get("feedback_history", [])
                self.interaction_stats = data.get("interaction_stats", self.interaction_stats)
        except (FileNotFoundError, json.JSONDecodeError):
            self.save_learning()
    
    def save_learning(self):
        """Save learned patterns"""
        data = {
            "response_patterns": dict(self.response_patterns),
            "corrections": self.corrections,
            "feedback_history": self.feedback_history,
            "interaction_stats": self.interaction_stats,
            "last_updated": datetime.datetime.now().isoformat()
        }
        with open(self.learning_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def learn_response(self, user_input, correct_response):
        """Learn a new response pattern"""
        # Extract patterns from input
        patterns = self._extract_patterns(user_input)
        
        for pattern in patterns:
            if correct_response not in self.response_patterns[pattern]:
                self.response_patterns[pattern].append(correct_response)
        
        self.interaction_stats["successful_responses"] += 1
        self.interaction_stats["total_interactions"] += 1
        self.save_learning()
        return True
    
    def _extract_patterns(self, text):
        """Extract patterns from text"""
        patterns = []
        text_lower = text.lower()
        
        # Extract question patterns
        if text_lower.endswith('?'):
            # Remove question words for pattern matching
            question_words = ["what", "who", "where", "when", "why", "how", "which"]
            words = text_lower.rstrip('?').split()
            if words and words[0] in question_words:
                patterns.append(f"{words[0]}_question")
                if len(words) > 1:
                    patterns.append(f"{words[0]}_{words[1]}")
        
        # Extract command patterns
        command_keywords = ["play", "open", "close", "search", "find", "get", 
                          "show", "tell", "set", "create", "send"]
        for keyword in command_keywords:
            if keyword in text_lower:
                patterns.append(f"command_{keyword}")
                break
        
        # Extract emotional patterns
        emotional_keywords = {
            "happy": ["happy", "good", "great", "excited", "wonderful"],
            "sad": ["sad", "bad", "terrible", "awful", "upset"],
            "angry": ["angry", "mad", "frustrated", "annoyed"],
            "tired": ["tired", "exhausted", "sleepy", "fatigued"]
        }
        
        for emotion, keywords in emotional_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                patterns.append(f"emotion_{emotion}")
                break
        
        # Add the full lowercase text as a pattern
        patterns.append(text_lower)
        
        return patterns
    
    def get_learned_response(self, user_input):
        """Get response from learned patterns"""
        patterns = self._extract_patterns(user_input)
        
        # Try exact pattern match
        for pattern in patterns:
            if pattern in self.response_patterns and self.response_patterns[pattern]:
                return np.random.choice(self.response_patterns[pattern])
        
        # Try partial pattern match
        for stored_pattern, responses in self.response_patterns.items():
            for pattern in patterns:
                if (stored_pattern in pattern or pattern in stored_pattern) and responses:
                    return np.random.choice(responses)
        
        return None
    
    def record_correction(self, user_input, wrong_response, correct_response):
        """Record a correction from user"""
        correction = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_input": user_input,
            "wrong_response": wrong_response,
            "correct_response": correct_response,
            "learned": False
        }
        
        self.corrections.append(correction)
        self.interaction_stats["user_corrections"] += 1
        
        # Auto-learn from correction
        self.learn_response(user_input, correct_response)
        correction["learned"] = True
        
        self.save_learning()
        return correction
    
    def record_feedback(self, user_input, jarvis_response, feedback_score):
        """Record user feedback (1-5 scale)"""
        feedback = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_input": user_input,
            "jarvis_response": jarvis_response,
            "feedback_score": feedback_score
        }
        
        self.feedback_history.append(feedback)
        
        # Update stats based on feedback
        if feedback_score >= 3:
            self.interaction_stats["successful_responses"] += 1
            # Learn from positive feedback
            self.learn_response(user_input, jarvis_response)
        else:
            self.interaction_stats["failed_responses"] += 1
        
        self.interaction_stats["total_interactions"] += 1
        self.save_learning()
        return feedback
    
    def get_learning_stats(self):
        """Get learning statistics"""
        total_patterns = sum(len(responses) for responses in self.response_patterns.values())
        
        return {
            "total_learned_patterns": total_patterns,
            "unique_patterns": len(self.response_patterns),
            "total_corrections": len(self.corrections),
            "total_feedback": len(self.feedback_history),
            **self.interaction_stats,
            "success_rate": (
                (self.interaction_stats["successful_responses"] / 
                 max(1, self.interaction_stats["total_interactions"])) * 100
            )
        }