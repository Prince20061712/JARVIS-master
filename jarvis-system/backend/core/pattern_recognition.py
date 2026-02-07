#!/usr/bin/env python3
"""
Pattern Recognition Module
Understands question types and command patterns
"""

import re
from enum import Enum

class QuestionType(Enum):
    FACTUAL = "factual"
    EXPLANATORY = "explanatory"
    PROCEDURAL = "procedural"
    COMPARATIVE = "comparative"
    OPINION = "opinion"
    RHETORICAL = "rhetorical"

class CommandType(Enum):
    ACTION = "action"
    QUERY = "query"
    CONTROL = "control"
    CONFIGURATION = "configuration"
    CREATION = "creation"

class PatternRecognizer:
    def __init__(self):
        # Question patterns
        self.question_patterns = {
            QuestionType.FACTUAL: [
                r"^what (is|are) (.+)\??$",
                r"^who (is|are) (.+)\??$",
                r"^where (is|are) (.+)\??$",
                r"^when (is|are) (.+)\??$"
            ],
            QuestionType.EXPLANATORY: [
                r"^how (does|do) (.+) work\??$",
                r"^explain (.+)$",
                r"^why (.+)\??$"
            ],
            QuestionType.PROCEDURAL: [
                r"^how (to|can I) (.+)\??$",
                r"^steps to (.+)$",
                r"^process of (.+)$"
            ],
            QuestionType.COMPARATIVE: [
                r"^difference between (.+) and (.+)$",
                r"^compare (.+) with (.+)$",
                r"^which is better (.+) or (.+)\??$"
            ],
            QuestionType.OPINION: [
                r"^what do you think about (.+)\??$",
                r"^opinion on (.+)$",
                r"^should I (.+)\??$"
            ],
            QuestionType.RHETORICAL: [
                r"^isn't it (.+)\??$",
                r"^don't you think (.+)\??$",
                r"^why bother (.+)\??$"
            ]
        }
        
        # Command patterns
        self.command_patterns = {
            CommandType.ACTION: [
                r"^(open|close|start|stop|run|execute) (.+)$",
                r"^(play|pause|stop) (.+)$",
                r"^(search|find|look up) (.+)$"
            ],
            CommandType.QUERY: [
                r"^(show|display|tell me) (.+)$",
                r"^(what|who|where|when|why|how) (.+)$"
            ],
            CommandType.CONTROL: [
                r"^(increase|decrease|set|adjust) (.+)$",
                r"^(turn on|turn off|enable|disable) (.+)$",
                r"^(volume|brightness|temperature) (.+)$"
            ],
            CommandType.CONFIGURATION: [
                r"^(configure|setup|install) (.+)$",
                r"^(change|modify) (.+) settings$",
                r"^(preference|option) (.+)$"
            ],
            CommandType.CREATION: [
                r"^(create|make|build) (.+)$",
                r"^(write|compose) (.+)$",
                r"^(schedule|plan) (.+)$"
            ]
        }
        
        # Intent keywords
        self.intent_keywords = {
            "information": ["what", "who", "where", "when", "why", "how", "explain", "tell me"],
            "action": ["open", "close", "play", "stop", "search", "find"],
            "control": ["increase", "decrease", "set", "adjust", "turn on", "turn off"],
            "communication": ["email", "message", "call", "send", "text"],
            "entertainment": ["music", "video", "movie", "game", "joke"],
            "productivity": ["reminder", "note", "schedule", "task", "todo"]
        }
    
    def recognize_question_type(self, text):
        """Recognize the type of question"""
        text_lower = text.lower().strip()
        
        for q_type, patterns in self.question_patterns.items():
            for pattern in patterns:
                match = re.match(pattern, text_lower)
                if match:
                    return {
                        "type": q_type,
                        "type_name": q_type.value,
                        "matched_pattern": pattern,
                        "extracted_groups": match.groups()
                    }
        
        # Check if it's a question at all
        if text_lower.endswith('?'):
            return {
                "type": QuestionType.FACTUAL,
                "type_name": "factual",
                "matched_pattern": None,
                "extracted_groups": (text_lower.rstrip('?'),)
            }
        
        return None
    
    def recognize_command_type(self, text):
        """Recognize the type of command"""
        text_lower = text.lower().strip()
        
        for cmd_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.match(pattern, text_lower)
                if match:
                    return {
                        "type": cmd_type,
                        "type_name": cmd_type.value,
                        "matched_pattern": pattern,
                        "extracted_groups": match.groups()
                    }
        
        # Fallback to keyword-based recognition
        intent = self._detect_intent(text_lower)
        return {
            "type": CommandType.ACTION if intent else CommandType.QUERY,
            "type_name": "action" if intent else "query",
            "matched_pattern": None,
            "extracted_groups": (text_lower,),
            "detected_intent": intent
        }
    
    def _detect_intent(self, text):
        """Detect user intent from keywords"""
        text_lower = text.lower()
        
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return intent
        
        return "unknown"
    
    def extract_entities(self, text):
        """Extract entities from text"""
        entities = {
            "time_entities": self._extract_time_entities(text),
            "date_entities": self._extract_date_entities(text),
            "location_entities": self._extract_location_entities(text),
            "person_entities": self._extract_person_entities(text),
            "number_entities": self._extract_number_entities(text)
        }
        return entities
    
    def _extract_time_entities(self, text):
        """Extract time-related entities"""
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)',
            r'(\d{1,2}\s*(?:o\'clock|oclock))',
            r'(morning|afternoon|evening|night|noon|midnight)'
        ]
        
        entities = []
        for pattern in time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))
    
    def _extract_date_entities(self, text):
        """Extract date-related entities"""
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(today|tomorrow|yesterday|next week|last week)',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)'
        ]
        
        entities = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))
    
    def _extract_location_entities(self, text):
        """Extract location entities"""
        # Simple location words
        location_keywords = [
            "home", "office", "work", "school", "store", "market",
            "bank", "park", "restaurant", "cafe", "hotel", "airport"
        ]
        
        entities = []
        for keyword in location_keywords:
            if keyword in text.lower():
                entities.append(keyword)
        
        return entities
    
    def _extract_person_entities(self, text):
        """Extract person entities"""
        # This is a simple implementation
        # In production, you'd use NER
        person_patterns = [
            r'(?:my|our)\s+(\w+)',
            r'(?:call|email|message)\s+(\w+)'
        ]
        
        entities = []
        for pattern in person_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))
    
    def _extract_number_entities(self, text):
        """Extract number entities"""
        number_patterns = [
            r'\b\d+\b',
            r'\b(?:one|two|three|four|five|six|seven|eight|nine|ten)\b'
        ]
        
        entities = []
        for pattern in number_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))
    
    def analyze_text(self, text):
        """Comprehensive text analysis"""
        analysis = {
            "is_question": text.strip().endswith('?'),
            "question_analysis": self.recognize_question_type(text),
            "command_analysis": self.recognize_command_type(text),
            "entities": self.extract_entities(text),
            "word_count": len(text.split()),
            "contains_emotion": self._detect_emotion(text)
        }
        
        return analysis
    
    def _detect_emotion(self, text):
        """Detect emotional content"""
        emotion_keywords = {
            "positive": ["good", "great", "happy", "excited", "wonderful", "awesome"],
            "negative": ["bad", "terrible", "sad", "angry", "frustrated", "upset"],
            "urgent": ["urgent", "immediately", "now", "quick", "fast", "hurry"]
        }
        
        text_lower = text.lower()
        emotions = []
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                emotions.append(emotion)
        
        return emotions if emotions else ["neutral"]