#!/usr/bin/env python3
"""
Emotional Intelligence Module
Responds appropriately to mood indicators and shows empathy
"""

import random
from enum import Enum

class EmotionalState(Enum):
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    STRESSED = "stressed"
    TIRED = "tired"
    EXCITED = "excited"
    NEUTRAL = "neutral"

class EmotionalIntelligence:
    def __init__(self, user_name="User"):
        self.user_name = user_name
        self.current_mood = EmotionalState.NEUTRAL
        self.mood_history = []
        self.empathy_level = 0.5  # 0-1 scale
        self.empathy_responses = self._load_empathy_responses()
        
    def _load_empathy_responses(self):
        """Load empathy responses database"""
        return {
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
            EmotionalState.NEUTRAL: [
                f"How are you feeling today, {self.user_name}?",
                f"Is everything alright, {self.user_name}?",
                f"How can I make your day better, {self.user_name}?",
                f"Ready when you are, {self.user_name}."
            ]
        }
    
    def detect_emotion(self, text, voice_tone=None):
        """Detect emotion from text and optionally voice tone"""
        text_lower = text.lower()
        
        # Emotion keyword mapping
        emotion_keywords = {
            EmotionalState.HAPPY: [
                "happy", "good", "great", "excited", "wonderful", "awesome",
                "fantastic", "amazing", "joy", "pleased", "delighted"
            ],
            EmotionalState.SAD: [
                "sad", "bad", "terrible", "awful", "upset", "unhappy",
                "depressed", "miserable", "heartbroken", "disappointed"
            ],
            EmotionalState.ANGRY: [
                "angry", "mad", "frustrated", "annoyed", "irritated",
                "furious", "rage", "outraged", "pissed", "livid"
            ],
            EmotionalState.STRESSED: [
                "stressed", "overwhelmed", "pressure", "anxious", "worried",
                "tense", "nervous", "panicked", "burnout", "exhausted"
            ],
            EmotionalState.TIRED: [
                "tired", "exhausted", "sleepy", "fatigued", "drained",
                "weary", "burned out", "worn out", "lethargic"
            ],
            EmotionalState.EXCITED: [
                "excited", "thrilled", "eager", "enthusiastic", "pumped",
                "energized", "stoked", "ecstatic", "overjoyed"
            ]
        }
        
        # Count emotion keywords
        emotion_scores = {state: 0 for state in EmotionalState}
        
        for state, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    emotion_scores[state] += 1
        
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
            "confidence": max_score / 3  # Normalize confidence
        })
        
        # Keep only last 50 mood entries
        if len(self.mood_history) > 50:
            self.mood_history.pop(0)
        
        self.current_mood = detected_emotion
        return detected_emotion
    
    def get_empathetic_response(self, detected_emotion=None):
        """Get an empathetic response based on detected emotion"""
        if detected_emotion is None:
            detected_emotion = self.current_mood
        
        responses = self.empathy_responses.get(detected_emotion, 
                                              self.empathy_responses[EmotionalState.NEUTRAL])
        
        return random.choice(responses)
    
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
            mood = entry["emotion"].value
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
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
    
    def provide_support(self, emotion):
        """Provide specific support based on emotion"""
        support_responses = {
            EmotionalState.SAD: [
                "Would you like me to play some uplifting music?",
                "I can share a joke to lighten the mood.",
                "Sometimes talking helps. I'm here to listen."
            ],
            EmotionalState.STRESSED: [
                "Let me help you organize your tasks.",
                "How about a 5-minute breathing exercise?",
                "Would you like me to schedule some break time?"
            ],
            EmotionalState.TIRED: [
                "Would you like me to set a reminder for rest?",
                "How about some calming music?",
                "Remember to stay hydrated and take breaks."
            ],
            EmotionalState.ANGRY: [
                "Let's work on a solution together.",
                "Would you like to vent? I'm listening.",
                "Sometimes stepping away helps. Want to take a short break?"
            ]
        }
        
        if emotion in support_responses:
            return random.choice(support_responses[emotion])
        
        return "How can I best support you right now?"