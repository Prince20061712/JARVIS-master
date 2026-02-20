from datetime import datetime, time
from typing import Dict, List, Any, Optional
from collections import defaultdict
import numpy as np
from utils.logger import logger

class TimeAnalyzer:
    """
    Analyzes study time usage, peak hours, and break patterns.
    Helps in detecting procrastination and predicting optimal study windows.
    """
    def __init__(self):
        self.session_logs = [] # List of {'start': datetime, 'end': datetime, 'is_productive': bool}
        self.hourly_productivity = defaultdict(list)

    def analyze_time_usage(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates statistics on total time, avg session length, and peak productivity."""
        if not sessions:
            return {"total_hours": 0, "avg_session": 0}

        total_duration = 0
        for s in sessions:
            duration = (s['end'] - s['start']).total_seconds() / 3600.0
            total_duration += duration
            hour = s['start'].hour
            self.hourly_productivity[hour].append(1.0 if s.get('is_productive', True) else 0.0)

        avg_session = total_duration / len(sessions)
        return {
            "total_hours": round(total_duration, 2),
            "avg_session_hours": round(avg_session, 2),
            "peak_hour": self.predict_optimal_time()
        }

    def predict_optimal_time(self) -> Optional[int]:
        """Identifies the hour of the day with the highest productivity scores."""
        if not self.hourly_productivity:
            return None
        
        averages = {h: np.mean(v) for h, v in self.hourly_productivity.items()}
        return max(averages, key=averages.get)

    def detect_procrastination(self, current_time: datetime, scheduled_time: datetime) -> bool:
        """Flags if a session starting significantly later than planned."""
        delay = (current_time - scheduled_time).total_seconds() / 60.0 # minutes
        return delay > 30 # Procrastination if > 30 mins late

    def get_circadian_rhythm(self) -> Dict[int, float]:
        """Returns a simplified productivity mapping across 24 hours."""
        return {h: float(np.mean(v)) if v else 0.5 for h, v in self.hourly_productivity.items()}
