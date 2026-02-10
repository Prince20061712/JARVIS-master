#!/usr/bin/env python3
"""
Advanced Proactive Assistant Module
Uses AI to anticipate user needs with intelligent predictions and learning
"""

import datetime
import random
import time
import json
import pickle
import numpy as np
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import hashlib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

class ProactiveEventType(Enum):
    REMINDER = "reminder"
    SUGGESTION = "suggestion"
    CHECKIN = "checkin"
    ALERT = "alert"
    MOTIVATION = "motivation"
    BREAK = "break"
    PREDICTION = "prediction"
    INSIGHT = "insight"
    OPTIMIZATION = "optimization"
    LEARNING = "learning"

class UserContext(Enum):
    WORKING = "working"
    STUDYING = "studying"
    CODING = "coding"
    ENTERTAINMENT = "entertainment"
    COMMUNICATION = "communication"
    RELAXING = "relaxing"
    TRAVELING = "traveling"
    SHOPPING = "shopping"
    LEARNING = "learning"
    CREATING = "creating"

class ProactivePriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class ProactiveEvent:
    event_type: ProactiveEventType
    message: str
    priority: ProactivePriority
    timestamp: str
    context: Dict[str, Any]
    confidence: float
    action_items: List[str]
    metadata: Dict[str, Any]

@dataclass
class UserPattern:
    pattern_hash: str
    context: UserContext
    time_window: Tuple[int, int]
    frequency: int
    last_observed: str
    typical_actions: List[str]
    success_rate: float
    learned_at: str

class AdvancedProactiveAssistant:
    def __init__(self, user_name="User", data_dir="proactive_data"):
        self.user_name = user_name
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Event tracking
        self.last_proactive_time = datetime.datetime.now()
        self.proactive_intervals = {
            ProactivePriority.CRITICAL: 300,    # 5 minutes
            ProactivePriority.HIGH: 900,        # 15 minutes
            ProactivePriority.MEDIUM: 1800,     # 30 minutes
            ProactivePriority.LOW: 3600,        # 1 hour
            ProactivePriority.INFO: 7200        # 2 hours
        }
        
        # User patterns and habits
        self.user_patterns: Dict[str, UserPattern] = {}
        self.context_history = deque(maxlen=1000)
        self.suggestion_history = deque(maxlen=500)
        self.feedback_history = deque(maxlen=500)
        
        # ML components
        self.pattern_classifier = None
        self.label_encoder = LabelEncoder()
        self.feature_names = []
        
        # Time-based triggers (enhanced)
        self.time_triggers = self._initialize_time_triggers()
        
        # Context-based triggers (enhanced)
        self.context_triggers = self._initialize_context_triggers()
        
        # User preferences
        self.user_preferences = self._load_preferences()
        
        # Statistics
        self.stats = {
            "total_events_generated": 0,
            "events_by_type": defaultdict(int),
            "events_by_priority": defaultdict(int),
            "user_feedback_positive": 0,
            "user_feedback_negative": 0,
            "prediction_accuracy": 0.0,
            "patterns_learned": 0,
            "average_response_time": 0.0
        }
        
        # External integrations (placeholder URLs)
        self.external_apis = {
            "weather": "https://api.openweathermap.org/data/2.5/weather",
            "news": "https://newsapi.org/v2/top-headlines",
            "calendar": "https://www.googleapis.com/calendar/v3",
            "stock": "https://www.alphavantage.co/query"
        }
        
        # Load existing data
        self._load_learned_data()
        self._initialize_ml_models()
    
    def _initialize_time_triggers(self) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """Initialize intelligent time-based triggers"""
        return {
            (5, 30): {
                "type": "morning_start",
                "context": UserContext.WORKING,
                "message": f"Good morning, {self.user_name}! Would you like me to prepare your daily briefing?",
                "actions": ["daily_briefing", "weather_check", "schedule_overview"],
                "priority": ProactivePriority.MEDIUM
            },
            (7, 0): {
                "type": "commute_check",
                "context": UserContext.TRAVELING,
                "message": "Time to head out? Need traffic updates or public transport info?",
                "actions": ["traffic_check", "transport_schedule", "route_optimization"],
                "priority": ProactivePriority.HIGH
            },
            (9, 0): {
                "type": "work_start",
                "context": UserContext.WORKING,
                "message": "Workday starting. Shall I organize your tasks by priority?",
                "actions": ["task_organization", "meeting_prep", "priority_setting"],
                "priority": ProactivePriority.HIGH
            },
            (12, 0): {
                "type": "lunch_optimization",
                "context": UserContext.ENTERTAINMENT,
                "message": "Lunch time! Want restaurant suggestions based on your preferences?",
                "actions": ["restaurant_suggestions", "nutrition_tracking", "break_reminder"],
                "priority": ProactivePriority.MEDIUM
            },
            (15, 0): {
                "type": "afternoon_productivity",
                "context": UserContext.WORKING,
                "message": "Afternoon productivity dip detected. How about a focus session with Pomodoro?",
                "actions": ["pomodoro_start", "energy_boost_music", "short_break"],
                "priority": ProactivePriority.LOW
            },
            (17, 30): {
                "type": "work_wrapup",
                "context": UserContext.WORKING,
                "message": "Wrapping up work? Need help summarizing today's achievements?",
                "actions": ["achievement_summary", "tomorrow_prep", "task_carryover"],
                "priority": ProactivePriority.MEDIUM
            },
            (20, 0): {
                "type": "evening_planning",
                "context": UserContext.ENTERTAINMENT,
                "message": "Evening plans? I can suggest activities based on your mood.",
                "actions": ["activity_suggestions", "entertainment_options", "relaxation_techniques"],
                "priority": ProactivePriority.LOW
            },
            (22, 0): {
                "type": "sleep_preparation",
                "context": UserContext.RELAXING,
                "message": "Winding down for sleep? Need calming sounds or meditation guidance?",
                "actions": ["sleep_sounds", "meditation_guide", "next_day_preview"],
                "priority": ProactivePriority.MEDIUM
            }
        }
    
    def _initialize_context_triggers(self) -> Dict[UserContext, Dict[str, Any]]:
        """Initialize context-based triggers"""
        return {
            UserContext.WORKING: {
                "check_interval": 45,  # minutes
                "break_suggestions": [
                    "You've been working intensely. Time for a 5-minute stretch?",
                    "Consider the 20-20-20 rule: look 20 feet away for 20 seconds.",
                    "Productivity tip: Try time-blocking your next task."
                ],
                "optimization_suggestions": [
                    "I notice you work best in the morning. Schedule important tasks then.",
                    "Your focus peaks after breaks. Try 25-minute work sessions.",
                    "Consider using noise-cancelling features for better concentration."
                ],
                "priority": ProactivePriority.LOW
            },
            UserContext.STUDYING: {
                "check_interval": 50,
                "break_suggestions": [
                    "Study break! Research shows breaks improve retention.",
                    "Try explaining what you learned to reinforce understanding.",
                    "Active recall time: Quiz yourself on recent material."
                ],
                "optimization_suggestions": [
                    "Spaced repetition would help with this material.",
                    "Create mind maps for complex topics.",
                    "Teach-back method: Explain concepts aloud."
                ],
                "priority": ProactivePriority.LOW
            },
            UserContext.CODING: {
                "check_interval": 60,
                "break_suggestions": [
                    "Code review time? Step back and look at the bigger picture.",
                    "Consider pair programming for complex logic.",
                    "Documentation break: Update comments while they're fresh."
                ],
                "optimization_suggestions": [
                    "Refactor suggestion: Extract that repeated logic into a function.",
                    "Consider adding error handling to your recent code.",
                    "Unit test opportunity for the module you're working on."
                ],
                "priority": ProactivePriority.LOW
            },
            UserContext.LEARNING: {
                "check_interval": 40,
                "break_suggestions": [
                    "Learning break! Let your brain consolidate the information.",
                    "Try a different learning modality (visual/auditory/kinesthetic).",
                    "Connect new knowledge to what you already know."
                ],
                "optimization_suggestions": [
                    "Try the Feynman technique for complex concepts.",
                    "Create flashcards for spaced repetition.",
                    "Find practical applications for what you're learning."
                ],
                "priority": ProactivePriority.LOW
            }
        }
    
    def _load_preferences(self) -> Dict[str, Any]:
        """Load user preferences"""
        pref_file = os.path.join(self.data_dir, "user_preferences.json")
        try:
            with open(pref_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "proactive_frequency": "medium",
                "notification_preferences": {
                    "work_hours": True,
                    "personal_time": True,
                    "weekends": False,
                    "urgent_only": False
                },
                "learning_topics": [],
                "avoid_topics": [],
                "preferred_suggestion_types": ["productivity", "health", "learning"],
                "quiet_hours": [(23, 0), (6, 0)],  # 11 PM to 6 AM
                "response_history": deque(maxlen=100)
            }
    
    def _save_preferences(self):
        """Save user preferences"""
        pref_file = os.path.join(self.data_dir, "user_preferences.json")
        with open(pref_file, 'w') as f:
            # Convert deque to list for JSON serialization
            prefs = self.user_preferences.copy()
            if 'response_history' in prefs:
                prefs['response_history'] = list(prefs['response_history'])
            json.dump(prefs, f, indent=2)
    
    def _load_learned_data(self):
        """Load learned patterns and history"""
        patterns_file = os.path.join(self.data_dir, "user_patterns.pkl")
        history_file = os.path.join(self.data_dir, "context_history.json")
        
        try:
            with open(patterns_file, 'rb') as f:
                self.user_patterns = pickle.load(f)
        except FileNotFoundError:
            pass
        
        try:
            with open(history_file, 'r') as f:
                history_data = json.load(f)
                self.context_history = deque(history_data.get("context_history", []), maxlen=1000)
                self.suggestion_history = deque(history_data.get("suggestion_history", []), maxlen=500)
                self.stats.update(history_data.get("stats", self.stats))
        except FileNotFoundError:
            pass
    
    def _save_learned_data(self):
        """Save learned patterns and history"""
        patterns_file = os.path.join(self.data_dir, "user_patterns.pkl")
        history_file = os.path.join(self.data_dir, "context_history.json")
        
        with open(patterns_file, 'wb') as f:
            pickle.dump(self.user_patterns, f)
        
        with open(history_file, 'w') as f:
            history_data = {
                "context_history": list(self.context_history),
                "suggestion_history": list(self.suggestion_history),
                "stats": self.stats,
                "last_updated": datetime.datetime.now().isoformat()
            }
            json.dump(history_data, f, indent=2)
    
    def _initialize_ml_models(self):
        """Initialize machine learning models"""
        try:
            model_file = os.path.join(self.data_dir, "pattern_classifier.pkl")
            if os.path.exists(model_file):
                with open(model_file, 'rb') as f:
                    self.pattern_classifier = pickle.load(f)
        except:
            pass
        
        if self.pattern_classifier is None:
            # Initialize with default classifier
            self.pattern_classifier = RandomForestClassifier(
                n_estimators=50,
                random_state=42
            )
    
    def update_user_context(self, context: Dict[str, Any]):
        """Update current user context"""
        current_time = datetime.datetime.now()
        
        context_entry = {
            "timestamp": current_time.isoformat(),
            "context": context,
            "metadata": {
                "day_of_week": current_time.weekday(),
                "hour_of_day": current_time.hour,
                "minute_of_hour": current_time.minute,
                "is_weekend": current_time.weekday() >= 5
            }
        }
        
        self.context_history.append(context_entry)
        
        # Extract patterns if enough context exists
        if len(self.context_history) >= 10:
            self._extract_patterns_from_context()
        
        self._save_learned_data()
    
    def _extract_patterns_from_context(self):
        """Extract patterns from context history"""
        if len(self.context_history) < 10:
            return
        
        recent_contexts = list(self.context_history)[-10:]
        
        # Group contexts by time and type
        context_by_hour = defaultdict(list)
        for ctx in recent_contexts:
            hour = datetime.datetime.fromisoformat(ctx["timestamp"]).hour
            context_type = ctx["context"].get("activity_type", "unknown")
            context_by_hour[hour].append(context_type)
        
        # Identify patterns
        for hour, activities in context_by_hour.items():
            if len(activities) >= 3:  # Need at least 3 occurrences to form a pattern
                activity_counter = defaultdict(int)
                for activity in activities:
                    activity_counter[activity] += 1
                
                most_common = max(activity_counter.items(), key=lambda x: x[1])
                if most_common[1] >= 3:  # Same activity at least 3 times
                    pattern_hash = hashlib.md5(
                        f"{hour}_{most_common[0]}".encode()
                    ).hexdigest()[:16]
                    
                    if pattern_hash not in self.user_patterns:
                        # Try to determine context enum
                        context_enum = self._map_activity_to_context(most_common[0])
                        
                        pattern = UserPattern(
                            pattern_hash=pattern_hash,
                            context=context_enum,
                            time_window=(hour, hour+1),
                            frequency=1,
                            last_observed=datetime.datetime.now().isoformat(),
                            typical_actions=self._suggest_actions_for_context(context_enum),
                            success_rate=0.5,  # Default
                            learned_at=datetime.datetime.now().isoformat()
                        )
                        self.user_patterns[pattern_hash] = pattern
                        self.stats["patterns_learned"] += 1
    
    def _map_activity_to_context(self, activity: str) -> UserContext:
        """Map activity string to UserContext enum"""
        mapping = {
            "working": UserContext.WORKING,
            "studying": UserContext.STUDYING,
            "coding": UserContext.CODING,
            "reading": UserContext.LEARNING,
            "watching": UserContext.ENTERTAINMENT,
            "gaming": UserContext.ENTERTAINMENT,
            "chatting": UserContext.COMMUNICATION,
            "browsing": UserContext.SHOPPING,
            "relaxing": UserContext.RELAXING
        }
        return mapping.get(activity.lower(), UserContext.WORKING)
    
    def _suggest_actions_for_context(self, context: UserContext) -> List[str]:
        """Suggest actions based on context"""
        action_suggestions = {
            UserContext.WORKING: [
                "task_prioritization",
                "meeting_preparation",
                "email_organization",
                "focus_sessions",
                "break_planning"
            ],
            UserContext.STUDYING: [
                "flashcard_creation",
                "study_session_planning",
                "concept_review",
                "practice_tests",
                "resource_finding"
            ],
            UserContext.CODING: [
                "code_review",
                "debugging_assistance",
                "documentation_writing",
                "testing_setup",
                "deployment_preparation"
            ],
            UserContext.LEARNING: [
                "topic_research",
                "skill_practice",
                "knowledge_testing",
                "application_finding",
                "progress_tracking"
            ]
        }
        return action_suggestions.get(context, [])
    
    def check_proactive_events(self, current_context: Optional[Dict[str, Any]] = None) -> List[ProactiveEvent]:
        """Check for and generate proactive events"""
        current_time = datetime.datetime.now()
        events = []
        
        # Check if we're in quiet hours
        if self._is_quiet_hour(current_time):
            return events
        
        # 1. Time-based triggers
        time_event = self._check_time_based_triggers(current_time)
        if time_event and self._should_trigger_event(time_event):
            events.append(time_event)
        
        # 2. Context-based triggers
        if current_context:
            context_event = self._check_context_based_triggers(current_context, current_time)
            if context_event and self._should_trigger_event(context_event):
                events.append(context_event)
        
        # 3. Pattern-based predictions
        prediction_event = self._generate_pattern_based_prediction(current_time)
        if prediction_event and self._should_trigger_event(prediction_event):
            events.append(prediction_event)
        
        # 4. ML-based suggestions
        ml_event = self._generate_ml_based_suggestion(current_context, current_time)
        if ml_event and self._should_trigger_event(ml_event):
            events.append(ml_event)
        
        # 5. External data triggers (weather, news, etc.)
        external_event = self._check_external_triggers(current_time)
        if external_event and self._should_trigger_event(external_event):
            events.append(external_event)
        
        # 6. Health and wellness checks
        wellness_event = self._check_wellness_triggers(current_context, current_time)
        if wellness_event and self._should_trigger_event(wellness_event):
            events.append(wellness_event)
        
        # Update last proactive time
        if events:
            self.last_proactive_time = current_time
            
            # Store in history
            for event in events:
                self.suggestion_history.append({
                    "event_type": event.event_type.value,
                    "message": event.message,
                    "timestamp": event.timestamp,
                    "priority": event.priority.value,
                    "confidence": event.confidence
                })
                self.stats["total_events_generated"] += 1
                self.stats["events_by_type"][event.event_type.value] += 1
                self.stats["events_by_priority"][event.priority.value] += 1
        
        self._save_learned_data()
        return events
    
    def _check_time_based_triggers(self, current_time: datetime.datetime) -> Optional[ProactiveEvent]:
        """Check time-based triggers"""
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        for (trigger_hour, trigger_minute), trigger_data in self.time_triggers.items():
            # Check if current time is within 15 minutes of trigger time
            time_diff = (current_hour * 60 + current_minute) - (trigger_hour * 60 + trigger_minute)
            if 0 <= time_diff <= 15:
                # Check if we triggered this recently
                last_trigger = self._get_last_trigger_time(trigger_data["type"])
                if last_trigger and (current_time - last_trigger).total_seconds() < 3600:
                    continue  # Triggered within last hour, skip
                
                context = {
                    "trigger_type": "time_based",
                    "hour": current_hour,
                    "minute": current_minute,
                    "day_of_week": current_time.weekday()
                }
                
                return ProactiveEvent(
                    event_type=ProactiveEventType.SUGGESTION,
                    message=trigger_data["message"],
                    priority=trigger_data["priority"],
                    timestamp=current_time.isoformat(),
                    context=context,
                    confidence=0.8,
                    action_items=trigger_data.get("actions", []),
                    metadata={"trigger_type": trigger_data["type"]}
                )
        
        return None
    
    def _check_context_based_triggers(self, context: Dict[str, Any], 
                                     current_time: datetime.datetime) -> Optional[ProactiveEvent]:
        """Check context-based triggers"""
        activity_type = context.get("activity_type")
        if not activity_type:
            return None
        
        # Map activity to context enum
        context_enum = self._map_activity_to_context(activity_type)
        if context_enum not in self.context_triggers:
            return None
        
        trigger_config = self.context_triggers[context_enum]
        activity_duration = context.get("activity_duration_minutes", 0)
        
        # Check if activity duration exceeds threshold
        if activity_duration >= trigger_config["check_interval"]:
            # Calculate break suggestion probability based on duration
            probability = min(1.0, activity_duration / (trigger_config["check_interval"] * 2))
            
            if random.random() < probability:  # Higher probability for longer sessions
                context_data = {
                    "trigger_type": "context_based",
                    "activity_type": activity_type,
                    "duration_minutes": activity_duration,
                    "context": context_enum.value
                }
                
                return ProactiveEvent(
                    event_type=ProactiveEventType.BREAK,
                    message=random.choice(trigger_config["break_suggestions"]),
                    priority=trigger_config["priority"],
                    timestamp=current_time.isoformat(),
                    context=context_data,
                    confidence=probability,
                    action_items=["take_break", "stretch", "hydrate"],
                    metadata={"activity_duration": activity_duration}
                )
        
        return None
    
    def _generate_pattern_based_prediction(self, current_time: datetime.datetime) -> Optional[ProactiveEvent]:
        """Generate predictions based on learned patterns"""
        current_hour = current_time.hour
        weekday = current_time.weekday()
        
        # Find patterns that match current time
        matching_patterns = []
        for pattern in self.user_patterns.values():
            start_hour, end_hour = pattern.time_window
            if start_hour <= current_hour < end_hour:
                # Check if pattern typically occurs on this weekday
                # (Simplified - in production, track weekday patterns)
                if pattern.frequency >= 3:  # Well-established pattern
                    matching_patterns.append(pattern)
        
        if matching_patterns:
            # Use the most frequent pattern
            best_pattern = max(matching_patterns, key=lambda p: p.frequency)
            
            # Only predict with sufficient confidence
            if best_pattern.success_rate >= 0.6:
                context = {
                    "trigger_type": "pattern_based",
                    "pattern_hash": best_pattern.pattern_hash,
                    "context": best_pattern.context.value,
                    "frequency": best_pattern.frequency
                }
                
                prediction_message = self._generate_prediction_message(best_pattern, current_time)
                
                return ProactiveEvent(
                    event_type=ProactiveEventType.PREDICTION,
                    message=prediction_message,
                    priority=ProactivePriority.LOW,
                    timestamp=current_time.isoformat(),
                    context=context,
                    confidence=best_pattern.success_rate,
                    action_items=best_pattern.typical_actions[:3],
                    metadata={
                        "pattern_frequency": best_pattern.frequency,
                        "last_observed": best_pattern.last_observed
                    }
                )
        
        return None
    
    def _generate_prediction_message(self, pattern: UserPattern, 
                                    current_time: datetime.datetime) -> str:
        """Generate prediction message based on pattern"""
        time_of_day = self._get_time_of_day(current_time)
        
        messages = {
            UserContext.WORKING: [
                f"Based on your patterns, this is typically when you start working. Need help organizing tasks?",
                f"I notice you often work around this time. Want to jump into your prioritized tasks?",
                f"Your productive hours are starting. Shall I set up your work environment?"
            ],
            UserContext.STUDYING: [
                f"Study time approaching based on your patterns. Need me to prepare study materials?",
                f"This is usually when you study. Want to review flashcards or set a study timer?",
                f"Learning session time. Need topic suggestions or resources?"
            ],
            UserContext.CODING: [
                f"Coding session pattern detected. Need me to open your development environment?",
                f"Typically when you code. Want to continue where you left off or start something new?",
                f"Development time. Need debugging tools or documentation?"
            ],
            UserContext.LEARNING: [
                f"Learning time based on your habits. Want to explore a new topic today?",
                f"This is when you usually learn new things. Need course recommendations?",
                f"Skill development time. What would you like to practice today?"
            ]
        }
        
        default_message = f"Based on your habits, you might want to start {pattern.context.value}. Can I help?"
        
        return random.choice(messages.get(pattern.context, [default_message]))
    
    def _generate_ml_based_suggestion(self, current_context: Optional[Dict[str, Any]],
                                     current_time: datetime.datetime) -> Optional[ProactiveEvent]:
        """Generate suggestions using ML models"""
        # This is a placeholder for ML-based suggestions
        # In production, this would use trained models
        
        # For now, generate based on time of day and context
        time_of_day = self._get_time_of_day(current_time)
        
        suggestions_by_time = {
            "morning": [
                "How about starting with a morning planning session?",
                "Want to review your goals for today?",
                "Morning energy high - perfect for creative work!"
            ],
            "afternoon": [
                "Afternoon productivity boost: Try the Pomodoro technique.",
                "Need an energy break? How about a quick walk or stretch?",
                "Time to review morning progress and adjust plans."
            ],
            "evening": [
                "Evening wind-down: Reflect on today's achievements.",
                "Planning for tomorrow? I can help organize your tasks.",
                "Relaxation time: Want some calming music or sounds?"
            ]
        }
        
        if time_of_day in suggestions_by_time:
            # Check user preferences for suggestion frequency
            if random.random() < 0.3:  # 30% chance for ML suggestions
                context = {
                    "trigger_type": "ml_based",
                    "time_of_day": time_of_day,
                    "model_confidence": 0.7
                }
                
                return ProactiveEvent(
                    event_type=ProactiveEventType.SUGGESTION,
                    message=random.choice(suggestions_by_time[time_of_day]),
                    priority=ProactivePriority.INFO,
                    timestamp=current_time.isoformat(),
                    context=context,
                    confidence=0.7,
                    action_items=["consider_suggestion", "provide_feedback"],
                    metadata={"model_type": "time_based_heuristic"}
                )
        
        return None
    
    def _check_external_triggers(self, current_time: datetime.datetime) -> Optional[ProactiveEvent]:
        """Check external data sources for triggers"""
        current_hour = current_time.hour
        
        # Weather check in morning
        if 6 <= current_hour <= 8:
            # 50% chance to suggest weather check
            if random.random() < 0.5:
                context = {
                    "trigger_type": "external",
                    "data_source": "weather",
                    "time_of_day": "morning"
                }
                
                return ProactiveEvent(
                    event_type=ProactiveEventType.SUGGESTION,
                    message=f"Good morning! Want a weather update before planning your day?",
                    priority=ProactivePriority.LOW,
                    timestamp=current_time.isoformat(),
                    context=context,
                    confidence=0.9,
                    action_items=["check_weather", "plan_activities"],
                    metadata={"external_api": "weather"}
                )
        
        # News check during commute hours
        if (7 <= current_hour <= 9) or (17 <= current_hour <= 19):
            # 40% chance to suggest news
            if random.random() < 0.4:
                context = {
                    "trigger_type": "external",
                    "data_source": "news",
                    "time_of_day": "commute"
                }
                
                return ProactiveEvent(
                    event_type=ProactiveEventType.SUGGESTION,
                    message=f"Commute time. Want the latest news headlines?",
                    priority=ProactivePriority.LOW,
                    timestamp=current_time.isoformat(),
                    context=context,
                    confidence=0.8,
                    action_items=["read_news", "listen_podcast"],
                    metadata={"external_api": "news"}
                )
        
        return None
    
    def _check_wellness_triggers(self, current_context: Optional[Dict[str, Any]],
                                current_time: datetime.datetime) -> Optional[ProactiveEvent]:
        """Check health and wellness triggers"""
        current_hour = current_time.hour
        
        # Hydration reminder
        if 8 <= current_hour <= 20:
            # Check last hydration suggestion
            last_hydration = self._get_last_event_of_type("hydration")
            if last_hydration:
                last_time = datetime.datetime.fromisoformat(last_hydration["timestamp"])
                if (current_time - last_time).total_seconds() < 7200:  # 2 hours
                    return None
            
            # 40% chance for hydration reminder
            if random.random() < 0.4:
                context = {
                    "trigger_type": "wellness",
                    "category": "hydration",
                    "hour": current_hour
                }
                
                return ProactiveEvent(
                    event_type=ProactiveEventType.REMINDER,
                    message="Remember to stay hydrated! Your body needs water to function optimally.",
                    priority=ProactivePriority.INFO,
                    timestamp=current_time.isoformat(),
                    context=context,
                    confidence=0.95,
                    action_items=["drink_water", "set_hydration_reminder"],
                    metadata={"wellness_category": "hydration"}
                )
        
        # Posture reminder during work hours
        if 9 <= current_hour <= 18 and current_context and \
           current_context.get("activity_type") in ["working", "coding", "studying"]:
            
            # Check last posture suggestion
            last_posture = self._get_last_event_of_type("posture")
            if last_posture:
                last_time = datetime.datetime.fromisoformat(last_posture["timestamp"])
                if (current_time - last_time).total_seconds() < 3600:  # 1 hour
                    return None
            
            # 30% chance for posture reminder
            if random.random() < 0.3:
                context = {
                    "trigger_type": "wellness",
                    "category": "posture",
                    "activity": current_context.get("activity_type")
                }
                
                return ProactiveEvent(
                    event_type=ProactiveEventType.REMINDER,
                    message="Posture check! Sit up straight, relax your shoulders, and take a deep breath.",
                    priority=ProactivePriority.INFO,
                    timestamp=current_time.isoformat(),
                    context=context,
                    confidence=0.9,
                    action_items=["adjust_posture", "stretch", "deep_breath"],
                    metadata={"wellness_category": "posture"}
                )
        
        return None
    
    def _get_last_event_of_type(self, event_type: str) -> Optional[Dict[str, Any]]:
        """Get last event of specific type from history"""
        for event in reversed(self.suggestion_history):
            if event.get("metadata", {}).get("wellness_category") == event_type:
                return event
        return None
    
    def _get_last_trigger_time(self, trigger_type: str) -> Optional[datetime.datetime]:
        """Get last time a specific trigger type was activated"""
        for event in reversed(self.suggestion_history):
            if event.get("metadata", {}).get("trigger_type") == trigger_type:
                return datetime.datetime.fromisoformat(event["timestamp"])
        return None
    
    def _get_time_of_day(self, current_time: datetime.datetime) -> str:
        """Get time of day category"""
        hour = current_time.hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def _is_quiet_hour(self, current_time: datetime.datetime) -> bool:
        """Check if current time is in user's quiet hours"""
        current_hour = current_time.hour
        for start_hour, end_hour in self.user_preferences.get("quiet_hours", []):
            if start_hour <= current_hour < end_hour:
                return True
        return False
    
    def _should_trigger_event(self, event: ProactiveEvent) -> bool:
        """Determine if an event should be triggered based on preferences and history"""
        # Check user preferences
        if not self.user_preferences.get("notification_preferences", {}).get("work_hours", True):
            current_hour = datetime.datetime.now().hour
            if 9 <= current_hour <= 17:  # Work hours
                return False
        
        # Check if similar event was recently triggered
        recent_events = list(self.suggestion_history)[-10:]  # Last 10 events
        for recent_event in recent_events:
            if (recent_event.get("message") == event.message or 
                (recent_event.get("metadata", {}).get("trigger_type") == 
                 event.metadata.get("trigger_type"))):
                
                recent_time = datetime.datetime.fromisoformat(recent_event["timestamp"])
                time_diff = (datetime.datetime.now() - recent_time).total_seconds()
                
                # Don't trigger same event within 30 minutes
                if time_diff < 1800:
                    return False
        
        # Check event priority against user preferences
        if self.user_preferences.get("notification_preferences", {}).get("urgent_only", False):
            return event.priority in [ProactivePriority.CRITICAL, ProactivePriority.HIGH]
        
        return True
    
    def provide_feedback(self, event_id: str, feedback: bool, notes: str = ""):
        """Provide feedback on a proactive event"""
        # Find the event in history (simplified - would use event_id in production)
        if self.suggestion_history:
            # Update last event's feedback
            last_event = self.suggestion_history[-1]
            last_event["feedback"] = feedback
            last_event["feedback_notes"] = notes
            last_event["feedback_timestamp"] = datetime.datetime.now().isoformat()
            
            # Update statistics
            if feedback:
                self.stats["user_feedback_positive"] += 1
            else:
                self.stats["user_feedback_negative"] += 1
            
            # Update pattern success rates if applicable
            if "pattern_hash" in last_event.get("context", {}):
                pattern_hash = last_event["context"]["pattern_hash"]
                if pattern_hash in self.user_patterns:
                    pattern = self.user_patterns[pattern_hash]
                    total_feedback = pattern.frequency
                    current_success = pattern.success_rate * total_feedback
                    
                    if feedback:
                        current_success += 1
                    
                    pattern.frequency += 1
                    pattern.success_rate = current_success / pattern.frequency
                    pattern.last_observed = datetime.datetime.now().isoformat()
            
            self.feedback_history.append({
                "event_type": last_event.get("event_type"),
                "message": last_event.get("message"),
                "feedback": feedback,
                "notes": notes,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            self._save_learned_data()
    
    def update_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences"""
        self.user_preferences.update(preferences)
        self._save_preferences()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        total_feedback = self.stats["user_feedback_positive"] + self.stats["user_feedback_negative"]
        feedback_accuracy = (
            self.stats["user_feedback_positive"] / total_feedback * 100
            if total_feedback > 0 else 0
        )
        
        return {
            "user_name": self.user_name,
            "total_events_generated": self.stats["total_events_generated"],
            "events_by_type": dict(self.stats["events_by_type"]),
            "events_by_priority": dict(self.stats["events_by_priority"]),
            "patterns_learned": self.stats["patterns_learned"],
            "user_feedback": {
                "positive": self.stats["user_feedback_positive"],
                "negative": self.stats["user_feedback_negative"],
                "accuracy_percentage": round(feedback_accuracy, 2)
            },
            "context_history_size": len(self.context_history),
            "suggestion_history_size": len(self.suggestion_history),
            "active_patterns": len(self.user_patterns),
            "user_preferences_summary": {
                "proactive_frequency": self.user_preferences.get("proactive_frequency", "medium"),
                "preferred_suggestion_types": self.user_preferences.get("preferred_suggestion_types", []),
                "quiet_hours": self.user_preferences.get("quiet_hours", [])
            }
        }
    
    def get_recent_suggestions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent proactive suggestions"""
        return list(self.suggestion_history)[-limit:]
    
    def get_pattern_insights(self) -> Dict[str, Any]:
        """Get insights from learned patterns"""
        insights = {
            "peak_productivity_hours": defaultdict(int),
            "common_contexts": defaultdict(int),
            "pattern_strengths": []
        }
        
        for pattern in self.user_patterns.values():
            start_hour, _ = pattern.time_window
            insights["peak_productivity_hours"][start_hour] += pattern.frequency
            insights["common_contexts"][pattern.context.value] += pattern.frequency
            
            insights["pattern_strengths"].append({
                "context": pattern.context.value,
                "time_window": f"{start_hour:02d}:00",
                "frequency": pattern.frequency,
                "success_rate": round(pattern.success_rate, 2),
                "typical_actions": pattern.typical_actions[:3]
            })
        
        # Sort insights
        insights["peak_productivity_hours"] = dict(sorted(
            insights["peak_productivity_hours"].items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        insights["common_contexts"] = dict(sorted(
            insights["common_contexts"].items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        insights["pattern_strengths"].sort(key=lambda x: x["frequency"], reverse=True)
        
        return insights
    
    def clear_history(self, history_type: str = "all"):
        """Clear specified history"""
        if history_type in ["suggestions", "all"]:
            self.suggestion_history.clear()
        if history_type in ["context", "all"]:
            self.context_history.clear()
        if history_type in ["patterns", "all"]:
            self.user_patterns.clear()
            self.stats["patterns_learned"] = 0
        
        self._save_learned_data()
        return f"Cleared {history_type} history."


# Example usage and testing
if __name__ == "__main__":
    print("🧠 Testing Advanced Proactive Assistant...")
    print("=" * 60)
    
    # Initialize assistant
    assistant = AdvancedProactiveAssistant("Prince")
    
    # Simulate context updates
    print("\n📝 Simulating context updates...")
    contexts = [
        {"activity_type": "working", "activity_duration_minutes": 30},
        {"activity_type": "coding", "activity_duration_minutes": 75},
        {"activity_type": "studying", "activity_duration_minutes": 55},
        {"activity_type": "reading", "activity_duration_minutes": 40}
    ]
    
    for i, context in enumerate(contexts, 1):
        print(f"\nUpdate {i}: {context['activity_type']} for {context['activity_duration_minutes']} min")
        assistant.update_user_context(context)
    
    # Check for proactive events
    print("\n🔔 Checking for proactive events...")
    events = assistant.check_proactive_events(contexts[1])  # Use coding context
    
    if events:
        print(f"\n✅ Generated {len(events)} proactive event(s):")
        for event in events:
            print(f"\n  Type: {event.event_type.value}")
            print(f"  Message: {event.message}")
            print(f"  Priority: {event.priority.value}")
            print(f"  Confidence: {event.confidence:.2f}")
            
            # Simulate feedback
            assistant.provide_feedback(
                event_id="test",
                feedback=random.choice([True, False]),
                notes="Test feedback"
            )
    else:
        print("\n  ⚠️ No proactive events generated (might be due to timing or preferences)")
    
    # Get statistics
    print("\n📊 Assistant Statistics:")
    stats = assistant.get_statistics()
    print(f"  • Total events generated: {stats['total_events_generated']}")
    print(f"  • Patterns learned: {stats['patterns_learned']}")
    print(f"  • Positive feedback: {stats['user_feedback']['positive']}")
    print(f"  • Negative feedback: {stats['user_feedback']['negative']}")
    
    # Get pattern insights
    print("\n🔍 Pattern Insights:")
    insights = assistant.get_pattern_insights()
    print(f"  • Common contexts: {list(insights['common_contexts'].keys())[:3]}")
    
    if insights["pattern_strengths"]:
        strongest_pattern = insights["pattern_strengths"][0]
        print(f"  • Strongest pattern: {strongest_pattern['context']} at {strongest_pattern['time_window']}")
        print(f"    Frequency: {strongest_pattern['frequency']}, Success rate: {strongest_pattern['success_rate']}")
    
    print("\n✅ Advanced Proactive Assistant test complete!")