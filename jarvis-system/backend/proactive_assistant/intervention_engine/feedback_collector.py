"""
Feedback Collector Module - Enhanced version
Collects, processes, and learns from user feedback on proactive interventions.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import numpy as np
from enum import Enum
import asyncio
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Types of feedback that can be collected."""
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SNOOZED = "snoozed"
    MODIFIED = "modified"
    IGNORED = "ignored"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class FeedbackImportance(Enum):
    """Importance levels for feedback."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class FeedbackCollector:
    """
    Enhanced feedback collection system that learns from user interactions.
    Uses reinforcement learning concepts to improve suggestion quality over time.
    """
    
    def __init__(self, storage_path: str = "data/feedback"):
        """
        Initialize the feedback collector.
        
        Args:
            storage_path: Path to store feedback data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Feedback storage
        self.feedback_history: List[Dict] = []
        self.user_preferences: Dict[str, Any] = {}
        self.context_patterns: Dict[str, List[Dict]] = defaultdict(list)
        
        # Learning parameters
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 0.2
        
        # Quality metrics
        self.suggestion_scores: Dict[str, float] = defaultdict(float)
        self.context_scores: Dict[str, float] = defaultdict(float)
        
        # Load existing data
        self._load_feedback_history()
        self._load_user_preferences()
        
        logger.info("FeedbackCollector initialized successfully")
    
    def _load_feedback_history(self):
        """Load feedback history from storage."""
        history_file = self.storage_path / "feedback_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.feedback_history = data.get('history', [])
                    self.suggestion_scores = defaultdict(
                        float, data.get('suggestion_scores', {})
                    )
                    self.context_scores = defaultdict(
                        float, data.get('context_scores', {})
                    )
                logger.info(f"Loaded {len(self.feedback_history)} feedback entries")
            except Exception as e:
                logger.error(f"Error loading feedback history: {e}")
    
    def _load_user_preferences(self):
        """Load user preferences from storage."""
        prefs_file = self.storage_path / "user_preferences.json"
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r') as f:
                    self.user_preferences = json.load(f)
                logger.info("Loaded user preferences")
            except Exception as e:
                logger.error(f"Error loading user preferences: {e}")
    
    async def collect_feedback(self, 
                              suggestion_id: str,
                              feedback_type: FeedbackType,
                              context: Dict[str, Any],
                              rating: Optional[int] = None,
                              comments: Optional[str] = None,
                              importance: FeedbackImportance = FeedbackImportance.MEDIUM) -> Dict[str, Any]:
        """
        Collect feedback on a suggestion.
        
        Args:
            suggestion_id: Unique identifier for the suggestion
            feedback_type: Type of feedback received
            context: Current context when feedback was given
            rating: Optional numeric rating (1-5)
            comments: Optional textual comments
            importance: Importance level of this feedback
            
        Returns:
            Dictionary with feedback processing results
        """
        try:
            # Create feedback entry
            feedback_entry = {
                'id': self._generate_feedback_id(suggestion_id),
                'suggestion_id': suggestion_id,
                'type': feedback_type.value if isinstance(feedback_type, FeedbackType) else feedback_type,
                'context': context.copy(),
                'rating': rating,
                'comments': comments,
                'importance': importance.value if isinstance(importance, FeedbackImportance) else importance,
                'timestamp': datetime.now().isoformat(),
                'processed': False,
                'learning_outcome': None
            }
            
            # Add to history
            self.feedback_history.append(feedback_entry)
            
            # Update learning models
            learning_result = await self._process_feedback_for_learning(feedback_entry)
            feedback_entry['processed'] = True
            feedback_entry['learning_outcome'] = learning_result
            
            # Update user preferences based on feedback
            self._update_user_preferences(feedback_entry)
            
            # Trim history if too large
            self._trim_history()
            
            # Save to disk
            await self._save_feedback()
            
            logger.info(f"Collected feedback for suggestion {suggestion_id}: {feedback_type}")
            
            return {
                'success': True,
                'feedback_id': feedback_entry['id'],
                'learning_outcome': learning_result,
                'updated_preferences': self._get_relevant_preferences(context)
            }
            
        except Exception as e:
            logger.error(f"Error collecting feedback: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_feedback_id(self, suggestion_id: str) -> str:
        """Generate a unique feedback ID."""
        timestamp = datetime.now().isoformat()
        unique_string = f"{suggestion_id}_{timestamp}_{np.random.random()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    async def _process_feedback_for_learning(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process feedback to improve suggestion quality using reinforcement learning.
        
        Args:
            feedback: Feedback entry to process
            
        Returns:
            Dictionary with learning outcomes
        """
        suggestion_id = feedback['suggestion_id']
        feedback_type = feedback['type']
        context = feedback['context']
        rating = feedback.get('rating', 3)
        
        # Calculate reward based on feedback type and rating
        reward = self._calculate_reward(feedback_type, rating)
        
        # Update suggestion score using Q-learning inspired approach
        current_score = self.suggestion_scores.get(suggestion_id, 0.5)
        new_score = current_score + self.learning_rate * (reward + self.discount_factor * current_score - current_score)
        self.suggestion_scores[suggestion_id] = max(0, min(1, new_score))
        
        # Update context-specific scores
        context_key = self._extract_context_key(context)
        if context_key:
            current_context_score = self.context_scores.get(context_key, 0.5)
            new_context_score = current_context_score + self.learning_rate * (reward - current_context_score)
            self.context_scores[context_key] = max(0, min(1, new_context_score))
        
        # Store pattern
        pattern = {
            'context': context_key,
            'feedback_type': feedback_type,
            'reward': reward,
            'timestamp': feedback['timestamp']
        }
        self.context_patterns[context_key].append(pattern)
        
        # Analyze patterns
        pattern_insights = self._analyze_patterns(context_key)
        
        return {
            'score_update': {
                'suggestion_score': self.suggestion_scores[suggestion_id],
                'context_score': self.context_scores.get(context_key, 0.5)
            },
            'reward_calculated': reward,
            'pattern_insights': pattern_insights,
            'exploration_adjusted': self.exploration_rate
        }
    
    def _calculate_reward(self, feedback_type: str, rating: Optional[int] = None) -> float:
        """
        Calculate reward value for feedback.
        
        Args:
            feedback_type: Type of feedback
            rating: Optional numeric rating
            
        Returns:
            Reward value between -1 and 1
        """
        base_rewards = {
            'accepted': 1.0,
            'positive': 0.8,
            'modified': 0.5,
            'neutral': 0.0,
            'snoozed': -0.2,
            'ignored': -0.5,
            'rejected': -0.8,
            'negative': -1.0
        }
        
        reward = base_rewards.get(feedback_type, 0.0)
        
        # Adjust for rating if provided
        if rating is not None:
            rating_reward = (rating - 3) / 2  # Convert 1-5 to -1 to 1
            reward = 0.7 * reward + 0.3 * rating_reward
        
        return reward
    
    def _extract_context_key(self, context: Dict[str, Any]) -> str:
        """Extract a key from context for pattern matching."""
        important_keys = ['activity', 'time_of_day', 'day_of_week', 'location', 'mood']
        key_parts = []
        
        for key in important_keys:
            if key in context:
                value = context[key]
                if isinstance(value, (str, int, float, bool)):
                    key_parts.append(f"{key}:{value}")
        
        return "|".join(key_parts) if key_parts else "default"
    
    def _analyze_patterns(self, context_key: str) -> Dict[str, Any]:
        """Analyze patterns for a specific context."""
        patterns = self.context_patterns.get(context_key, [])
        
        if len(patterns) < 5:
            return {'confidence': 'low', 'message': 'Insufficient data'}
        
        # Calculate statistics
        recent_patterns = patterns[-20:]  # Last 20 interactions
        acceptance_rate = sum(1 for p in recent_patterns if p['feedback_type'] in ['accepted', 'positive']) / len(recent_patterns)
        
        # Trend analysis
        if len(recent_patterns) >= 10:
            first_half = recent_patterns[:5]
            second_half = recent_patterns[-5:]
            
            first_avg = np.mean([p['reward'] for p in first_half])
            second_avg = np.mean([p['reward'] for p in second_half])
            
            trend = 'improving' if second_avg > first_avg else 'declining' if second_avg < first_avg else 'stable'
        else:
            trend = 'insufficient'
        
        return {
            'confidence': 'high' if len(patterns) > 20 else 'medium',
            'acceptance_rate': acceptance_rate,
            'trend': trend,
            'total_interactions': len(patterns),
            'suggestion_count': len(set(p['suggestion_id'] for p in patterns if hasattr(p, 'suggestion_id')))
        }
    
    def _update_user_preferences(self, feedback: Dict[str, Any]):
        """Update user preferences based on feedback."""
        context = feedback['context']
        feedback_type = feedback['type']
        
        # Update activity preferences
        if 'activity' in context:
            activity = context['activity']
            if activity not in self.user_preferences:
                self.user_preferences[activity] = {}
            
            # Update suggestion type preferences
            if 'suggestion_type' in context:
                sug_type = context['suggestion_type']
                if sug_type not in self.user_preferences[activity]:
                    self.user_preferences[activity][sug_type] = {'accepted': 0, 'rejected': 0, 'total': 0}
                
                prefs = self.user_preferences[activity][sug_type]
                if feedback_type in ['accepted', 'positive']:
                    prefs['accepted'] += 1
                elif feedback_type in ['rejected', 'negative']:
                    prefs['rejected'] += 1
                prefs['total'] += 1
        
        # Update time preferences
        if 'time_of_day' in context:
            time_key = f"time_{context['time_of_day']}"
            if time_key not in self.user_preferences:
                self.user_preferences[time_key] = {'suggestions': 0, 'acceptances': 0}
            
            self.user_preferences[time_key]['suggestions'] += 1
            if feedback_type in ['accepted', 'positive']:
                self.user_preferences[time_key]['acceptances'] += 1
    
    def _get_relevant_preferences(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get preferences relevant to current context."""
        relevant = {}
        
        if 'activity' in context and context['activity'] in self.user_preferences:
            relevant['activity_preferences'] = self.user_preferences[context['activity']]
        
        if 'time_of_day' in context:
            time_key = f"time_{context['time_of_day']}"
            if time_key in self.user_preferences:
                relevant['time_preferences'] = self.user_preferences[time_key]
        
        return relevant
    
    def _trim_history(self, max_entries: int = 10000):
        """Trim feedback history to prevent unlimited growth."""
        if len(self.feedback_history) > max_entries:
            # Keep most recent entries
            self.feedback_history = self.feedback_history[-max_entries:]
            
            # Also trim pattern storage
            for context_key in self.context_patterns:
                if len(self.context_patterns[context_key]) > 1000:
                    self.context_patterns[context_key] = self.context_patterns[context_key][-1000:]
    
    async def _save_feedback(self):
        """Save feedback data to storage."""
        try:
            # Save feedback history
            history_file = self.storage_path / "feedback_history.json"
            with open(history_file, 'w') as f:
                json.dump({
                    'history': self.feedback_history[-1000:],  # Save last 1000
                    'suggestion_scores': dict(self.suggestion_scores),
                    'context_scores': dict(self.context_scores)
                }, f, indent=2)
            
            # Save user preferences
            prefs_file = self.storage_path / "user_preferences.json"
            with open(prefs_file, 'w') as f:
                json.dump(self.user_preferences, f, indent=2)
            
            logger.debug("Feedback data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving feedback data: {e}")
    
    async def get_feedback_statistics(self, 
                                     days: int = 30,
                                     context_filter: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get statistics about collected feedback.
        
        Args:
            days: Number of days to analyze
            context_filter: Optional filter for specific context
            
        Returns:
            Dictionary with feedback statistics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter recent feedback
        recent_feedback = [
            f for f in self.feedback_history
            if datetime.fromisoformat(f['timestamp']) > cutoff_date
        ]
        
        if context_filter:
            recent_feedback = [
                f for f in recent_feedback
                if all(f['context'].get(k) == v for k, v in context_filter.items())
            ]
        
        if not recent_feedback:
            return {'message': 'No feedback data available for the specified period'}
        
        # Calculate statistics
        total = len(recent_feedback)
        feedback_types = defaultdict(int)
        avg_rating = 0
        ratings_count = 0
        
        for fb in recent_feedback:
            feedback_types[fb['type']] += 1
            if fb.get('rating'):
                avg_rating += fb['rating']
                ratings_count += 1
        
        if ratings_count > 0:
            avg_rating /= ratings_count
        
        # Acceptance rate
        accepted = feedback_types.get('accepted', 0) + feedback_types.get('positive', 0)
        acceptance_rate = accepted / total if total > 0 else 0
        
        # Top performing suggestions
        suggestion_performance = []
        for sug_id, score in self.suggestion_scores.items():
            sug_feedback = [f for f in recent_feedback if f['suggestion_id'] == sug_id]
            if sug_feedback:
                suggestion_performance.append({
                    'suggestion_id': sug_id,
                    'score': score,
                    'interactions': len(sug_feedback)
                })
        
        suggestion_performance.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'period_days': days,
            'total_feedback': total,
            'feedback_type_distribution': dict(feedback_types),
            'acceptance_rate': acceptance_rate,
            'average_rating': avg_rating if ratings_count > 0 else None,
            'top_suggestions': suggestion_performance[:10],
            'context_patterns': {
                k: self._analyze_patterns(k)
                for k in list(self.context_patterns.keys())[:5]
            },
            'exploration_rate': self.exploration_rate
        }
    
    async def adjust_exploration_rate(self, performance_threshold: float = 0.7):
        """
        Dynamically adjust exploration rate based on performance.
        
        Args:
            performance_threshold: Threshold above which to reduce exploration
        """
        stats = await self.get_feedback_statistics(days=7)
        
        if stats['acceptance_rate'] > performance_threshold:
            # Reduce exploration when doing well
            self.exploration_rate = max(0.05, self.exploration_rate * 0.95)
        else:
            # Increase exploration when struggling
            self.exploration_rate = min(0.4, self.exploration_rate * 1.1)
        
        logger.info(f"Adjusted exploration rate to {self.exploration_rate}")