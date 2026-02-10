#!/usr/bin/env python3
"""
Enhanced Human-Like Emotion Detection Module
Simulates how humans understand emotions through multiple channels
"""

import random
import re
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
from typing import Dict, List, Tuple, Optional
import json

class EmotionalState(Enum):
    HAPPY = "happy"
    SAD = "sad" 
    ANGRY = "angry"
    STRESSED = "stressed"
    ANXIOUS = "anxious"
    TIRED = "tired"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    CONTENT = "content"
    NEUTRAL = "neutral"
    MIXED = "mixed"  # For complex emotional states

class EmotionalContext:
    """Tracks contextual information for better emotion understanding"""
    def __init__(self):
        self.recent_topics = deque(maxlen=10)
        self.recent_interactions = deque(maxlen=20)
        self.time_of_day = None
        self.day_of_week = None
        self.seasonal_context = None  # Holiday season, weekend, etc.
        self.conversation_depth = 0
        self.urgency_level = 0
        
    def update_context(self, text: str, timestamp: datetime):
        """Update contextual understanding"""
        self.time_of_day = timestamp.hour
        self.day_of_week = timestamp.weekday()
        
        # Detect topics
        topics = self._extract_topics(text)
        self.recent_topics.extend(topics)
        
        # Update conversation depth
        if "I feel" in text or "I am" in text.lower():
            self.conversation_depth += 1
            
        # Detect urgency
        urgency_indicators = ["now", "urgent", "asap", "immediately", "deadline"]
        if any(indicator in text.lower() for indicator in urgency_indicators):
            self.urgency_level = min(10, self.urgency_level + 2)
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract potential conversation topics"""
        topics = []
        # Simple topic extraction
        topic_keywords = {
            "work": ["work", "job", "office", "boss", "colleague"],
            "family": ["family", "mom", "dad", "children", "kids", "partner"],
            "health": ["health", "doctor", "hospital", "pain", "sick"],
            "finance": ["money", "bill", "price", "cost", "expensive"],
            "social": ["friend", "party", "social", "date", "relationship"]
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
                
        return topics

class EmotionalIntelligence:
    def __init__(self, user_name: str = "User"):
        self.user_name = user_name
        self.current_mood = EmotionalState.NEUTRAL
        self.mood_history = []
        self.emotional_context = EmotionalContext()
        self.empathy_level = 0.5
        self.personality_profile = self._build_personality_profile()
        self.emotion_memory = defaultdict(list)  # Store emotional patterns
        self.linguistic_patterns = self._analyze_linguistic_patterns()
        
        # Load empathy responses
        self.empathy_responses = self._load_empathy_responses()
        
        # Emotional intensity tracking
        self.emotional_intensity = 0.0  # 0-1 scale
        self.recent_intensity = deque(maxlen=5)
        
    def _build_personality_profile(self) -> Dict:
        """Build initial personality profile (evolves over time)"""
        return {
            "emotional_openness": 0.5,  # How openly they express emotions
            "emotional_range": 0.5,     # How wide their emotional range is
            "optimism_bias": 0.5,       # Tendency toward positive/negative
            "stress_tolerance": 0.5,    # How well they handle stress
            "recovery_speed": 0.5,      # How quickly they bounce back
            "learned_patterns": {}      # Learned emotional response patterns
        }
    
    def _analyze_linguistic_patterns(self) -> Dict:
        """Analyze how user typically expresses emotions"""
        return {
            "direct_expression": [],  # "I feel X"
            "metaphorical": [],       # "I'm on cloud nine"
            "physical_manifestation": [],  # "My heart is heavy"
            "contextual": [],         # Emotion implied by situation
            "contradictions": []      # Mixed signals
        }
    
    def _load_empathy_responses(self) -> Dict:
        """Load enhanced empathy responses with personalization"""
        responses = {
            EmotionalState.HAPPY: [
                f"That's wonderful to hear, {self.user_name}!",
                f"I'm glad you're feeling good, {self.user_name}!",
                f"Your positivity is uplifting, {self.user_name}!",
                f"Great to hear you're in good spirits, {self.user_name}!"
            ],
            EmotionalState.SAD: [
                f"I'm sorry to hear that, {self.user_name}. I'm here for you.",
                f"That sounds difficult, {self.user_name}. Would you like to talk about it?",
                f"I understand, {self.user_name}. Sometimes we all feel that way.",
                f"I'm here to listen, {self.user_name}. You're not alone."
            ],
            EmotionalState.ANGRY: [
                f"I sense your frustration, {self.user_name}. Let's work through this.",
                f"That sounds frustrating, {self.user_name}. How can I help?",
                f"I understand you're upset, {self.user_name}. Let's find a solution.",
                f"Take a deep breath, {self.user_name}. I'm here to assist."
            ],
            EmotionalState.STRESSED: [
                f"I can see you're stressed, {self.user_name}. Let's prioritize together.",
                f"Stress can be overwhelming, {self.user_name}. How can I lighten your load?",
                f"Let's break this down, {self.user_name}. One step at a time.",
                f"I'm here to help manage the stress, {self.user_name}."
            ],
            EmotionalState.ANXIOUS: [
                f"I hear your worry, {self.user_name}. Let's take it one step at a time.",
                f"That sounds anxiety-provoking, {self.user_name}. I'm here with you.",
                f"Let's breathe through this together, {self.user_name}.",
                f"I understand the anxiety, {self.user_name}. We'll work through it."
            ],
            EmotionalState.TIRED: [
                f"You sound tired, {self.user_name}. Remember to rest.",
                f"Fatigue is understandable, {self.user_name}. Would you like to take a break?",
                f"Your hard work is commendable, {self.user_name}. Don't forget self-care.",
                f"Even machines need maintenance, {self.user_name}. You deserve rest too."
            ],
            EmotionalState.EXCITED: [
                f"Your excitement is contagious, {self.user_name}!",
                f"That's fantastic news, {self.user_name}!",
                f"I'm excited for you, {self.user_name}!",
                f"What great energy, {self.user_name}!"
            ],
            EmotionalState.FRUSTRATED: [
                f"I sense the frustration, {self.user_name}. Let's find a new approach.",
                f"That's understandably frustrating, {self.user_name}.",
                f"Let's work through this frustration together, {self.user_name}.",
                f"I hear the frustration in your voice, {self.user_name}."
            ],
            EmotionalState.CONTENT: [
                f"Contentment is lovely to hear, {self.user_name}.",
                f"I'm glad you're feeling content, {self.user_name}.",
                f"Peaceful moments are precious, {self.user_name}.",
                f"Contentment suits you, {self.user_name}."
            ],
            EmotionalState.MIXED: [
                f"Mixed feelings are completely normal, {self.user_name}.",
                f"I hear multiple emotions there, {self.user_name}. That's okay.",
                f"Complex feelings make sense, {self.user_name}.",
                f"It's okay to feel multiple things at once, {self.user_name}."
            ],
            EmotionalState.NEUTRAL: [
                f"How are you feeling today, {self.user_name}?",
                f"Is everything alright, {self.user_name}?",
                f"How can I make your day better, {self.user_name}?",
                f"Ready when you are, {self.user_name}."
            ]
        }
        return responses
    
    def detect_emotion(self, text: str, voice_tone: Optional[Dict] = None) -> EmotionalState:
        """Detect emotion from text (simplified version)"""
        text_lower = text.lower()
        
        # Emotion keyword mapping
        emotion_keywords = {
            EmotionalState.HAPPY: [
                "happy", "good", "great", "excited", "wonderful", "awesome",
                "fantastic", "amazing", "joy", "pleased", "delighted", "lovely"
            ],
            EmotionalState.SAD: [
                "sad", "bad", "terrible", "awful", "upset", "unhappy",
                "depressed", "miserable", "heartbroken", "disappointed",
                "not feeling well", "feel bad"
            ],
            EmotionalState.ANGRY: [
                "angry", "mad", "frustrated", "annoyed", "irritated",
                "furious", "rage", "outraged", "pissed", "livid"
            ],
            EmotionalState.STRESSED: [
                "stressed", "overwhelmed", "pressure", "anxious", "worried",
                "tense", "nervous", "panicked", "burnout", "exhausted"
            ],
            EmotionalState.ANXIOUS: [
                "anxious", "worried", "nervous", "scared", "fearful",
                "afraid", "panicked", "uneasy", "apprehensive"
            ],
            EmotionalState.TIRED: [
                "tired", "exhausted", "sleepy", "fatigued", "drained",
                "weary", "burned out", "worn out", "lethargic"
            ],
            EmotionalState.EXCITED: [
                "excited", "thrilled", "eager", "enthusiastic", "pumped",
                "energized", "stoked", "ecstatic", "overjoyed"
            ],
            EmotionalState.FRUSTRATED: [
                "frustrated", "stuck", "blocked", "can't", "won't work",
                "annoyed", "irritated", "fed up"
            ],
            EmotionalState.CONTENT: [
                "content", "peaceful", "calm", "satisfied", "at peace",
                "comfortable", "serene", "relaxed"
            ]
        }
        
        # Count emotion keywords
        emotion_scores = {state: 0 for state in emotion_keywords.keys()}
        
        for state, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    emotion_scores[state] += 1
        
        # Check for intensity indicators
        intensity_words = ["very", "really", "extremely", "so", "incredibly"]
        intensity_multiplier = 1.0
        for word in intensity_words:
            if word in text_lower:
                intensity_multiplier = 1.5
                break
        
        # Apply intensity multiplier
        for state in emotion_scores:
            emotion_scores[state] *= intensity_multiplier
        
        # Find dominant emotion
        max_score = max(emotion_scores.values())
        if max_score > 0:
            dominant_emotions = [state for state, score in emotion_scores.items() 
                               if score == max_score]
            detected_emotion = random.choice(dominant_emotions)
        else:
            detected_emotion = EmotionalState.NEUTRAL
        
        # Update mood history
        self.mood_history.append({
            "emotion": detected_emotion,
            "text": text[:100],  # Store first 100 chars
            "timestamp": datetime.now(),
            "confidence": min(1.0, max_score / 3)  # Normalize confidence
        })
        
        # Keep only last 50 mood entries
        if len(self.mood_history) > 50:
            self.mood_history.pop(0)
        
        self.current_mood = detected_emotion
        
        # Simple intensity calculation
        word_count = len(text.split())
        self.emotional_intensity = min(1.0, max_score / (word_count + 1))
        self.recent_intensity.append(self.emotional_intensity)
        
        return detected_emotion
    
    def detect_emotion_humanlike(self, text: str, 
                                voice_tone: Optional[Dict] = None,
                                timestamp: Optional[datetime] = None) -> Dict:
        """
        Human-like emotion detection using multiple channels
        Returns: {
            "primary_emotion": EmotionalState,
            "secondary_emotions": List[EmotionalState],
            "confidence": float,
            "intensity": float,
            "triggers": List[str],
            "complexity": float
        }
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Use the simplified detection for now
        primary_emotion = self.detect_emotion(text, voice_tone)
        
        # Calculate simple intensity
        text_lower = text.lower()
        intensity_words = ["very", "really", "extremely", "so", "incredibly", "absolutely"]
        intensity = 0.5  # default
        for word in intensity_words:
            if word in text_lower:
                intensity = 0.8
                break
        
        # Check for mixed emotions
        secondary_emotions = []
        if "but" in text_lower or "however" in text_lower:
            # Try to detect secondary emotion
            parts = text_lower.split(" but ")
            if len(parts) > 1:
                secondary_emotion = self.detect_emotion(parts[1], voice_tone)
                if secondary_emotion != primary_emotion:
                    secondary_emotions.append(secondary_emotion)
        
        # Simple triggers detection
        triggers = []
        trigger_words = {
            "work": ["work", "job", "boss", "deadline"],
            "study": ["study", "exam", "test", "homework"],
            "health": ["sick", "pain", "doctor", "hospital"],
            "social": ["friend", "family", "argue", "fight"]
        }
        
        for trigger_type, words in trigger_words.items():
            if any(word in text_lower for word in words):
                triggers.append(trigger_type)
        
        # Simple complexity calculation
        complexity = 0.3
        if secondary_emotions:
            complexity = 0.6
        if "mixed" in text_lower or "conflicted" in text_lower:
            complexity = 0.8
        
        return {
            "primary_emotion": primary_emotion,
            "secondary_emotions": secondary_emotions,
            "confidence": 0.7,  # default confidence
            "intensity": intensity,
            "triggers": triggers,
            "complexity": complexity,
            "emotion_scores": {primary_emotion: 0.7}
        }
    
    def get_empathetic_response(self, detected_emotion=None):
        """Get an empathetic response based on detected emotion"""
        if detected_emotion is None:
            detected_emotion = self.current_mood
        
        responses = self.empathy_responses.get(detected_emotion, 
                                              self.empathy_responses[EmotionalState.NEUTRAL])
        
        return random.choice(responses)
    
    def get_enhanced_empathetic_response(self, emotion_analysis: Optional[Dict] = None) -> str:
        """Get enhanced empathetic response based on comprehensive analysis"""
        if emotion_analysis is None:
            primary_emotion = self.current_mood
            intensity = self.emotional_intensity
        else:
            primary_emotion = emotion_analysis["primary_emotion"]
            intensity = emotion_analysis.get("intensity", 0.5)
        
        # Get base response
        responses = self.empathy_responses.get(
            primary_emotion, 
            self.empathy_responses[EmotionalState.NEUTRAL]
        )
        
        base_response = random.choice(responses)
        
        # Adjust based on intensity
        if intensity > 0.7:
            intensity_modifiers = [
                " I can tell this is really affecting you.",
                " This seems to be weighing heavily on you.",
                " I can feel the strength of this emotion.",
                " This appears to be quite intense for you."
            ]
            base_response += random.choice(intensity_modifiers)
        
        return base_response
    
    def adjust_empathy(self, user_feedback):
        """Adjust empathy level based on user feedback"""
        # Positive feedback increases empathy
        if user_feedback == "positive":
            self.empathy_level = min(1.0, self.empathy_level + 0.1)
        elif user_feedback == "negative":
            self.empathy_level = max(0.1, self.empathy_level - 0.1)
        
        return self.empathy_level
    
    def get_mood_trend(self, days=7):
        """Get mood trend over time"""
        if not self.mood_history:
            return {"average_mood": "neutral", "mood_changes": 0}
        
        # Count mood frequencies
        mood_counts = {}
        for entry in self.mood_history[-days*10:]:  # Approximate last 'days'
            mood = entry["emotion"]
            if isinstance(mood, EmotionalState):
                mood_value = mood.value
            else:
                mood_value = str(mood)
            mood_counts[mood_value] = mood_counts.get(mood_value, 0) + 1
        
        # Find most common mood
        if mood_counts:
            average_mood = max(mood_counts.items(), key=lambda x: x[1])[0]
        else:
            average_mood = "neutral"
        
        # Count mood changes
        mood_changes = 0
        for i in range(1, len(self.mood_history)):
            if self.mood_history[i]["emotion"] != self.mood_history[i-1]["emotion"]:
                mood_changes += 1
        
        return {
            "average_mood": average_mood,
            "mood_changes": mood_changes,
            "current_mood": self.current_mood.value,
            "empathy_level": self.empathy_level,
            "mood_distribution": mood_counts
        }
    
    def provide_support(self, emotion=None):
        """Provide specific support based on emotion"""
        if emotion is None:
            emotion = self.current_mood
        
        support_responses = {
            EmotionalState.SAD: [
                "Would you like me to play some uplifting music?",
                "I can share a joke to lighten the mood.",
                "Sometimes talking helps. I'm here to listen.",
                "Would a comforting distraction help right now?"
            ],
            EmotionalState.STRESSED: [
                "Let me help you organize your tasks.",
                "How about a 5-minute breathing exercise?",
                "Would you like me to schedule some break time?",
                "Let's break this down into smaller, manageable steps."
            ],
            EmotionalState.TIRED: [
                "Would you like me to set a reminder for rest?",
                "How about some calming music?",
                "Remember to stay hydrated and take breaks.",
                "Even a 10-minute power nap can help refresh you."
            ],
            EmotionalState.ANGRY: [
                "Let's work on a solution together.",
                "Would you like to vent? I'm listening.",
                "Sometimes stepping away helps. Want to take a short break?",
                "Let's find a constructive way to channel this energy."
            ],
            EmotionalState.ANXIOUS: [
                "Let's focus on what you can control right now.",
                "Would a grounding exercise help?",
                "Remember to breathe deeply and slowly.",
                "Let's take this one small step at a time."
            ],
            EmotionalState.FRUSTRATED: [
                "Let's try a different approach.",
                "Sometimes starting fresh helps. Want to take a break and come back?",
                "What's one small thing we can accomplish right now?",
                "Let's simplify and focus on the core issue."
            ]
        }
        
        if emotion in support_responses:
            return random.choice(support_responses[emotion])
        
        return "How can I best support you right now?"
    
    def provide_enhanced_support(self, emotion_analysis: Dict) -> str:
        """Provide enhanced support based on comprehensive analysis"""
        primary = emotion_analysis["primary_emotion"]
        intensity = emotion_analysis.get("intensity", 0.5)
        secondary = emotion_analysis.get("secondary_emotions", [])
        
        support_options = []
        
        # Base support based on primary emotion
        if primary == EmotionalState.SAD:
            if intensity > 0.7:
                support_options = [
                    "Would you like me to just sit with you in this feeling?",
                    "Sometimes the heaviest feelings just need to be acknowledged.",
                    "Would listening to some gentle, soothing music help?"
                ]
            else:
                support_options = [
                    "Would a gentle distraction help, or would you prefer to stay with the feeling?",
                    "How about a warm drink and some comforting music?",
                    "Would sharing a happy memory help lift your spirits?"
                ]
        
        elif primary == EmotionalState.ANXIOUS:
            if intensity > 0.7:
                support_options = [
                    "Let's do a quick 5-4-3-2-1 grounding exercise together.",
                    "How about we name 5 things you can see around you right now?",
                    "Would breathing in for 4, holding for 4, out for 6 help?"
                ]
            else:
                support_options = [
                    "How about we write down what's worrying you?",
                    "Would organizing your thoughts into categories help?",
                    "Shall we find one small, manageable action you can take?"
                ]
        
        # Add secondary emotion considerations
        if EmotionalState.TIRED in secondary and intensity > 0.5:
            support_options.append("Given the tiredness, maybe rest should come first?")
        
        if not support_options:
            support_options = ["How can I best support you in this moment?"]
        
        return random.choice(support_options)
    
    def get_emotional_summary(self, hours: int = 24) -> Dict:
        """Get comprehensive emotional summary"""
        recent_history = [entry for entry in self.mood_history 
                         if datetime.now() - entry.get("timestamp", datetime.now()) 
                         < timedelta(hours=hours)]
        
        if not recent_history:
            return {"status": "No recent emotional data"}
        
        # Analyze patterns
        emotions = [entry.get("emotion", EmotionalState.NEUTRAL) 
                   for entry in recent_history]
        
        primary_emotions = [e.value if isinstance(e, EmotionalState) else e 
                           for e in emotions]
        
        # Calculate emotional diversity
        unique_emotions = len(set(primary_emotions))
        emotional_diversity = unique_emotions / len(primary_emotions) if primary_emotions else 0
        
        # Calculate emotional volatility
        changes = 0
        for i in range(1, len(emotions)):
            if emotions[i] != emotions[i-1]:
                changes += 1
        
        volatility = changes / len(emotions) if emotions else 0
        
        return {
            "emotional_timeline": recent_history[-10:],  # Last 10 entries
            "primary_emotion": self.current_mood.value,
            "intensity_trend": list(self.recent_intensity),
            "emotional_diversity": emotional_diversity,
            "emotional_volatility": volatility,
            "common_triggers": self._identify_common_triggers(),
            "support_suggestions": self._generate_support_suggestions(emotions)
        }
    
    def _identify_common_triggers(self) -> List[str]:
        """Identify common emotional triggers from history"""
        triggers = []
        
        # Simplified version
        work_triggers = ["deadline", "boss", "meeting", "workload", "work", "job"]
        social_triggers = ["friend", "family", "argue", "fight", "partner", "relationship"]
        health_triggers = ["sick", "pain", "tired", "exhausted", "not feeling well"]
        
        # Check last 20 entries
        for entry in self.mood_history[-20:]:
            text = entry.get("text", "").lower()
            emotion = entry.get("emotion")
            
            if emotion in [EmotionalState.STRESSED, EmotionalState.ANXIOUS]:
                if any(trigger in text for trigger in work_triggers):
                    triggers.append("work pressure")
            
            if emotion in [EmotionalState.SAD, EmotionalState.ANGRY]:
                if any(trigger in text for trigger in social_triggers):
                    triggers.append("social interactions")
            
            if emotion in [EmotionalState.SAD, EmotionalState.TIRED]:
                if any(trigger in text for trigger in health_triggers):
                    triggers.append("health concerns")
        
        return list(set(triggers))[:3]  # Return top 3 unique triggers
    
    def _generate_support_suggestions(self, emotions: List) -> List[str]:
        """Generate support suggestions based on emotional patterns"""
        suggestions = []
        
        # Count emotions
        emotion_counts = {}
        for emotion in emotions:
            if isinstance(emotion, EmotionalState):
                key = emotion.value
            else:
                key = str(emotion)
            emotion_counts[key] = emotion_counts.get(key, 0) + 1
        
        # Generate suggestions based on patterns
        if emotion_counts.get("sad", 0) > 3:
            suggestions.append("Consider incorporating more uplifting activities into your routine")
        
        if emotion_counts.get("stressed", 0) > 3:
            suggestions.append("Regular breaks and mindfulness exercises might help")
        
        if emotion_counts.get("tired", 0) > 3:
            suggestions.append("Prioritizing sleep and rest could be beneficial")
        
        if len(emotion_counts) > 4:  # High emotional diversity
            suggestions.append("Your emotional range is wide - this shows great emotional awareness")
        
        return suggestions[:3]  # Return top 3 suggestions

# Simple version for quick integration
class SimpleEmotionalIntelligence:
    def __init__(self, user_name="User"):
        self.user_name = user_name
        self.current_mood = EmotionalState.NEUTRAL
        self.mood_history = []
        self.empathy_level = 0.5
        
    def detect_emotion(self, text):
        """Simple emotion detection"""
        text_lower = text.lower()
        
        emotion_map = {
            EmotionalState.HAPPY: ["happy", "good", "great", "excited", "wonderful"],
            EmotionalState.SAD: ["sad", "bad", "terrible", "awful", "not feeling well"],
            EmotionalState.ANGRY: ["angry", "mad", "frustrated", "annoyed"],
            EmotionalState.STRESSED: ["stressed", "overwhelmed", "pressure"],
            EmotionalState.TIRED: ["tired", "exhausted", "sleepy"],
            EmotionalState.EXCITED: ["excited", "thrilled", "eager"]
        }
        
        for emotion, keywords in emotion_map.items():
            for keyword in keywords:
                if keyword in text_lower:
                    self.current_mood = emotion
                    return emotion
        
        return EmotionalState.NEUTRAL
    
    def get_response(self):
        """Get appropriate response"""
        responses = {
            EmotionalState.HAPPY: f"I'm glad you're feeling good, {self.user_name}!",
            EmotionalState.SAD: f"I'm sorry to hear that, {self.user_name}. I'm here for you.",
            EmotionalState.ANGRY: f"I sense your frustration, {self.user_name}. Let's work through this.",
            EmotionalState.STRESSED: f"I can see you're stressed, {self.user_name}. Let's prioritize together.",
            EmotionalState.TIRED: f"You sound tired, {self.user_name}. Remember to rest.",
            EmotionalState.EXCITED: f"Your excitement is contagious, {self.user_name}!",
            EmotionalState.NEUTRAL: f"How can I help you today, {self.user_name}?"
        }
        
        return responses.get(self.current_mood, responses[EmotionalState.NEUTRAL])

# Example usage
if __name__ == "__main__":
    # Test with simplified version
    ei = SimpleEmotionalIntelligence("Prince")
    
    test_phrases = [
        "I am not feeling well",
        "I'm so excited about today!",
        "Work is really stressing me out",
        "I'm tired and exhausted",
        "I feel frustrated with this project"
    ]
    
    for phrase in test_phrases:
        print(f"\nUser: {phrase}")
        emotion = ei.detect_emotion(phrase)
        print(f"Detected emotion: {emotion.value}")
        print(f"Response: {ei.get_response()}")