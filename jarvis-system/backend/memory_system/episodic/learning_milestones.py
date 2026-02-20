from datetime import datetime
from typing import List, Dict, Any, Optional
from utils.logger import logger

class MilestoneTracker:
    """
    Tracks significant learning events and achievements.
    """
    MILESTONE_TYPES = ["topic_completion", "exam_pass", "skill_mastery", "streak_bonus"]

    def __init__(self):
        self.milestones: List[Dict[str, Any]] = []
        self.streaks: Dict[str, int] = {}  # E.g., {"daily_study": 5}
        self.last_activity: Optional[datetime] = None

    def add_milestone(self, m_type: str, title: str, description: str):
        """Records a new milestone."""
        if m_type not in self.MILESTONE_TYPES:
            logger.warning(f"Unknown milestone type: {m_type}. Using 'skill_mastery' instead.")
            m_type = "skill_mastery"

        achievement = {
            "type": m_type,
            "title": title,
            "description": description,
            "timestamp": datetime.now()
        }
        self.milestones.append(achievement)
        logger.info(f"🏆 Milestone Reached: {title}")
        self._notify_user(achievement)

    def check_daily_streak(self):
        """Checks and updates daily study streaks."""
        now = datetime.now()
        if not self.last_activity:
            self.streaks["daily_study"] = 1
        else:
            delta_days = (now.date() - self.last_activity.date()).days
            if delta_days == 1:
                self.streaks["daily_study"] = self.streaks.get("daily_study", 1) + 1
                
                # Award streak milestones
                streak = self.streaks["daily_study"]
                if streak in [3, 7, 30, 100]:
                    self.add_milestone(
                        "streak_bonus", 
                        f"{streak} Day Streak!", 
                        f"Studied consistently for {streak} days."
                    )
            elif delta_days > 1:
                self.streaks["daily_study"] = 1 # Reset off streak
                
        self.last_activity = now

    def _notify_user(self, achievement: Dict[str, Any]):
        """Stub for connecting to UI/Voice notification systems."""
        # This would typically push to a websocket or TTS engine.
        print(f">>> NOTIFICATION: {achievement['title']} - {achievement['description']} <<<")

    def get_milestones(self) -> List[Dict[str, Any]]:
        return sorted(self.milestones, key=lambda x: x["timestamp"], reverse=True)

    def generate_progress_report(self) -> Dict[str, Any]:
        """Compiles a report of all achievements and current streaks."""
        return {
            "total_milestones": len(self.milestones),
            "current_streaks": self.streaks,
            "recent_achievements": self.get_milestones()[:5]
        }
