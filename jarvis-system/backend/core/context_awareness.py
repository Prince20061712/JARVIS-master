#!/usr/bin/env python3
"""
Context Awareness Module
Handles time of day, user activities, and contextual understanding
"""

import datetime
from enum import Enum

class TimeOfDay(Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"

class ActivityType(Enum):
    WORKING = "working"
    STUDYING = "studying"
    ENTERTAINMENT = "entertainment"
    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"
    LEISURE = "leisure"
    UNKNOWN = "unknown"

class ContextAwareness:
    def __init__(self, user_name="User"):
        self.user_name = user_name
        self.current_activity = ActivityType.UNKNOWN
        self.last_activity_change = datetime.datetime.now()
        self.activity_duration = 0
        self.context_history = []
        
    def get_time_of_day(self):
        """Determine current time of day"""
        current_hour = datetime.datetime.now().hour
        
        if 5 <= current_hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= current_hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= current_hour < 21:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT
    
    def detect_activity(self, user_input):
        """Detect user activity from input"""
        input_lower = user_input.lower()
        
        # Working activities
        work_keywords = ["code", "program", "write", "work", "project", "debug", 
                        "develop", "build", "create", "design", "implement"]
        if any(keyword in input_lower for keyword in work_keywords):
            return ActivityType.WORKING
        
        # Studying activities
        study_keywords = ["study", "learn", "read", "research", "exam", "test",
                         "homework", "assignment", "course", "tutorial"]
        if any(keyword in input_lower for keyword in study_keywords):
            return ActivityType.STUDYING
        
        # Entertainment activities
        entertainment_keywords = ["play", "watch", "listen", "music", "movie", 
                                 "game", "video", "song", "youtube", "netflix"]
        if any(keyword in input_lower for keyword in entertainment_keywords):
            return ActivityType.ENTERTAINMENT
        
        # Productivity activities
        productivity_keywords = ["remind", "note", "schedule", "plan", "organize",
                                "task", "todo", "calendar", "meeting", "appointment"]
        if any(keyword in input_lower for keyword in productivity_keywords):
            return ActivityType.PRODUCTIVITY
        
        # Communication activities
        communication_keywords = ["email", "message", "call", "chat", "send",
                                 "text", "communicate", "talk", "speak"]
        if any(keyword in input_lower for keyword in communication_keywords):
            return ActivityType.COMMUNICATION
        
        return ActivityType.UNKNOWN
    
    def update_context(self, user_input, jarvis_response=""):
        """Update context based on interaction"""
        time_of_day = self.get_time_of_day()
        new_activity = self.detect_activity(user_input)
        
        # Update activity if changed
        if new_activity != self.current_activity:
            self.last_activity_change = datetime.datetime.now()
            self.current_activity = new_activity
            self.activity_duration = 0
        else:
            self.activity_duration = (datetime.datetime.now() - 
                                     self.last_activity_change).seconds // 60  # in minutes
        
        # Store context
        context_entry = {
            "timestamp": datetime.datetime.now(),
            "time_of_day": time_of_day.value,
            "activity": self.current_activity.value,
            "user_input": user_input[:50],  # Store first 50 chars
            "jarvis_response": jarvis_response[:50] if jarvis_response else ""
        }
        
        self.context_history.append(context_entry)
        # Keep only last 50 context entries
        if len(self.context_history) > 50:
            self.context_history.pop(0)
        
        return context_entry
    
    def get_contextual_greeting(self):
        """Get greeting based on context"""
        time_of_day = self.get_time_of_day()
        greetings = {
            TimeOfDay.MORNING: f"Good morning {self.user_name}! Ready for the day?",
            TimeOfDay.AFTERNOON: f"Good afternoon {self.user_name}. How's your day going?",
            TimeOfDay.EVENING: f"Good evening {self.user_name}. How was your day?",
            TimeOfDay.NIGHT: f"Late night session, {self.user_name}? How can I assist?"
        }
        return greetings.get(time_of_day, f"Hello {self.user_name}.")
    
    def get_activity_suggestion(self):
        """Get suggestion based on current activity"""
        suggestions = {
            ActivityType.WORKING: "Would you like me to play some focus music or set a pomodoro timer?",
            ActivityType.STUDYING: "I can help with research or set study reminders.",
            ActivityType.ENTERTAINMENT: "I can recommend content or adjust media settings.",
            ActivityType.PRODUCTIVITY: "I can help organize tasks or set priorities.",
            ActivityType.COMMUNICATION: "I can help draft messages or manage contacts.",
            ActivityType.LEISURE: "How can I enhance your leisure time?",
            ActivityType.UNKNOWN: "How can I assist you today?"
        }
        return suggestions.get(self.current_activity, "How can I help?")
    
    def get_context_summary(self):
        """Get summary of current context"""
        return {
            "time_of_day": self.get_time_of_day().value,
            "current_activity": self.current_activity.value,
            "activity_duration_minutes": self.activity_duration,
            "last_activity_change": self.last_activity_change.strftime("%H:%M"),
            "context_history_count": len(self.context_history)
        }