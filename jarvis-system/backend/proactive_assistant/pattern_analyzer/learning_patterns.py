"""
Learning Pattern Analyzer for Student Behavior Tracking
"""

import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict
from utils.logger import logger

class LearningPatternAnalyzer:
    """
    Analyzes student learning patterns for personalized recommendations
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.session_history = []
        self.topic_mastery = defaultdict(float)
        self.time_preferences = defaultdict(int)
        self.attention_span = defaultdict(float)
        
    def analyze_session(self, session_data: Dict):
        """Analyze a completed study session"""
        try:
            # Track topic coverage
            for topic in session_data.get('topics_covered', []):
                self.topic_mastery[topic] = self._update_mastery(
                    topic, 
                    session_data.get('performance', 0.5)
                )
            
            # Track time preferences
            ts = session_data.get('timestamp')
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            elif not ts:
                ts = datetime.now()
            
            session_hour = ts.hour
            self.time_preferences[session_hour] += 1
            
            # Calculate attention span
            duration = session_data.get('duration', 0)
            breaks = session_data.get('breaks_taken', 0)
            if duration > 0:
                score = (1 - breaks/duration)
                self.attention_span[duration] = (
                    self.attention_span.get(duration, 0) * 0.7 + 
                    score * 0.3
                )
            
            # Store session
            self.session_history.append(session_data)
            logger.info(f"Analyzed session for {self.user_id}. History count: {len(self.session_history)}")
            
            return self.generate_insights()
        except Exception as e:
            logger.error(f"Error analyzing session for {self.user_id}: {e}")
            return {}
    
    def _update_mastery(self, topic: str, performance: float) -> float:
        """Update topic mastery score"""
        current = self.topic_mastery.get(topic, 0.0)
        # Exponential moving average
        return current * 0.7 + performance * 0.3
    
    def generate_insights(self) -> Dict:
        """Generate learning insights"""
        return {
            'strong_topics': self.get_strong_topics(),
            'weak_topics': self.get_weak_topics(),
            'optimal_study_time': self.get_optimal_study_time(),
            'avg_attention_span': self.get_avg_attention_span(),
            'recommended_session_duration': self.get_recommended_duration(),
            'consistency_score': self.calculate_consistency()
        }
    
    def get_strong_topics(self, threshold=0.7):
        """Get topics with mastery above threshold"""
        return [t for t, m in self.topic_mastery.items() if m > threshold]
    
    def get_weak_topics(self, threshold=0.4):
        """Get topics needing improvement"""
        return [t for t, m in self.topic_mastery.items() if m < threshold]
    
    def get_optimal_study_time(self):
        """Find optimal study time based on history"""
        if not self.time_preferences:
            return None
        return max(self.time_preferences, key=self.time_preferences.get)
    
    def get_avg_attention_span(self):
        """Calculate average attention span"""
        if not self.attention_span:
            return 45  # default 45 minutes
        return float(np.mean(list(self.attention_span.keys())))
    
    def get_recommended_duration(self):
        """Recommend session duration based on attention span"""
        avg_span = self.get_avg_attention_span()
        return min(avg_span * 1.2, 120)  # Cap at 2 hours
    
    def calculate_consistency(self):
        """Calculate study consistency score"""
        if len(self.session_history) < 2:
            return 0.5
        
        # Check regularity of study sessions
        timestamps = []
        for s in self.session_history:
            ts = s.get('timestamp')
            if isinstance(ts, str): ts = datetime.fromisoformat(ts)
            if ts: timestamps.append(ts.timestamp())
        
        if len(timestamps) < 2: return 0.5
        
        intervals = np.diff(sorted(timestamps))
        
        # Lower variance = higher consistency
        variance = np.var(intervals) if len(intervals) > 0 else 0
        consistency = 1 / (1 + variance / (3600 * 24))  # Normalize by day
        
        return float(min(consistency, 1.0))
