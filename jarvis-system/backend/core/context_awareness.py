#!/usr/bin/env python3
"""
Advanced Context Awareness Module
Simulates human-like contextual understanding with memory, learning, and multi-modal awareness
"""

import datetime
import json
import os
import re
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import threading
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import pytz
from textblob import TextBlob
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

class TimeOfDay(Enum):
    EARLY_MORNING = "early_morning"  # 4-7
    MORNING = "morning"              # 7-12
    AFTERNOON = "afternoon"          # 12-17
    EVENING = "evening"              # 17-21
    NIGHT = "night"                  # 21-24
    LATE_NIGHT = "late_night"        # 0-4

class ActivityType(Enum):
    WORKING = "working"
    STUDYING = "studying"
    ENTERTAINMENT = "entertainment"
    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"
    LEISURE = "leisure"
    CREATIVE = "creative"
    PLANNING = "planning"
    SHOPPING = "shopping"
    TRAVEL = "travel"
    HEALTH = "health"
    UNKNOWN = "unknown"

class EmotionalState(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    STRESSED = "stressed"
    TIRED = "tired"
    FOCUSED = "focused"
    RELAXED = "relaxed"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"

@dataclass
class UserProfile:
    """Stores learned user preferences and patterns"""
    preferred_greetings: Dict[str, List[str]] = None
    activity_patterns: Dict[str, Dict[str, Any]] = None
    preferred_times: Dict[str, List[str]] = None
    emotional_tendencies: Dict[str, List[str]] = None
    topics_of_interest: List[str] = None
    pet_peeves: List[str] = None
    conversation_style: str = "neutral"  # formal, casual, technical, friendly
    
    def __post_init__(self):
        if self.preferred_greetings is None:
            self.preferred_greetings = defaultdict(list)
        if self.activity_patterns is None:
            self.activity_patterns = defaultdict(dict)
        if self.preferred_times is None:
            self.preferred_times = defaultdict(list)
        if self.emotional_tendencies is None:
            self.emotional_tendencies = defaultdict(list)
        if self.topics_of_interest is None:
            self.topics_of_interest = []
        if self.pet_peeves is None:
            self.pet_peeves = []

class ContextMemory:
    """Manages short-term and long-term context memory"""
    def __init__(self, max_short_term=20, max_long_term=1000):
        self.short_term = deque(maxlen=max_short_term)
        self.long_term = deque(maxlen=max_long_term)
        self.semantic_memory = {}  # Conceptual relationships
        self.episodic_memory = []  # Specific events with emotional tags
        
    def add_short_term(self, context: Dict[str, Any]):
        """Add to working memory"""
        self.short_term.append(context)
        
    def add_long_term(self, context: Dict[str, Any]):
        """Add to long-term memory with semantic processing"""
        self.long_term.append(context)
        self._extract_semantics(context)
        
    def _extract_semantics(self, context: Dict[str, Any]):
        """Extract meaningful patterns and relationships"""
        # Extract entities and relationships
        text = f"{context.get('user_input', '')} {context.get('jarvis_response', '')}"
        blob = TextBlob(text)
        
        # Store noun phrases as concepts
        for np in blob.noun_phrases:
            if np not in self.semantic_memory:
                self.semantic_memory[np] = {
                    'first_seen': datetime.datetime.now(),
                    'frequency': 1,
                    'related_contexts': [context],
                    'emotional_associations': []
                }
            else:
                self.semantic_memory[np]['frequency'] += 1
                self.semantic_memory[np]['related_contexts'].append(context)

class HumanLikeContextAwareness:
    def __init__(self, user_name: str, user_id: str = None, timezone: str = "UTC"):
        self.user_name = user_name
        self.user_id = user_id or user_name.lower().replace(" ", "_")
        self.timezone = pytz.timezone(timezone)
        
        # Core context tracking
        self.current_activity = ActivityType.UNKNOWN
        self.current_emotional_state = EmotionalState.NEUTRAL
        self.last_interaction_time = None
        self.conversation_context = []
        
        # Memory systems
        self.memory = ContextMemory()
        self.user_profile = UserProfile()
        
        # Temporal awareness
        self.weekly_patterns = defaultdict(list)
        self.daily_routines = {}
        
        # Environmental awareness (simulated)
        self.environmental_context = {
            'location': 'home',  # home, office, traveling, etc.
            'device': 'desktop',  # desktop, mobile, car, etc.
            'interaction_mode': 'text',  # text, voice, gesture
            'attention_level': 'high',  # high, medium, low, distracted
        }
        
        # Learning and adaptation
        self.interaction_count = 0
        self.learning_rate = 0.1
        self.preference_model = TfidfVectorizer(max_features=100)
        self.trained = False
        
        # Load existing profile if available
        self._load_profile()
        
        # Start background context maintenance
        self._maintenance_thread = threading.Thread(target=self._context_maintenance, daemon=True)
        self._maintenance_thread.start()
    
    def _load_profile(self):
        """Load user profile from storage"""
        profile_file = f"{self.user_id}_profile.json"
        if os.path.exists(profile_file):
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    self.user_profile = UserProfile(**data)
                    print(f"Loaded profile for {self.user_name}")
            except Exception as e:
                print(f"Error loading profile: {e}")
    
    def _save_profile(self):
        """Save user profile to storage"""
        profile_file = f"{self.user_id}_profile.json"
        try:
            with open(profile_file, 'w') as f:
                json.dump(asdict(self.user_profile), f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving profile: {e}")
    
    def get_time_of_day(self) -> TimeOfDay:
        """Determine current time of day with more granularity"""
        current_hour = datetime.datetime.now(self.timezone).hour
        
        if 0 <= current_hour < 4:
            return TimeOfDay.LATE_NIGHT
        elif 4 <= current_hour < 7:
            return TimeOfDay.EARLY_MORNING
        elif 7 <= current_hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= current_hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= current_hour < 21:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT
    
    def _detect_emotional_state(self, text: str) -> EmotionalState:
        """Analyze emotional state from text"""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Check for emotional keywords
        emotional_keywords = {
            EmotionalState.HAPPY: ["great", "awesome", "wonderful", "happy", "excited", "love"],
            EmotionalState.STRESSED: ["stress", "busy", "overwhelmed", "deadline", "urgent"],
            EmotionalState.TIRED: ["tired", "exhausted", "sleepy", "long day"],
            EmotionalState.FOCUSED: ["focus", "concentrate", "deep work", "productive"],
            EmotionalState.FRUSTRATED: ["frustrated", "annoyed", "angry", "upset", "problem"],
            EmotionalState.RELAXED: ["relax", "chill", "calm", "peaceful"]
        }
        
        text_lower = text.lower()
        for state, keywords in emotional_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return state
        
        # Use sentiment analysis as fallback
        if polarity > 0.3:
            return EmotionalState.HAPPY
        elif polarity < -0.3:
            return EmotionalState.FRUSTRATED
        elif subjectivity < 0.3:
            return EmotionalState.NEUTRAL
        else:
            return EmotionalState.NEUTRAL
    
    def _detect_activity_with_context(self, text: str, previous_context: Dict = None) -> ActivityType:
        """Advanced activity detection using context"""
        text_lower = text.lower()
        
        # Multi-level activity detection
        activity_patterns = {
            ActivityType.WORKING: {
                'keywords': ["code", "program", "debug", "develop", "meeting", "deadline", "project"],
                'context_cues': ["office", "work", "job", "colleague"],
                'time_pattern': ['MORNING', 'AFTERNOON']
            },
            ActivityType.STUDYING: {
                'keywords': ["study", "learn", "research", "homework", "exam", "course"],
                'context_cues': ["school", "university", "library", "student"],
                'time_pattern': ['AFTERNOON', 'EVENING']
            },
            ActivityType.CREATIVE: {
                'keywords': ["write", "design", "create", "draw", "compose", "build"],
                'context_cues': ["inspiration", "creative", "art", "music"],
                'time_pattern': ['NIGHT', 'LATE_NIGHT']
            },
            ActivityType.PLANNING: {
                'keywords': ["plan", "schedule", "organize", "prepare", "arrange"],
                'context_cues': ["tomorrow", "next week", "agenda", "calendar"],
                'time_pattern': ['MORNING', 'EVENING']
            }
        }
        
        # Score activities based on multiple factors
        scores = {}
        current_time = self.get_time_of_day()
        
        for activity, pattern in activity_patterns.items():
            score = 0
            
            # Keyword matching
            for keyword in pattern['keywords']:
                if keyword in text_lower:
                    score += 2
            
            # Context cue matching
            if previous_context:
                prev_text = previous_context.get('user_input', '').lower()
                for cue in pattern['context_cues']:
                    if cue in prev_text:
                        score += 1.5
            
            # Time pattern matching
            if current_time.value.upper() in pattern['time_pattern']:
                score += 1
            
            scores[activity] = score
        
        # Get highest scoring activity
        if scores:
            max_activity = max(scores.items(), key=lambda x: x[1])
            if max_activity[1] > 1:
                return max_activity[0]
        
        return ActivityType.UNKNOWN
    
    def _update_environmental_context(self, text: str):
        """Infer environmental context from conversation"""
        text_lower = text.lower()
        
        # Detect location cues
        location_cues = {
            'home': ["home", "house", "apartment", "living room", "bedroom"],
            'office': ["office", "work", "desk", "meeting", "colleague"],
            'car': ["car", "driving", "road", "traffic", "commute"],
            'public': ["store", "restaurant", "park", "gym", "cafe"]
        }
        
        for location, cues in location_cues.items():
            if any(cue in text_lower for cue in cues):
                self.environmental_context['location'] = location
                break
        
        # Detect device/interface cues
        if "phone" in text_lower or "mobile" in text_lower:
            self.environmental_context['device'] = 'mobile'
        elif "car" in text_lower or "driving" in text_lower:
            self.environmental_context['device'] = 'car'
        
        # Detect attention level
        distraction_cues = ["busy", "multitasking", "distracted", "in a hurry"]
        if any(cue in text_lower for cue in distraction_cues):
            self.environmental_context['attention_level'] = 'low'
        elif "focus" in text_lower or "concentrate" in text_lower:
            self.environmental_context['attention_level'] = 'high'
    
    def update_context(self, user_input: str, jarvis_response: str = "") -> Dict[str, Any]:
        """Comprehensive context update with multi-faceted awareness"""
        self.interaction_count += 1
        
        # Get temporal context
        current_time = datetime.datetime.now(self.timezone)
        time_of_day = self.get_time_of_day()
        day_of_week = current_time.strftime("%A")
        
        # Detect emotional state
        emotional_state = self._detect_emotional_state(user_input)
        
        # Detect activity with memory of previous context
        previous_context = self.conversation_context[-1] if self.conversation_context else None
        activity = self._detect_activity_with_context(user_input, previous_context)
        
        # Update environmental context
        self._update_environmental_context(user_input)
        
        # Create comprehensive context entry
        context_entry = {
            "timestamp": current_time.isoformat(),
            "time_of_day": time_of_day.value,
            "day_of_week": day_of_week,
            "activity": activity.value,
            "emotional_state": emotional_state.value,
            "environment": self.environmental_context.copy(),
            "user_input": user_input,
            "jarvis_response": jarvis_response,
            "interaction_id": self.interaction_count,
            "context_chain": len(self.conversation_context)
        }
        
        # Update current state
        self.current_activity = activity
        self.current_emotional_state = emotional_state
        self.last_interaction_time = current_time
        
        # Add to memory systems
        self.memory.add_short_term(context_entry)
        self.memory.add_long_term(context_entry)
        
        # Update conversation context
        self.conversation_context.append(context_entry)
        if len(self.conversation_context) > 10:
            self.conversation_context.pop(0)
        
        # Learn from this interaction
        self._learn_from_interaction(context_entry)
        
        # Update weekly patterns
        self.weekly_patterns[day_of_week].append({
            'time': current_time.hour,
            'activity': activity.value,
            'emotional_state': emotional_state.value
        })
        
        return context_entry
    
    def _learn_from_interaction(self, context: Dict[str, Any]):
        """Learn user preferences and patterns"""
        # Learn greeting preferences
        time_of_day = context['time_of_day']
        if context['jarvis_response']:
            response_start = context['jarvis_response'].split()[0].lower()
            if response_start in ['hi', 'hello', 'hey', 'good']:
                if response_start not in self.user_profile.preferred_greetings[time_of_day]:
                    self.user_profile.preferred_greetings[time_of_day].append(response_start)
        
        # Learn activity patterns
        activity = context['activity']
        if activity not in self.user_profile.activity_patterns:
            self.user_profile.activity_patterns[activity] = {
                'common_times': [],
                'emotional_associations': [],
                'duration_patterns': []
            }
        
        # Add time pattern for this activity
        self.user_profile.activity_patterns[activity]['common_times'].append(
            context['timestamp']
        )
        
        # Add emotional association
        self.user_profile.activity_patterns[activity]['emotional_associations'].append(
            context['emotional_state']
        )
        
        # Save learned profile periodically
        if self.interaction_count % 10 == 0:
            self._save_profile()
    
    def get_contextual_greeting(self) -> str:
        """Intelligent greeting based on comprehensive context"""
        time_of_day = self.get_time_of_day()
        day_of_week = datetime.datetime.now(self.timezone).strftime("%A")
        
        # Use learned preferences
        preferred_greetings = self.user_profile.preferred_greetings.get(time_of_day.value, [])
        
        # Base greetings by time
        base_greetings = {
            TimeOfDay.EARLY_MORNING: ["Early bird, I see!", "Up already?", "Morning has broken!"],
            TimeOfDay.MORNING: ["Good morning!", "Rise and shine!", "Ready for the day?"],
            TimeOfDay.AFTERNOON: ["Good afternoon!", "How's your day going?", "Afternoon!"],
            TimeOfDay.EVENING: ["Good evening!", "How was your day?", "Evening!"],
            TimeOfDay.NIGHT: ["Working late?", "Still up?", "Night owl!"],
            TimeOfDay.LATE_NIGHT: ["Very late!", "Shouldn't you be sleeping?", "Late night session!"]
        }
        
        # Select greeting
        if preferred_greetings:
            greeting_base = np.random.choice(preferred_greetings)
        else:
            greeting_base = np.random.choice(base_greetings[time_of_day])
        
        # Add emotional awareness
        emotional_addons = {
            EmotionalState.HAPPY: [" You sound cheerful!", " Glad to hear you're in good spirits!"],
            EmotionalState.TIRED: [" You sound tired. Need a break?", " Long day?"],
            EmotionalState.STRESSED: [" Take a deep breath.", " One thing at a time."],
            EmotionalState.FOCUSED: [" I see you're in the zone.", " Staying focused, I like it!"]
        }
        
        emotional_addon = emotional_addons.get(self.current_emotional_state, "")
        if emotional_addon:
            emotional_addon = np.random.choice(emotional_addon)
        
        # Add continuity if we have recent context
        continuity = ""
        if len(self.conversation_context) > 0:
            last_context = self.conversation_context[-1]
            if 'activity' in last_context:
                continuity_map = {
                    'working': " Continuing with work?",
                    'studying': " Back to studying?",
                    'planning': " Still planning?",
                }
                continuity = continuity_map.get(last_context['activity'], "")
        
        return f"{greeting_base}{emotional_addon}{continuity} How can I assist you today?"
    
    def get_contextual_suggestion(self) -> str:
        """Intelligent suggestions based on holistic context"""
        suggestions = []
        
        # Activity-based suggestions
        activity_suggestions = {
            ActivityType.WORKING: [
                "Would you like some focus music?",
                "Should I start a pomodoro timer?",
                "Need help organizing your tasks?",
                "Want me to minimize distractions?"
            ],
            ActivityType.STUDYING: [
                "I can help summarize key points.",
                "Would flashcards be helpful?",
                "Need a study break reminder?",
                "Want me to find related resources?"
            ],
            ActivityType.CREATIVE: [
                "Need some creative inspiration?",
                "Should I play ambient sounds?",
                "Want to brainstorm together?",
                "Need help organizing your ideas?"
            ],
            ActivityType.PLANNING: [
                "I can help create a timeline.",
                "Should we prioritize tasks?",
                "Need to schedule reminders?",
                "Want to visualize your plan?"
            ]
        }
        
        if self.current_activity in activity_suggestions:
            suggestions.append(np.random.choice(activity_suggestions[self.current_activity]))
        
        # Time-based suggestions
        time_suggestions = {
            TimeOfDay.LATE_NIGHT: [
                "It's getting late. Should we wrap up soon?",
                "Don't forget to get enough sleep!",
                "Would you like me to set a bedtime reminder?"
            ],
            TimeOfDay.EARLY_MORNING: [
                "Ready for your morning routine?",
                "Need help planning your day?",
                "Would you like some motivational quotes?"
            ]
        }
        
        time_of_day = self.get_time_of_day()
        if time_of_day in time_suggestions:
            suggestions.append(np.random.choice(time_suggestions[time_of_day]))
        
        # Emotional state suggestions
        emotional_suggestions = {
            EmotionalState.STRESSED: [
                "Would a short meditation help?",
                "How about we take a 5-minute break?",
                "Let me tell you a joke to lighten the mood."
            ],
            EmotionalState.TIRED: [
                "Would you like some energizing music?",
                "How about a quick stretch?",
                "Need me to order some coffee?"
            ]
        }
        
        if self.current_emotional_state in emotional_suggestions:
            suggestions.append(np.random.choice(emotional_suggestions[self.current_emotional_state]))
        
        # Combine suggestions
        if suggestions:
            return " " + " | ".join(suggestions[:2])
        else:
            return " How can I assist you further?"
    
    def anticipate_needs(self) -> List[str]:
        """Anticipate user needs based on patterns"""
        needs = []
        current_time = datetime.datetime.now(self.timezone)
        
        # Check daily routines
        hour = current_time.hour
        day_of_week = current_time.strftime("%A")
        
        # Morning routine check
        if hour == 8 and day_of_week in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
            needs.append("Would you like your morning briefing?")
        
        # Lunch time check
        if hour == 12 and self.current_activity == ActivityType.WORKING:
            needs.append("It's lunch time. Need help ordering food?")
        
        # End of work day check
        if hour == 17 and self.current_activity == ActivityType.WORKING:
            needs.append("End of work day. Want to review tomorrow's schedule?")
        
        # Based on recent activities
        if len(self.conversation_context) > 2:
            recent_activities = [c['activity'] for c in self.conversation_context[-3:]]
            if all(a == 'working' for a in recent_activities):
                needs.append("You've been working hard. Time for a break?")
        
        return needs
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get comprehensive context summary"""
        return {
            "user": self.user_name,
            "current_state": {
                "activity": self.current_activity.value,
                "emotional_state": self.current_emotional_state.value,
                "time_of_day": self.get_time_of_day().value,
                "environment": self.environmental_context
            },
            "temporal_context": {
                "day_of_week": datetime.datetime.now(self.timezone).strftime("%A"),
                "week_number": datetime.datetime.now(self.timezone).isocalendar()[1],
                "last_interaction": self.last_interaction_time.isoformat() if self.last_interaction_time else None
            },
            "interaction_history": {
                "total_interactions": self.interaction_count,
                "conversation_length": len(self.conversation_context),
                "short_term_memory": len(self.memory.short_term),
                "long_term_memory": len(self.memory.long_term)
            },
            "learned_patterns": {
                "preferred_greetings": dict(self.user_profile.preferred_greetings),
                "activity_frequencies": {k: len(v['common_times']) for k, v in self.user_profile.activity_patterns.items()}
            }
        }
    
    def _context_maintenance(self):
        """Background thread for maintaining context awareness"""
        import time
        
        while True:
            time.sleep(60)  # Run every minute
            
            # Check for context drift
            if self.last_interaction_time:
                time_since_last = datetime.datetime.now(self.timezone) - self.last_interaction_time
                if time_since_last.total_seconds() > 300:  # 5 minutes
                    # User might have changed context without telling us
                    self.current_activity = ActivityType.UNKNOWN
                    self.environmental_context['attention_level'] = 'unknown'
            
            # Clean up old patterns periodically
            if self.interaction_count % 100 == 0:
                self._cleanup_patterns()
    
    def _cleanup_patterns(self):
        """Remove outdated patterns"""
        # Keep only recent patterns (last 30 days)
        cutoff_date = datetime.datetime.now(self.timezone) - datetime.timedelta(days=30)
        
        for activity in list(self.user_profile.activity_patterns.keys()):
            timestamps = self.user_profile.activity_patterns[activity]['common_times']
            recent_timestamps = [
                ts for ts in timestamps 
                if datetime.datetime.fromisoformat(ts) > cutoff_date
            ]
            
            if recent_timestamps:
                self.user_profile.activity_patterns[activity]['common_times'] = recent_timestamps
            else:
                del self.user_profile.activity_patterns[activity]
    
    def reset_conversation_context(self):
        """Reset conversation context while maintaining long-term memory"""
        self.conversation_context = []
        self.current_activity = ActivityType.UNKNOWN
        self.current_emotional_state = EmotionalState.NEUTRAL
        print(f"Conversation context reset for {self.user_name}")


# Example usage
if __name__ == "__main__":
    # Initialize with user
    context_engine = HumanLikeContextAwareness(
        user_name="John Doe",
        user_id="john_doe_123",
        timezone="America/New_York"
    )
    
    # Simulate interactions
    interactions = [
        "I need to finish my programming project, it's due tomorrow",
        "I'm feeling really stressed about this deadline",
        "Can you help me organize my tasks?",
        "It's getting late, I should probably sleep"
    ]
    
    for i, user_input in enumerate(interactions):
        print(f"\n{'='*50}")
        print(f"Interaction {i+1}: {user_input}")
        
        # Update context
        context = context_engine.update_context(
            user_input=user_input,
            jarvis_response=f"I understand about interaction {i+1}"
        )
        
        # Get contextual greeting
        greeting = context_engine.get_contextual_greeting()
        print(f"Contextual Greeting: {greeting}")
        
        # Get suggestions
        suggestions = context_engine.get_contextual_suggestion()
        print(f"Suggestions: {suggestions}")
        
        # Get anticipated needs
        needs = context_engine.anticipate_needs()
        if needs:
            print(f"Anticipated Needs: {needs}")
        
        # Show context summary
        summary = context_engine.get_context_summary()
        print(f"\nContext Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")