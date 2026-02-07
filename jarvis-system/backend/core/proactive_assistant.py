#!/usr/bin/env python3
"""
Proactive Assistant Module
Anticipates user needs and provides timely suggestions
"""

import datetime
import random
import time
from enum import Enum

class ProactiveEventType(Enum):
    REMINDER = "reminder"
    SUGGESTION = "suggestion"
    CHECKIN = "checkin"
    ALERT = "alert"
    MOTIVATION = "motivation"
    BREAK = "break"

class ProactiveAssistant:
    def __init__(self, user_name="User"):
        self.user_name = user_name
        self.last_proactive_time = datetime.datetime.now()
        self.proactive_interval = 1800  # 30 minutes in seconds
        self.user_habits = {}
        self.last_activity_change = datetime.datetime.now()
        self.activity_duration = 0
        self.suggestion_history = []
        
        # Time-based triggers
        self.time_triggers = {
            (8, 0): ("morning_start", "Good morning! Ready to start your day?"),
            (10, 0): ("morning_checkin", "How's your morning going? Need anything?"),
            (13, 0): ("lunch_reminder", "Time for a lunch break!"),
            (15, 0): ("afternoon_energy", "Afternoon energy dip? How about a quick stretch?"),
            (18, 0): ("evening_winddown", "Evening approaching. Time to wrap up?"),
            (20, 0): ("relaxation", "Remember to relax and unwind."),
            (22, 0): ("bedtime_reminder", "Getting late. Consider winding down for bed.")
        }
        
        # Activity-based triggers
        self.activity_triggers = {
            "working": {
                "duration": 45,  # minutes
                "message": "You've been working for 45 minutes. How about a short break?"
            },
            "studying": {
                "duration": 50,
                "message": "Study session alert! Consider taking a 10-minute break."
            },
            "coding": {
                "duration": 60,
                "message": "Coding for an hour straight? Time to rest your eyes."
            }
        }
        
        # Motivational messages
        self.motivational_messages = [
            f"Keep up the great work, {self.user_name}!",
            f"You're making excellent progress, {self.user_name}.",
            f"Remember to take care of yourself while you work.",
            f"Stay hydrated and focused!",
            f"You're doing amazing work today!"
        ]
    
    def update_activity(self, activity_type, start_time=None):
        """Update current activity tracking"""
        if start_time:
            self.last_activity_change = start_time
        else:
            self.last_activity_change = datetime.datetime.now()
        
        self.activity_duration = 0
    
    def check_proactive_actions(self, context=None):
        """Check if proactive action is needed"""
        current_time = datetime.datetime.now()
        
        # Check time since last proactive action
        time_since_last = (current_time - self.last_proactive_time).total_seconds()
        if time_since_last < self.proactive_interval:
            return None
        
        # Check time-based triggers
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        for (trigger_hour, trigger_minute), (trigger_type, message) in self.time_triggers.items():
            if (current_hour == trigger_hour and 
                trigger_minute <= current_minute < trigger_minute + 15):
                self.last_proactive_time = current_time
                return self._create_event(
                    ProactiveEventType.CHECKIN if "checkin" in trigger_type else ProactiveEventType.REMINDER,
                    message,
                    "medium"
                )
        
        # Check activity duration
        if context and context.get("current_activity") != "unknown":
            activity = context.get("current_activity")
            activity_duration_min = context.get("activity_duration_minutes", 0)
            
            if activity in self.activity_triggers:
                trigger_duration = self.activity_triggers[activity]["duration"]
                if activity_duration_min >= trigger_duration:
                    self.last_proactive_time = current_time
                    return self._create_event(
                        ProactiveEventType.BREAK,
                        self.activity_triggers[activity]["message"],
                        "low"
                    )
        
        # Random motivational check-in (10% chance when conditions are right)
        if (current_hour >= 9 and current_hour <= 17 and 
            random.random() < 0.1 and  # 10% chance
            context and context.get("current_activity") in ["working", "studying"]):
            
            self.last_proactive_time = current_time
            return self._create_event(
                ProactiveEventType.MOTIVATION,
                random.choice(self.motivational_messages),
                "low"
            )
        
        # Check for long inactivity (if user hasn't interacted in 2 hours during work hours)
        if hasattr(self, 'last_user_interaction'):
            inactivity_minutes = (current_time - self.last_user_interaction).seconds // 60
            if (current_hour >= 9 and current_hour <= 17 and 
                inactivity_minutes >= 120):
                self.last_proactive_time = current_time
                return self._create_event(
                    ProactiveEventType.CHECKIN,
                    f"Long time no see, {self.user_name}! Everything alright?",
                    "medium"
                )
        
        return None
    
    def _create_event(self, event_type, message, priority):
        """Create a proactive event"""
        event = {
            "type": event_type.value,
            "type_name": event_type.name,
            "message": message,
            "priority": priority,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Store in history
        self.suggestion_history.append(event)
        if len(self.suggestion_history) > 50:
            self.suggestion_history.pop(0)
        
        return event
    
    def record_user_interaction(self):
        """Record when user last interacted"""
        self.last_user_interaction = datetime.datetime.now()
    
    def learn_habit(self, time_of_day, activity, common_actions):
        """Learn user habits based on patterns"""
        key = f"{time_of_day}_{activity}"
        if key not in self.user_habits:
            self.user_habits[key] = {
                "actions": common_actions,
                "frequency": 1,
                "last_observed": datetime.datetime.now()
            }
        else:
            self.user_habits[key]["frequency"] += 1
            self.user_habits[key]["last_observed"] = datetime.datetime.now()
    
    def get_suggestions_based_on_habit(self, time_of_day, activity):
        """Get suggestions based on learned habits"""
        key = f"{time_of_day}_{activity}"
        if key in self.user_habits and self.user_habits[key]["frequency"] >= 3:
            # User frequently does this activity at this time
            common_actions = self.user_habits[key]["actions"]
            if common_actions:
                # Suggest something related to their habits
                suggestions = {
                    "morning_working": "Would you like me to organize your tasks for today?",
                    "afternoon_studying": "How about some background study music?",
                    "evening_entertainment": "Looking for movie recommendations?",
                    "night_relaxing": "Would you like some ambient sounds to relax?"
                }
                
                for pattern, suggestion in suggestions.items():
                    if pattern in key:
                        return suggestion
        
        return None
    
    def check_reminders(self):
        """Check for scheduled reminders"""
        try:
            with open("reminders.txt", "r") as f:
                reminders = f.readlines()
            
            current_time = datetime.datetime.now()
            triggered_reminders = []
            
            for reminder in reminders:
                try:
                    parts = reminder.strip().split(" - Time: ")
                    if len(parts) == 2:
                        reminder_time_str = parts[1]
                        reminder_time = datetime.datetime.strptime(
                            reminder_time_str, 
                            "%H:%M"
                        ).replace(
                            year=current_time.year,
                            month=current_time.month,
                            day=current_time.day
                        )
                        
                        # Check if reminder time is within next 5 minutes
                        time_diff = (reminder_time - current_time).total_seconds()
                        if 0 <= time_diff <= 300:  # 5 minutes in seconds
                            reminder_text = parts[0].split(": ", 1)[1] if ": " in parts[0] else parts[0]
                            triggered_reminders.append(reminder_text)
                except:
                    continue
            
            if triggered_reminders:
                return self._create_event(
                    ProactiveEventType.REMINDER,
                    f"Reminder: {triggered_reminders[0]}",
                    "high"
                )
        
        except FileNotFoundError:
            pass
        
        return None
    
    def check_weather_alert(self):
        """Check for weather alerts"""
        # This is a placeholder - in a real implementation, you'd call a weather API
        # For now, we'll just demonstrate the structure
        current_hour = datetime.datetime.now().hour
        
        if 6 <= current_hour <= 8:
            # Morning weather check
            suggestions = [
                "Good morning! Don't forget to check today's weather before heading out.",
                "Morning! Would you like me to check the weather for today?",
                "Ready for the day? Want a weather update?"
            ]
            
            # Only suggest occasionally (33% chance)
            if random.random() < 0.33:
                return self._create_event(
                    ProactiveEventType.SUGGESTION,
                    random.choice(suggestions),
                    "low"
                )
        
        return None
    
    def check_system_health(self, system_metrics=None):
        """Check system health and suggest optimizations"""
        if not system_metrics:
            return None
        
        alerts = []
        
        # Check CPU usage
        if system_metrics.get("cpu_percent", 0) > 80:
            alerts.append("CPU usage is high. Consider closing unused applications.")
        
        # Check memory
        if system_metrics.get("memory_percent", 0) > 85:
            alerts.append("Memory usage is high. You might want to free up some RAM.")
        
        # Check disk space
        if system_metrics.get("disk_percent", 0) > 90:
            alerts.append("Disk space is running low. Consider cleaning up files.")
        
        if alerts:
            return self._create_event(
                ProactiveEventType.ALERT,
                "System Alert: " + " | ".join(alerts[:2]),  # Limit to 2 alerts
                "high"
            )
        
        return None
    
    def get_time_based_suggestion(self):
        """Get suggestion based on time of day"""
        current_hour = datetime.datetime.now().hour
        
        suggestions = {
            (5, 9): [  # Early morning
                f"Good morning, {self.user_name}! Would you like me to read today's news?",
                f"Morning! How about some uplifting music to start your day?"
            ],
            (9, 12): [  # Late morning
                f"Mid-morning check-in. Need a coffee break suggestion?",
                f"Working hard? Consider taking a 5-minute stretch break."
            ],
            (12, 14): [  # Lunch time
                f"Lunch time! Need restaurant suggestions or recipe ideas?",
                f"Remember to hydrate! Would you like me to set a hydration reminder?"
            ],
            (14, 17): [  # Afternoon
                f"Afternoon energy dip? How about some focus music?",
                f"Productivity tip: Try the Pomodoro technique for better focus."
            ],
            (17, 20): [  # Evening
                f"Evening time! Planning your evening activities?",
                f"Work day ending. Would you like help summarizing today's tasks?"
            ],
            (20, 23): [  # Night
                f"Evening wind-down. How about some relaxing music?",
                f"Before bed, would you like me to set tomorrow's reminders?"
            ],
            (23, 5): [  # Late night
                f"Late night session? Remember to rest when you can.",
                f"Working late? Take care of your health and sleep schedule."
            ]
        }
        
        for (start_hour, end_hour), suggestion_list in suggestions.items():
            if start_hour <= current_hour < end_hour or (start_hour > end_hour and 
                                                         (current_hour >= start_hour or 
                                                          current_hour < end_hour)):
                # Only suggest occasionally (25% chance)
                if random.random() < 0.25:
                    return random.choice(suggestion_list)
        
        return None
    
    def get_statistics(self):
        """Get proactive assistant statistics"""
        return {
            "total_suggestions": len(self.suggestion_history),
            "recent_suggestions": self.suggestion_history[-10:] if self.suggestion_history else [],
            "learned_habits": len(self.user_habits),
            "last_proactive_time": self.last_proactive_time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_habits_summary": {
                key: {
                    "frequency": data["frequency"],
                    "last_observed": data["last_observed"].strftime("%Y-%m-%d %H:%M:%S")
                }
                for key, data in self.user_habits.items()
            }
        }
    
    def clear_history(self):
        """Clear suggestion history"""
        self.suggestion_history = []
        return "Suggestion history cleared."

# Export the class
__all__ = ['ProactiveAssistant', 'ProactiveEventType']

# Quick test function
if __name__ == "__main__":
    print("🧪 Testing Proactive Assistant...")
    print("=" * 50)
    
    assistant = ProactiveAssistant("Prince")
    
    # Test time-based triggers
    print("\n⏰ Testing time-based triggers:")
    for hour in [8, 10, 13, 15, 18, 20, 22]:
        test_time = datetime.datetime.now().replace(hour=hour, minute=5)
        print(f"\nAt {hour:02d}:05:")
        assistant.last_proactive_time = test_time - datetime.timedelta(hours=1)
        result = assistant.check_proactive_actions()
        if result:
            print(f"  ✓ {result['message']}")
        else:
            print("  ✗ No trigger")
    
    # Test activity-based triggers
    print("\n💼 Testing activity-based triggers:")
    context = {
        "current_activity": "working",
        "activity_duration_minutes": 50
    }
    result = assistant.check_proactive_actions(context)
    if result:
        print(f"  ✓ Activity trigger: {result['message']}")
    
    # Test statistics
    print("\n📊 Assistant Statistics:")
    stats = assistant.get_statistics()
    print(f"  • Total suggestions: {stats['total_suggestions']}")
    print(f"  • Learned habits: {stats['learned_habits']}")
    
    print("\n✅ Proactive Assistant test complete!")