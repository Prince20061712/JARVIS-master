#!/usr/bin/env python3
"""
Advanced Pattern Recognition Module
Uses NLP, ML, and semantic analysis for understanding text patterns
"""

import re
import numpy as np
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
import hashlib

class QuestionType(Enum):
    FACTUAL = "factual"
    DEFINITION = "definition"
    EXPLANATORY = "explanatory"
    PROCEDURAL = "procedural"
    COMPARATIVE = "comparative"
    OPINION = "opinion"
    RHETORICAL = "rhetorical"
    HYPOTHETICAL = "hypothetical"
    CAUSAL = "causal"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    QUANTITATIVE = "quantitative"

class CommandType(Enum):
    ACTION = "action"
    QUERY = "query"
    CONTROL = "control"
    CONFIGURATION = "configuration"
    CREATION = "creation"
    DELETION = "deletion"
    MODIFICATION = "modification"
    NAVIGATION = "navigation"
    COMMUNICATION = "communication"
    SYSTEM = "system"

class IntentType(Enum):
    INFORMATION_SEEKING = "information_seeking"
    ACTION_REQUEST = "action_request"
    OPINION_SEEKING = "opinion_seeking"
    SOCIAL_INTERACTION = "social_interaction"
    PROBLEM_SOLVING = "problem_solving"
    DECISION_MAKING = "decision_making"
    ENTERTAINMENT = "entertainment"
    LEARNING = "learning"
    SHOPPING = "shopping"
    TRAVEL = "travel"

class EmotionType(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    CURIOUS = "curious"
    URGENT = "urgent"
    FORMAL = "formal"
    CASUAL = "casual"

@dataclass
class PatternMatch:
    pattern_type: str
    confidence: float
    matched_text: str
    extracted_entities: Dict[str, List[str]]
    semantic_analysis: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class TextAnalysis:
    text: str
    tokens: List[str]
    pos_tags: List[Tuple[str, str]]
    entities: Dict[str, List[str]]
    intent: IntentType
    emotion: EmotionType
    patterns: List[PatternMatch]
    complexity_score: float
    language_features: Dict[str, Any]

class AdvancedPatternRecognizer:
    def __init__(self, data_dir="pattern_data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize pattern databases
        self.pattern_database = self._load_pattern_database()
        self.learned_patterns = defaultdict(list)
        
        # NLP components
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            stop_words='english',
            max_features=5000
        )
        
        # Initialize pattern recognizers
        self._initialize_question_patterns()
        self._initialize_command_patterns()
        self._initialize_intent_patterns()
        self._initialize_entity_patterns()
        
        # Statistical tracking
        self.pattern_stats = defaultdict(int)
        self.confusion_matrix = defaultdict(lambda: defaultdict(int))
        
        # Load learned patterns if they exist
        self._load_learned_patterns()
    
    def _initialize_question_patterns(self):
        """Initialize comprehensive question patterns"""
        self.question_patterns = {
            QuestionType.FACTUAL: [
                r'^(?:what|who|where|when|which) (?:is|are|was|were|will be)\s+([^?]+)\??$',
                r'^(?:tell me|give me|show me) (?:information|details|facts) about\s+([^?]+)\??$',
                r'^(?:do you know|can you tell me) (?:about\s+)?([^?]+)\??$',
            ],
            QuestionType.DEFINITION: [
                r'^what (?:does|do) ([^?]+) (?:mean|refer to)\??$',
                r'^define\s+([^?]+)\??$',
                r'^what is (?:the )?definition of\s+([^?]+)\??$',
                r'^explain (?:the )?term\s+([^?]+)\??$',
            ],
            QuestionType.EXPLANATORY: [
                r'^how (?:does|do)\s+([^?]+) (?:work|function|operate)\??$',
                r'^why (?:does|do|is|are)\s+([^?]+)\??$',
                r'^explain (?:how|why)\s+([^?]+)\??$',
                r'^what causes\s+([^?]+)\??$',
            ],
            QuestionType.PROCEDURAL: [
                r'^how (?:to|can I|do I|should I)\s+([^?]+)\??$',
                r'^steps (?:to|for)\s+([^?]+)\??$',
                r'^procedure for\s+([^?]+)\??$',
                r'^tutorial (?:on|for)\s+([^?]+)\??$',
            ],
            QuestionType.COMPARATIVE: [
                r'^difference between\s+([^?]+) and\s+([^?]+)\??$',
                r'^compare\s+([^?]+) (?:with|to)\s+([^?]+)\??$',
                r'^(?:which|what) is better\s+([^?]+) or\s+([^?]+)\??$',
                r'^similarities between\s+([^?]+) and\s+([^?]+)\??$',
            ],
            QuestionType.OPINION: [
                r'^what (?:do you|does .+) think about\s+([^?]+)\??$',
                r'^opinion on\s+([^?]+)\??$',
                r'^(?:do you|does .+) like\s+([^?]+)\??$',
                r'^should I\s+([^?]+)\??$',
            ],
            QuestionType.HYPOTHETICAL: [
                r'^what if\s+([^?]+)\??$',
                r'^suppose\s+([^?]+)\??$',
                r'^imagine if\s+([^?]+)\??$',
                r'^hypothetically,\s+([^?]+)\??$',
            ],
            QuestionType.CAUSAL: [
                r'^what (?:would|will) happen if\s+([^?]+)\??$',
                r'^consequences of\s+([^?]+)\??$',
                r'^effect of\s+([^?]+) on\s+([^?]+)\??$',
            ],
            QuestionType.QUANTITATIVE: [
                r'^how (?:many|much|long|often|far)\s+([^?]+)\??$',
                r'^what (?:percentage|fraction|ratio) of\s+([^?]+)\??$',
                r'^size of\s+([^?]+)\??$',
            ]
        }
    
    def _initialize_command_patterns(self):
        """Initialize comprehensive command patterns"""
        self.command_patterns = {
            CommandType.ACTION: [
                r'^(?:open|close|start|stop|run|execute|launch)\s+([^?.!]+)[.!]?$',
                r'^(?:play|pause|resume|stop|skip)\s+(?:the\s+)?([^?.!]+)[.!]?$',
                r'^(?:search|find|look up|google)\s+(?:for\s+)?([^?.!]+)[.!]?$',
            ],
            CommandType.QUERY: [
                r'^(?:show|display|list|tell me)\s+(?:the\s+)?([^?.!]+)[.!]?$',
                r'^(?:what is|who is|where is|when is)\s+([^?.!]+)[.!]?$',
                r'^(?:give me|provide)\s+(?:information|details) (?:about|on)\s+([^?.!]+)[.!]?$',
            ],
            CommandType.CONTROL: [
                r'^(?:increase|decrease|set|adjust)\s+(?:the\s+)?([^?.!]+)(?:\s+to\s+([^?.!]+))?[.!]?$',
                r'^(?:turn on|turn off|enable|disable|toggle)\s+(?:the\s+)?([^?.!]+)[.!]?$',
                r'^(?:volume|brightness|temperature|speed)\s+(?:up|down|to)\s+([^?.!]+)[.!]?$',
            ],
            CommandType.CREATION: [
                r'^(?:create|make|build|generate)\s+(?:a\s+)?([^?.!]+)[.!]?$',
                r'^(?:write|compose|draft)\s+(?:a\s+)?([^?.!]+)[.!]?$',
                r'^(?:schedule|plan|organize)\s+(?:a\s+)?([^?.!]+)[.!]?$',
            ],
            CommandType.COMMUNICATION: [
                r'^(?:send|email|message|text|call)\s+(?:a\s+)?([^?.!]+)(?:\s+to\s+([^?.!]+))?[.!]?$',
                r'^(?:reply|respond|answer)\s+(?:to\s+)?([^?.!]+)[.!]?$',
                r'^(?:share|forward)\s+(?:the\s+)?([^?.!]+)[.!]?$',
            ],
            CommandType.NAVIGATION: [
                r'^(?:go to|navigate to|open)\s+(?:the\s+)?([^?.!]+)[.!]?$',
                r'^(?:visit|browse|explore)\s+(?:the\s+)?([^?.!]+)[.!]?$',
                r'^(?:back|forward|home|refresh|reload)[.!]?$',
            ]
        }
    
    def _initialize_intent_patterns(self):
        """Initialize intent recognition patterns"""
        self.intent_patterns = {
            IntentType.INFORMATION_SEEKING: [
                "what", "who", "where", "when", "why", "how",
                "explain", "tell me about", "information on",
                "details about", "facts about"
            ],
            IntentType.ACTION_REQUEST: [
                "open", "close", "play", "stop", "search",
                "find", "start", "run", "execute", "launch"
            ],
            IntentType.OPINION_SEEKING: [
                "what do you think", "opinion on", "do you like",
                "should I", "would you recommend", "is it good"
            ],
            IntentType.SOCIAL_INTERACTION: [
                "hello", "hi", "hey", "how are you", "good morning",
                "good night", "thank you", "thanks", "you're welcome"
            ],
            IntentType.PROBLEM_SOLVING: [
                "how to fix", "troubleshoot", "error with",
                "problem with", "issue with", "help with"
            ],
            IntentType.LEARNING: [
                "learn about", "study", "teach me", "tutorial",
                "course on", "education about"
            ],
            IntentType.ENTERTAINMENT: [
                "joke", "fun fact", "entertain me", "play music",
                "watch movie", "game", "trivia"
            ]
        }
    
    def _initialize_entity_patterns(self):
        """Initialize entity extraction patterns"""
        self.entity_patterns = {
            "PERSON": [
                r'(?:my|our|your)\s+(?:friend|colleague|boss|teacher|professor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'(?:call|email|message|text)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'^(?:I am|my name is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            ],
            "LOCATION": [
                r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'at\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            ],
            "DATE": [
                r'on\s+(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December))',
                r'(\d{4}-\d{2}-\d{2})',
                r'(?:today|tomorrow|yesterday|next week|last week|this month)',
            ],
            "TIME": [
                r'at\s+(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)',
                r'(\d{1,2}\s*(?:o\'clock|oclock))',
                r'(?:in the )?(morning|afternoon|evening|night)',
            ],
            "NUMBER": [
                r'(\d+(?:\.\d+)?)',
                r'(?:about|approximately|around)\s+(\d+)',
            ],
            "ORGANIZATION": [
                r'(?:at|from|to)\s+([A-Z][a-z]+\s+(?:University|College|School|Institute|Company|Corporation|LLC|Inc))',
            ],
            "PRODUCT": [
                r'(?:buy|purchase|order)\s+(?:a\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'(?:iPhone|MacBook|Windows|Android)\s+([A-Za-z0-9]+)',
            ]
        }
    
    def analyze_text(self, text: str) -> TextAnalysis:
        """Comprehensive text analysis with multiple dimensions"""
        text_lower = text.lower().strip()
        
        # Tokenization and basic analysis
        tokens = self._tokenize(text)
        
        # Intent detection
        intent = self._detect_intent(text_lower)
        
        # Emotion detection
        emotion = self._detect_emotion(text_lower)
        
        # Entity extraction
        entities = self._extract_entities_advanced(text)
        
        # Pattern recognition
        patterns = self._recognize_all_patterns(text)
        
        # POS tagging (simplified)
        pos_tags = self._simplified_pos_tagging(tokens)
        
        # Complexity analysis
        complexity_score = self._calculate_complexity(text, tokens)
        
        # Language features
        language_features = self._analyze_language_features(text)
        
        return TextAnalysis(
            text=text,
            tokens=tokens,
            pos_tags=pos_tags,
            entities=entities,
            intent=intent,
            emotion=emotion,
            patterns=patterns,
            complexity_score=complexity_score,
            language_features=language_features
        )
    
    def _recognize_all_patterns(self, text: str) -> List[PatternMatch]:
        """Recognize all patterns in text"""
        patterns = []
        text_lower = text.lower().strip()
        
        # Question patterns
        question_match = self._recognize_question_type_advanced(text_lower)
        if question_match:
            patterns.append(question_match)
        
        # Command patterns
        command_match = self._recognize_command_type_advanced(text_lower)
        if command_match:
            patterns.append(command_match)
        
        # Intent patterns
        intent_match = self._recognize_intent_pattern(text_lower)
        if intent_match:
            patterns.append(intent_match)
        
        # Learned patterns
        learned_matches = self._match_learned_patterns(text_lower)
        patterns.extend(learned_matches)
        
        return patterns
    
    def _recognize_question_type_advanced(self, text: str) -> Optional[PatternMatch]:
        """Advanced question type recognition"""
        if not text.endswith('?'):
            return None
        
        text_without_punctuation = text.rstrip('?').strip()
        
        best_match = None
        highest_confidence = 0
        
        for q_type, patterns in self.question_patterns.items():
            for pattern in patterns:
                match = re.match(pattern, text_without_punctuation)
                if match:
                    confidence = self._calculate_pattern_confidence(pattern, text_without_punctuation)
                    
                    if confidence > highest_confidence:
                        highest_confidence = confidence
                        
                        # Extract entities from the match
                        entities = {}
                        for i, group in enumerate(match.groups(), 1):
                            if group:
                                # Analyze the group for specific entities
                                group_entities = self._extract_entities_from_text(group)
                                for entity_type, entity_list in group_entities.items():
                                    if entity_type not in entities:
                                        entities[entity_type] = []
                                    entities[entity_type].extend(entity_list)
                        
                        best_match = PatternMatch(
                            pattern_type=f"question_{q_type.value}",
                            confidence=confidence,
                            matched_text=text_without_punctuation,
                            extracted_entities=entities,
                            semantic_analysis={
                                "question_type": q_type.value,
                                "groups": match.groups(),
                                "pattern": pattern
                            },
                            metadata={
                                "is_rhetorical": self._is_rhetorical_question(text),
                                "requires_fact": q_type in [QuestionType.FACTUAL, QuestionType.DEFINITION],
                                "requires_explanation": q_type in [QuestionType.EXPLANATORY, QuestionType.PROCEDURAL]
                            }
                        )
        
        return best_match
    
    def _recognize_command_type_advanced(self, text: str) -> Optional[PatternMatch]:
        """Advanced command type recognition"""
        text_clean = text.rstrip('.!?').strip()
        
        best_match = None
        highest_confidence = 0
        
        for cmd_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.match(pattern, text_clean)
                if match:
                    confidence = self._calculate_pattern_confidence(pattern, text_clean)
                    
                    if confidence > highest_confidence:
                        highest_confidence = confidence
                        
                        # Extract parameters
                        params = {}
                        groups = match.groups()
                        if groups:
                            # First group is usually the main object
                            params["object"] = groups[0]
                            if len(groups) > 1 and groups[1]:
                                params["target"] = groups[1]
                        
                        # Extract entities from parameters
                        entities = {}
                        for param in params.values():
                            param_entities = self._extract_entities_from_text(param)
                            for entity_type, entity_list in param_entities.items():
                                if entity_type not in entities:
                                    entities[entity_type] = []
                                entities[entity_type].extend(entity_list)
                        
                        best_match = PatternMatch(
                            pattern_type=f"command_{cmd_type.value}",
                            confidence=confidence,
                            matched_text=text_clean,
                            extracted_entities=entities,
                            semantic_analysis={
                                "command_type": cmd_type.value,
                                "parameters": params,
                                "pattern": pattern
                            },
                            metadata={
                                "is_actionable": cmd_type in [CommandType.ACTION, CommandType.CONTROL],
                                "requires_response": cmd_type in [CommandType.QUERY, CommandType.CREATION],
                                "is_destructive": cmd_type == CommandType.DELETION
                            }
                        )
        
        return best_match
    
    def _recognize_intent_pattern(self, text: str) -> Optional[PatternMatch]:
        """Recognize intent patterns"""
        best_intent = None
        highest_score = 0
        
        for intent_type, keywords in self.intent_patterns.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in text:
                    score += len(keyword.split()) * 2  # Weight by word count
                    matched_keywords.append(keyword)
            
            # Context-based scoring
            context_score = self._calculate_context_score(text, intent_type)
            score += context_score
            
            if score > highest_score and score > 5:  # Threshold
                highest_score = score
                best_intent = intent_type
        
        if best_intent:
            confidence = min(1.0, highest_score / 20.0)  # Normalize confidence
            
            return PatternMatch(
                pattern_type=f"intent_{best_intent.value}",
                confidence=confidence,
                matched_text=text,
                extracted_entities={},
                semantic_analysis={
                    "intent_type": best_intent.value,
                    "score": highest_score
                },
                metadata={
                    "requires_action": best_intent in [IntentType.ACTION_REQUEST, IntentType.PROBLEM_SOLVING],
                    "is_social": best_intent == IntentType.SOCIAL_INTERACTION,
                    "is_informational": best_intent == IntentType.INFORMATION_SEEKING
                }
            )
        
        return None
    
    def _calculate_pattern_confidence(self, pattern: str, text: str) -> float:
        """Calculate confidence score for pattern match"""
        # Base confidence from regex match
        confidence = 0.7
        
        # Length factor (longer matches are better)
        pattern_complexity = len(pattern.replace('(', '').replace(')', '').split())
        text_length = len(text.split())
        
        if text_length >= pattern_complexity:
            confidence += 0.2
        
        # Specificity factor (more specific patterns get higher confidence)
        specificity_score = pattern.count('(') / max(1, len(pattern.split()))
        confidence += specificity_score * 0.1
        
        # Learn from historical accuracy
        pattern_hash = hashlib.md5(pattern.encode()).hexdigest()[:8]
        if pattern_hash in self.pattern_stats:
            historical_accuracy = self.pattern_stats[pattern_hash] / 100.0
            confidence = (confidence + historical_accuracy) / 2
        
        return min(1.0, confidence)
    
    def _detect_intent(self, text: str) -> IntentType:
        """Detect primary intent"""
        text_lower = text.lower()
        
        # Check for social intent first
        social_keywords = ["hello", "hi", "hey", "good morning", "good night", "thank you"]
        if any(keyword in text_lower for keyword in social_keywords):
            return IntentType.SOCIAL_INTERACTION
        
        # Check for question intent
        if text_lower.endswith('?'):
            # Analyze question type to determine intent
            if "how to" in text_lower or "steps" in text_lower:
                return IntentType.PROBLEM_SOLVING
            elif "what do you think" in text_lower or "opinion" in text_lower:
                return IntentType.OPINION_SEEKING
            else:
                return IntentType.INFORMATION_SEEKING
        
        # Check for command/action intent
        action_keywords = ["open", "close", "play", "stop", "search", "find"]
        if any(keyword in text_lower for keyword in action_keywords):
            return IntentType.ACTION_REQUEST
        
        # Check for entertainment intent
        entertainment_keywords = ["joke", "fun fact", "entertain", "music", "movie"]
        if any(keyword in text_lower for keyword in entertainment_keywords):
            return IntentType.ENTERTAINMENT
        
        # Default to information seeking
        return IntentType.INFORMATION_SEEKING
    
    def _detect_emotion(self, text: str) -> EmotionType:
        """Detect emotion in text"""
        text_lower = text.lower()
        
        emotion_indicators = {
            EmotionType.POSITIVE: [
                "great", "excellent", "wonderful", "awesome", "happy",
                "good", "nice", "perfect", "amazing", "fantastic"
            ],
            EmotionType.NEGATIVE: [
                "bad", "terrible", "awful", "horrible", "sad",
                "angry", "frustrated", "upset", "disappointed", "hate"
            ],
            EmotionType.EXCITED: [
                "exciting", "can't wait", "looking forward", "wow",
                "awesome", "thrilled", "excited"
            ],
            EmotionType.FRUSTRATED: [
                "frustrating", "annoying", "irritating", "problem",
                "issue", "error", "won't work", "doesn't work"
            ],
            EmotionType.URGENT: [
                "urgent", "immediately", "now", "asap", "quick",
                "fast", "hurry", "emergency"
            ],
            EmotionType.CURIOUS: [
                "curious", "wonder", "interesting", "fascinating",
                "intriguing", "want to know", "tell me more"
            ]
        }
        
        emotion_scores = defaultdict(int)
        for emotion, indicators in emotion_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    emotion_scores[emotion] += 1
        
        if emotion_scores:
            # Find emotion with highest score
            dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            return dominant_emotion
        
        # Check for formal vs casual
        formal_indicators = ["please", "could you", "would you", "kindly"]
        casual_indicators = ["hey", "yo", "what's up", "lol", "haha"]
        
        if any(indicator in text_lower for indicator in formal_indicators):
            return EmotionType.FORMAL
        elif any(indicator in text_lower for indicator in casual_indicators):
            return EmotionType.CASUAL
        
        return EmotionType.NEUTRAL
    
    def _extract_entities_advanced(self, text: str) -> Dict[str, List[str]]:
        """Advanced entity extraction"""
        entities = defaultdict(list)
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    for group in match.groups():
                        if group:
                            entities[entity_type].append(group)
        
        # Additional entity extraction using learned patterns
        learned_entities = self._extract_learned_entities(text)
        for entity_type, entity_list in learned_entities.items():
            entities[entity_type].extend(entity_list)
        
        # Remove duplicates
        for entity_type in entities:
            entities[entity_type] = list(set(entities[entity_type]))
        
        return dict(entities)
    
    def _extract_entities_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from a piece of text"""
        return self._extract_entities_advanced(text)
    
    def _extract_learned_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using learned patterns"""
        # This would integrate with the learning system
        # For now, return empty dict
        return {}
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Simple tokenization
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def _simplified_pos_tagging(self, tokens: List[str]) -> List[Tuple[str, str]]:
        """Simplified POS tagging"""
        pos_tags = []
        
        # Basic POS tagging rules
        pos_rules = {
            "NOUN": r'.*(tion|ment|ness|ity|ance|ence)$',
            "VERB": r'^(is|am|are|was|were|be|been|being|have|has|had|do|does|did|can|could|will|would|shall|should|may|might|must)$',
            "ADJ": r'.*(able|ible|ful|ic|ical|ive|ous|ish|y)$',
            "ADV": r'.*(ly|wise|ward|wards)$',
            "PRON": r'^(I|you|he|she|it|we|they|me|him|her|us|them|my|your|his|her|its|our|their)$'
        }
        
        for token in tokens:
            pos = "OTHER"
            for pos_type, pattern in pos_rules.items():
                if re.match(pattern, token, re.IGNORECASE):
                    pos = pos_type
                    break
            
            pos_tags.append((token, pos))
        
        return pos_tags
    
    def _calculate_complexity(self, text: str, tokens: List[str]) -> float:
        """Calculate text complexity score"""
        if not tokens:
            return 0.0
        
        # Sentence length complexity
        sentence_length = len(tokens)
        length_score = min(1.0, sentence_length / 30.0)
        
        # Vocabulary complexity (unique words ratio)
        unique_words = len(set(tokens))
        vocab_score = unique_words / len(tokens) if tokens else 0
        
        # Question complexity
        question_score = 1.0 if text.endswith('?') else 0.0
        
        # Command complexity
        command_keywords = ["open", "close", "search", "find", "create", "make"]
        command_score = 1.0 if any(keyword in text.lower() for keyword in command_keywords) else 0.0
        
        # Combined complexity
        complexity = (length_score * 0.3 + vocab_score * 0.3 + 
                     question_score * 0.2 + command_score * 0.2)
        
        return min(1.0, complexity)
    
    def _analyze_language_features(self, text: str) -> Dict[str, Any]:
        """Analyze language features"""
        text_lower = text.lower()
        
        features = {
            "has_question_mark": text.endswith('?'),
            "has_exclamation": text.endswith('!'),
            "has_period": text.endswith('.'),
            "word_count": len(text.split()),
            "sentence_count": len(re.split(r'[.!?]+', text)),
            "contains_numbers": bool(re.search(r'\d', text)),
            "contains_urls": bool(re.search(r'https?://\S+', text)),
            "contains_emails": bool(re.search(r'\S+@\S+\.\S+', text)),
            "contains_hashtags": bool(re.search(r'#\w+', text)),
            "contains_mentions": bool(re.search(r'@\w+', text)),
        }
        
        # Readability metrics (simplified)
        words = text.split()
        syllables = sum(self._count_syllables(word) for word in words)
        sentences = max(1, features["sentence_count"])
        
        if words:
            features["average_word_length"] = sum(len(word) for word in words) / len(words)
            features["average_syllables_per_word"] = syllables / len(words)
            
            # Flesch Reading Ease (simplified)
            flesch_score = 206.835 - 1.015 * (len(words) / sentences) - 84.6 * (syllables / len(words))
            features["readability_score"] = max(0, min(100, flesch_score))
        
        return features
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)"""
        word = word.lower()
        if len(word) <= 3:
            return 1
        
        count = 0
        vowels = "aeiouy"
        if word[0] in vowels:
            count += 1
        
        for i in range(1, len(word)):
            if word[i] in vowels and word[i-1] not in vowels:
                count += 1
        
        if word.endswith("e"):
            count -= 1
        
        if count == 0:
            count = 1
        
        return count
    
    def _is_rhetorical_question(self, text: str) -> bool:
        """Check if question is rhetorical"""
        rhetorical_indicators = [
            "isn't it", "don't you think", "aren't we", "shouldn't we",
            "why bother", "who cares", "what's the point"
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in rhetorical_indicators)
    
    def _calculate_context_score(self, text: str, intent_type: IntentType) -> float:
        """Calculate context-based score for intent"""
        # This would integrate with conversation context
        # For now, return base score
        return 0.0
    
    def _match_learned_patterns(self, text: str) -> List[PatternMatch]:
        """Match against learned patterns"""
        # This would integrate with the learning system
        return []
    
    def learn_pattern(self, pattern: str, pattern_type: str, example: str, confidence: float = 0.8):
        """Learn a new pattern from example"""
        pattern_hash = hashlib.md5(pattern.encode()).hexdigest()[:8]
        
        self.learned_patterns[pattern_type].append({
            "pattern": pattern,
            "pattern_hash": pattern_hash,
            "example": example,
            "confidence": confidence,
            "learned_at": datetime.datetime.now().isoformat()
        })
        
        # Update pattern database
        self._save_learned_patterns()
    
    def _load_pattern_database(self) -> Dict:
        """Load pattern database from file"""
        db_file = os.path.join(self.data_dir, "pattern_database.json")
        try:
            with open(db_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_learned_patterns(self):
        """Save learned patterns to file"""
        learned_file = os.path.join(self.data_dir, "learned_patterns.json")
        with open(learned_file, 'w') as f:
            json.dump(dict(self.learned_patterns), f, indent=2)
    
    def _load_learned_patterns(self):
        """Load learned patterns from file"""
        learned_file = os.path.join(self.data_dir, "learned_patterns.json")
        try:
            with open(learned_file, 'r') as f:
                self.learned_patterns = defaultdict(list, json.load(f))
        except FileNotFoundError:
            pass
    
    def update_pattern_accuracy(self, pattern_hash: str, was_correct: bool):
        """Update pattern accuracy statistics"""
        if was_correct:
            self.pattern_stats[pattern_hash] = min(100, self.pattern_stats.get(pattern_hash, 0) + 1)
        else:
            self.pattern_stats[pattern_hash] = max(0, self.pattern_stats.get(pattern_hash, 0) - 1)
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get pattern recognition statistics"""
        total_patterns = sum(len(patterns) for patterns in self.question_patterns.values()) + \
                        sum(len(patterns) for patterns in self.command_patterns.values())
        
        return {
            "total_predefined_patterns": total_patterns,
            "total_learned_patterns": sum(len(patterns) for patterns in self.learned_patterns.values()),
            "pattern_types": {
                "question_types": len(self.question_patterns),
                "command_types": len(self.command_patterns),
                "intent_types": len(self.intent_patterns),
                "entity_types": len(self.entity_patterns)
            },
            "pattern_accuracy": dict(self.pattern_stats),
            "learned_patterns_by_type": {k: len(v) for k, v in self.learned_patterns.items()}
        }
    
    def export_patterns(self) -> Dict[str, Any]:
        """Export all patterns for analysis"""
        return {
            "question_patterns": {
                qtype.value: patterns 
                for qtype, patterns in self.question_patterns.items()
            },
            "command_patterns": {
                ctype.value: patterns 
                for ctype, patterns in self.command_patterns.items()
            },
            "intent_patterns": {
                itype.value: keywords 
                for itype, keywords in self.intent_patterns.items()
            },
            "entity_patterns": self.entity_patterns,
            "learned_patterns": dict(self.learned_patterns),
            "statistics": self.get_pattern_statistics()
        }


# Example usage
if __name__ == "__main__":
    print("Testing Advanced Pattern Recognizer...")
    
    recognizer = AdvancedPatternRecognizer()
    
    test_texts = [
        "What is artificial intelligence and how does it work?",
        "Open Chrome browser and search for machine learning tutorials",
        "Hello! How are you doing today?",
        "Can you explain quantum computing in simple terms?",
        "I need to fix my printer that won't connect to WiFi",
        "Create a new document and write a report about climate change",
        "What's the difference between machine learning and deep learning?",
    ]
    
    for text in test_texts:
        print(f"\n{'='*60}")
        print(f"Analyzing: {text}")
        print(f"{'='*60}")
        
        analysis = recognizer.analyze_text(text)
        
        print(f"Intent: {analysis.intent.value}")
        print(f"Emotion: {analysis.emotion.value}")
        print(f"Complexity Score: {analysis.complexity_score:.2f}")
        
        if analysis.patterns:
            print(f"Patterns detected:")
            for pattern in analysis.patterns:
                print(f"  - {pattern.pattern_type} (confidence: {pattern.confidence:.2f})")
        
        if analysis.entities:
            print(f"Entities:")
            for entity_type, entities in analysis.entities.items():
                if entities:
                    print(f"  {entity_type}: {', '.join(entities)}")
        
        # Language features
        print(f"Word Count: {analysis.language_features['word_count']}")
        if 'readability_score' in analysis.language_features:
            print(f"Readability: {analysis.language_features['readability_score']:.1f}")
    
    # Get statistics
    stats = recognizer.get_pattern_statistics()
    print(f"\nPattern Statistics:")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")