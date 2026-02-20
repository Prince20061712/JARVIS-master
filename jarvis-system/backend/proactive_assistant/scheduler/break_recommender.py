from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from utils.logger import logger

class BreakRecommender:
    """
    Suggests study breaks using the Pomodoro technique and user's focus patterns.
    Adapts break length based on session intensity and fatigue signals.
    """
    def __init__(self, work_duration_mins: int = 25, short_break_mins: int = 5, long_break_mins: int = 20):
        self.work_duration = work_duration_mins
        self.short_break = short_break_mins
        self.long_break = long_break_mins
        self.pomodoros_completed = 0
        self.session_start = datetime.now()

    def suggest_break(self, current_session_mins: int) -> Optional[Dict[str, Any]]:
        """Determines if a break is due based on time elapsed."""
        if current_session_mins >= self.work_duration:
            self.pomodoros_completed += 1
            break_type = "long" if self.pomodoros_completed % 4 == 0 else "short"
            length = self.long_break if break_type == "long" else self.short_break
            
            return {
                "type": break_type,
                "duration_mins": length,
                "message": self._get_break_activity(break_type)
            }
        return None

    def optimize_break_length(self, student_stress: float) -> int:
        """Increases break duration if high stress is detected."""
        if student_stress > 0.7:
            logger.info("Increasing break duration due to high student stress.")
            return self.short_break + 5
        return self.short_break

    def _get_break_activity(self, break_type: str) -> str:
        short_activities = ["Stretch for 2 minutes", "Rest your eyes", "Quick water break"]
        long_activities = ["Go for a short walk", "A quick snack break", "Listen to a calming song"]
        
        if break_type == "short":
            return random.choice(short_activities) if 'random' in globals() else short_activities[0]
        return random.choice(long_activities) if 'random' in globals() else long_activities[0]
