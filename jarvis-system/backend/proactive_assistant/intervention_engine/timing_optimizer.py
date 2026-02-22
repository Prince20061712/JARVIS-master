"""
Timing Optimizer Module - Enhanced version
Optimizes when to deliver suggestions for maximum impact and user engagement.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass, field
import json
from pathlib import Path
import random

logger = logging.getLogger(__name__)

class EngagementLevel(Enum):
    """User engagement levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    OPTIMAL = "optimal"

class InterventionState(Enum):
    """States for intervention timing."""
    PENDING = "pending"
    READY = "ready"
    DELIVERED = "delivered"
    SKIPPED = "skipped"
    EXPIRED = "expired"

@dataclass
class TimingWindow:
    """Represents an optimal timing window for interventions."""
    start_time: datetime
    end_time: datetime
    confidence: float
    reason: str
    engagement_level: EngagementLevel

@dataclass
class InterventionHistory:
    """History of interventions for learning."""
    suggestion_id: str
    scheduled_time: datetime
    actual_time: Optional[datetime]
    outcome: str
    context: Dict[str, Any]
    engagement_score: float
    response_time: Optional[float] = None

class TimingOptimizer:
    """
    Enhanced timing optimizer that learns optimal intervention times
    based on user behavior patterns and engagement metrics.
    """
    
    def __init__(self, storage_path: str = "data/timing"):
        """
        Initialize the timing optimizer.
        
        Args:
            storage_path: Path to store timing data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Timing data storage
        self.intervention_history: List[InterventionHistory] = []
        self.user_patterns: Dict[str, Any] = {}
        self.optimal_windows: Dict[str, List[TimingWindow]] = defaultdict(list)
        
        # Real-time tracking
        self.pending_interventions: Dict[str, Dict[str, Any]] = {}
        self.last_intervention_time: Dict[str, datetime] = {}
        self.context_queue: deque = deque(maxlen=100)
        
        # Learning parameters
        self.window_size = timedelta(minutes=30)
        self.learning_rate = 0.1
        self.engagement_threshold = 0.7
        
        # Load existing data
        self._load_data()
        
        logger.info("TimingOptimizer initialized successfully")
    
    def _load_data(self):
        """Load timing data from storage."""
        history_file = self.storage_path / "intervention_history.json"
        patterns_file = self.storage_path / "user_patterns.json"
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    for entry in data:
                        self.intervention_history.append(InterventionHistory(**entry))
                logger.info(f"Loaded {len(self.intervention_history)} intervention records")
            except Exception as e:
                logger.error(f"Error loading intervention history: {e}")
        
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    self.user_patterns = json.load(f)
                logger.info("Loaded user patterns")
            except Exception as e:
                logger.error(f"Error loading user patterns: {e}")
    
    async def calculate_optimal_time(self,
                                    suggestion_id: str,
                                    context: Dict[str, Any],
                                    urgency: float = 0.5,
                                    preferred_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate the optimal time to deliver an intervention.
        
        Args:
            suggestion_id: ID of the suggestion
            context: Current context
            urgency: Urgency level (0-1)
            preferred_time: User's preferred time if any
            
        Returns:
            Dictionary with timing recommendations
        """
        try:
            # Add to context queue for pattern learning
            self.context_queue.append({
                'timestamp': datetime.now(),
                'context': context.copy()
            })
            
            # Get user availability patterns
            availability = self._get_availability_patterns(context)
            
            # Get engagement patterns
            engagement_patterns = self._analyze_engagement_patterns()
            
            # Calculate base optimal time
            base_time = preferred_time or datetime.now()
            
            # Adjust based on patterns
            adjusted_time = self._apply_timing_adjustments(
                base_time, availability, engagement_patterns, urgency
            )
            
            # Find optimal window
            optimal_window = self._find_optimal_window(adjusted_time, context, urgency)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(optimal_window, urgency, context)
            
            # Determine engagement level
            engagement = self._estimate_engagement_level(optimal_window, context)
            
            # Store pending intervention
            self.pending_interventions[suggestion_id] = {
                'suggestion_id': suggestion_id,
                'optimal_time': optimal_window.start_time.isoformat() if optimal_window else None,
                'context': context.copy(),
                'urgency': urgency,
                'calculated_at': datetime.now().isoformat(),
                'state': InterventionState.PENDING.value
            }
            
            result = {
                'success': True,
                'optimal_time': optimal_window.start_time.isoformat() if optimal_window else base_time.isoformat(),
                'optimal_window': {
                    'start': optimal_window.start_time.isoformat() if optimal_window else None,
                    'end': optimal_window.end_time.isoformat() if optimal_window else None,
                    'confidence': confidence,
                    'reason': optimal_window.reason if optimal_window else "Based on current context"
                } if optimal_window else None,
                'engagement_level': engagement.value,
                'alternative_times': self._generate_alternative_times(optimal_window, 3),
                'wait_time_seconds': self._calculate_wait_time(optimal_window) if optimal_window else 0
            }
            
            logger.info(f"Calculated optimal time for suggestion {suggestion_id}: {result['optimal_time']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating optimal time: {e}")
            return {
                'success': False,
                'error': str(e),
                'optimal_time': datetime.now().isoformat()  # Fallback to now
            }
    
    def _get_availability_patterns(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get user availability patterns from history."""
        patterns = {
            'best_times': [],
            'worst_times': [],
            'typical_duration': timedelta(minutes=30),
            'interruption_sensitivity': 0.5
        }
        
        # Analyze intervention history
        if self.intervention_history:
            # Group by hour of day
            hourly_engagement = defaultdict(list)
            for intervention in self.intervention_history:
                if intervention.actual_time:
                    hour = intervention.actual_time.hour
                    hourly_engagement[hour].append(intervention.engagement_score)
            
            # Find best and worst hours
            avg_by_hour = {
                hour: np.mean(scores) 
                for hour, scores in hourly_engagement.items() 
                if len(scores) >= 3
            }
            
            if avg_by_hour:
                sorted_hours = sorted(avg_by_hour.items(), key=lambda x: x[1], reverse=True)
                patterns['best_times'] = [hour for hour, _ in sorted_hours[:3]]
                patterns['worst_times'] = [hour for hour, _ in sorted_hours[-3:]]
        
        # Consider context
        if 'time_of_day' in context:
            current_hour = datetime.now().hour
            if patterns['best_times'] and current_hour in patterns['best_times']:
                patterns['interruption_sensitivity'] = 0.3  # Lower sensitivity during good times
            elif patterns['worst_times'] and current_hour in patterns['worst_times']:
                patterns['interruption_sensitivity'] = 0.8  # Higher sensitivity during bad times
        
        return patterns
    
    def _analyze_engagement_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in user engagement with interventions."""
        patterns = {
            'response_time_avg': timedelta(minutes=5),
            'completion_rate': 0.7,
            'optimal_intervals': [],
            'time_of_day_preferences': defaultdict(float)
        }
        
        if not self.intervention_history:
            return patterns
        
        # Calculate average response time
        response_times = [
            i.response_time for i in self.intervention_history 
            if i.response_time is not None
        ]
        if response_times:
            patterns['response_time_avg'] = timedelta(
                seconds=np.mean([rt.total_seconds() for rt in response_times])
            )
        
        # Calculate completion rate
        successful = sum(1 for i in self.intervention_history if i.outcome == 'accepted')
        patterns['completion_rate'] = successful / len(self.intervention_history)
        
        # Analyze time of day preferences
        for intervention in self.intervention_history:
            if intervention.actual_time:
                hour = intervention.actual_time.hour
                patterns['time_of_day_preferences'][hour] += intervention.engagement_score
        
        # Normalize preferences
        total = sum(patterns['time_of_day_preferences'].values())
        if total > 0:
            for hour in patterns['time_of_day_preferences']:
                patterns['time_of_day_preferences'][hour] /= total
        
        return patterns
    
    def _apply_timing_adjustments(self,
                                 base_time: datetime,
                                 availability: Dict[str, Any],
                                 engagement_patterns: Dict[str, Any],
                                 urgency: float) -> datetime:
        """Apply various adjustments to find optimal time."""
        adjusted_time = base_time
        
        # Adjust based on availability
        current_hour = adjusted_time.hour
        if availability['worst_times'] and current_hour in availability['worst_times']:
            # Move to next best hour
            if availability['best_times']:
                next_best = min(
                    availability['best_times'],
                    key=lambda x: (x - current_hour) % 24
                )
                hour_diff = (next_best - current_hour) % 24
                adjusted_time += timedelta(hours=hour_diff)
        
        # Adjust based on engagement patterns
        if engagement_patterns['time_of_day_preferences']:
            best_hour = max(
                engagement_patterns['time_of_day_preferences'].items(),
                key=lambda x: x[1]
            )[0]
            
            # Weighted blend based on urgency
            if urgency < 0.3:  # Low urgency, can wait for optimal time
                hour_diff = (best_hour - adjusted_time.hour) % 24
                if hour_diff <= 4:  # Only adjust if within reasonable window
                    adjusted_time += timedelta(hours=hour_diff)
        
        return adjusted_time
    
    def _find_optimal_window(self,
                            target_time: datetime,
                            context: Dict[str, Any],
                            urgency: float) -> Optional[TimingWindow]:
        """Find the optimal timing window around target time."""
        # Check historical windows
        context_key = self._get_context_key(context)
        historical_windows = self.optimal_windows.get(context_key, [])
        
        # Filter windows that contain target time
        relevant_windows = [
            w for w in historical_windows
            if w.start_time <= target_time <= w.end_time
        ]
        
        if relevant_windows:
            # Use best historical window
            best_window = max(relevant_windows, key=lambda w: w.confidence)
            return best_window
        
        # Generate new window based on patterns
        window_start = target_time - self.window_size / 2
        window_end = target_time + self.window_size / 2
        
        # Adjust based on context
        if 'activity' in context:
            if context['activity'] in ['coding', 'working']:
                # Longer windows for focused work
                window_start = target_time - timedelta(minutes=10)
                window_end = target_time + timedelta(minutes=20)
                reason = "During focused work, wait for natural break points"
            elif context['activity'] in ['break', 'relaxing']:
                # Shorter windows during breaks
                window_start = target_time - timedelta(minutes=5)
                window_end = target_time + timedelta(minutes=5)
                reason = "During breaks, intervene quickly before focus returns"
            else:
                reason = "Based on general availability patterns"
        else:
            reason = "Based on calculated optimal time"
        
        # Adjust window size based on urgency
        if urgency > 0.8:
            window_start = target_time
            window_end = target_time + timedelta(minutes=5)
            reason += " (high urgency - narrow window)"
        elif urgency < 0.2:
            window_start = target_time - timedelta(hours=1)
            window_end = target_time + timedelta(hours=1)
            reason += " (low urgency - wide window)"
        
        # Calculate confidence
        confidence = self._calculate_window_confidence(window_start, window_end, context)
        
        # Estimate engagement level
        engagement = self._estimate_engagement_level(
            TimingWindow(window_start, window_end, confidence, reason, EngagementLevel.MEDIUM),
            context
        )
        
        return TimingWindow(
            start_time=window_start,
            end_time=window_end,
            confidence=confidence,
            reason=reason,
            engagement_level=engagement
        )
    
    def _calculate_window_confidence(self,
                                   start: datetime,
                                   end: datetime,
                                   context: Dict[str, Any]) -> float:
        """Calculate confidence score for a timing window."""
        confidence = 0.5  # Base confidence
        
        # Check if we have historical data for this time
        similar_interventions = [
            i for i in self.intervention_history
            if i.actual_time and 
            start.hour <= i.actual_time.hour <= end.hour and
            i.engagement_score > self.engagement_threshold
        ]
        
        if similar_interventions:
            # Higher confidence if similar times worked well
            avg_engagement = np.mean([i.engagement_score for i in similar_interventions])
            confidence += 0.3 * avg_engagement
        
        # Check context similarity
        context_matches = 0
        for hist_intervention in self.intervention_history[-10:]:  # Last 10 interventions
            match_score = self._context_similarity(context, hist_intervention.context)
            if match_score > 0.7:
                context_matches += 1
        
        if context_matches > 0:
            confidence += 0.1 * min(context_matches / 5, 1.0)
        
        # Adjust based on time of day patterns
        current_hour = start.hour
        if 9 <= current_hour <= 11 or 14 <= current_hour <= 16:
            confidence += 0.1  # Typical peak productivity hours
        elif 0 <= current_hour <= 6:
            confidence -= 0.2  # Late night, likely sleeping
        
        return min(1.0, max(0.0, confidence))
    
    def _context_similarity(self, context1: Dict, context2: Dict) -> float:
        """Calculate similarity between two contexts."""
        if not context1 or not context2:
            return 0.0
        
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0
        
        matches = 0
        for key in common_keys:
            if context1[key] == context2[key]:
                matches += 1
        
        return matches / len(common_keys)
    
    def _estimate_engagement_level(self,
                                 window: TimingWindow,
                                 context: Dict[str, Any]) -> EngagementLevel:
        """Estimate expected engagement level for a timing window."""
        # Base on window confidence
        if window.confidence > 0.8:
            base_level = EngagementLevel.HIGH
        elif window.confidence > 0.6:
            base_level = EngagementLevel.MEDIUM
        elif window.confidence > 0.4:
            base_level = EngagementLevel.LOW
        else:
            base_level = EngagementLevel.LOW
        
        # Adjust based on context
        if 'activity' in context:
            if context['activity'] in ['break', 'relaxing']:
                if base_level == EngagementLevel.HIGH:
                    return EngagementLevel.OPTIMAL
            elif context['activity'] in ['coding', 'working']:
                if base_level in [EngagementLevel.MEDIUM, EngagementLevel.HIGH]:
                    return EngagementLevel.MEDIUM  # Lower during focused work
        
        # Adjust based on time
        current_hour = window.start_time.hour
        if 12 <= current_hour <= 13:  # Lunch time
            if base_level == EngagementLevel.HIGH:
                return EngagementLevel.MEDIUM
        elif 17 <= current_hour <= 19:  # Evening commute/dinner
            if base_level == EngagementLevel.HIGH:
                return EngagementLevel.MEDIUM
        
        return base_level
    
    def _calculate_wait_time(self, window: TimingWindow) -> int:
        """Calculate wait time in seconds until optimal window."""
        now = datetime.now()
        
        if now < window.start_time:
            return int((window.start_time - now).total_seconds())
        elif window.start_time <= now <= window.end_time:
            return 0  # In optimal window now
        else:
            return -1  # Window has passed
    
    def _generate_alternative_times(self,
                                   optimal_window: Optional[TimingWindow],
                                   count: int) -> List[str]:
        """Generate alternative timing suggestions."""
        alternatives = []
        
        if not optimal_window:
            return alternatives
        
        now = datetime.now()
        
        # Alternative 1: Slightly later
        alt1 = optimal_window.start_time + timedelta(minutes=30)
        if alt1 > now:
            alternatives.append(alt1.isoformat())
        
        # Alternative 2: Next optimal window based on patterns
        if self.optimal_windows:
            all_windows = sorted(
                [w for sublist in self.optimal_windows.values() for w in sublist],
                key=lambda w: w.confidence,
                reverse=True
            )
            for window in all_windows[:count]:
                if window.start_time > now and window.start_time != optimal_window.start_time:
                    alternatives.append(window.start_time.isoformat())
                    if len(alternatives) >= count:
                        break
        
        # Fill with generic alternatives if needed
        while len(alternatives) < count:
            alt_time = now + timedelta(hours=len(alternatives) + 1)
            alternatives.append(alt_time.isoformat())
        
        return alternatives[:count]
    
    def _get_context_key(self, context: Dict[str, Any]) -> str:
        """Generate a context key for pattern matching."""
        important_keys = ['activity', 'location', 'day_of_week']
        key_parts = []
        
        for key in important_keys:
            if key in context:
                key_parts.append(f"{key}:{context[key]}")
        
        return "|".join(key_parts) if key_parts else "default"
    
    async def record_intervention_outcome(self,
                                         suggestion_id: str,
                                         outcome: str,
                                         engagement_score: float,
                                         response_time: Optional[float] = None):
        """
        Record the outcome of an intervention for learning.
        
        Args:
            suggestion_id: ID of the suggestion
            outcome: Outcome ('accepted', 'rejected', 'ignored', 'snoozed')
            engagement_score: User engagement score (0-1)
            response_time: Time taken to respond in seconds
        """
        try:
            # Get pending intervention data
            pending = self.pending_interventions.get(suggestion_id, {})
            
            # Create history entry
            history_entry = InterventionHistory(
                suggestion_id=suggestion_id,
                scheduled_time=datetime.fromisoformat(pending.get('optimal_time', datetime.now().isoformat())),
                actual_time=datetime.now(),
                outcome=outcome,
                context=pending.get('context', {}),
                engagement_score=engagement_score,
                response_time=timedelta(seconds=response_time) if response_time else None
            )
            
            self.intervention_history.append(history_entry)
            
            # Update optimal windows based on this outcome
            await self._update_optimal_windows(history_entry)
            
            # Remove from pending
            if suggestion_id in self.pending_interventions:
                del self.pending_interventions[suggestion_id]
            
            # Trim history if needed
            self._trim_history()
            
            # Save data
            await self._save_data()
            
            logger.info(f"Recorded outcome for intervention {suggestion_id}: {outcome}")
            
        except Exception as e:
            logger.error(f"Error recording intervention outcome: {e}")
    
    async def _update_optimal_windows(self, intervention: InterventionHistory):
        """Update optimal windows based on intervention outcome."""
        if intervention.outcome not in ['accepted', 'positive']:
            return  # Only learn from positive outcomes
        
        context_key = self._get_context_key(intervention.context)
        
        # Create or update window
        window_start = intervention.actual_time - timedelta(minutes=15)
        window_end = intervention.actual_time + timedelta(minutes=15)
        
        # Check if similar window exists
        existing_windows = self.optimal_windows.get(context_key, [])
        updated = False
        
        for i, window in enumerate(existing_windows):
            if (abs((window.start_time - window_start).total_seconds()) < 1800):  # Within 30 minutes
                # Update existing window
                new_confidence = window.confidence + self.learning_rate * (intervention.engagement_score - window.confidence)
                existing_windows[i].confidence = min(1.0, new_confidence)
                existing_windows[i].engagement_level = self._estimate_engagement_level(window, intervention.context)
                updated = True
                break
        
        if not updated:
            # Create new window
            new_window = TimingWindow(
                start_time=window_start,
                end_time=window_end,
                confidence=0.6,  # Starting confidence
                reason="Learned from successful intervention",
                engagement_level=self._estimate_engagement_level(
                    TimingWindow(window_start, window_end, 0.6, "", EngagementLevel.MEDIUM),
                    intervention.context
                )
            )
            self.optimal_windows[context_key].append(new_window)
        
        # Limit windows per context
        if len(self.optimal_windows[context_key]) > 20:
            # Keep highest confidence windows
            self.optimal_windows[context_key] = sorted(
                self.optimal_windows[context_key],
                key=lambda w: w.confidence,
                reverse=True
            )[:20]
    
    def _trim_history(self, max_entries: int = 1000):
        """Trim intervention history to prevent unlimited growth."""
        if len(self.intervention_history) > max_entries:
            self.intervention_history = self.intervention_history[-max_entries:]
    
    async def _save_data(self):
        """Save timing data to storage."""
        try:
            # Save intervention history
            history_file = self.storage_path / "intervention_history.json"
            with open(history_file, 'w') as f:
                json.dump([
                    {
                        'suggestion_id': i.suggestion_id,
                        'scheduled_time': i.scheduled_time.isoformat(),
                        'actual_time': i.actual_time.isoformat() if i.actual_time else None,
                        'outcome': i.outcome,
                        'context': i.context,
                        'engagement_score': i.engagement_score,
                        'response_time': i.response_time.total_seconds() if i.response_time else None
                    }
                    for i in self.intervention_history
                ], f, indent=2, default=str)
            
            # Save optimal windows
            windows_data = {}
            for context_key, windows in self.optimal_windows.items():
                windows_data[context_key] = [
                    {
                        'start_time': w.start_time.isoformat(),
                        'end_time': w.end_time.isoformat(),
                        'confidence': w.confidence,
                        'reason': w.reason,
                        'engagement_level': w.engagement_level.value
                    }
                    for w in windows
                ]
            
            windows_file = self.storage_path / "optimal_windows.json"
            with open(windows_file, 'w') as f:
                json.dump(windows_data, f, indent=2)
            
            logger.debug("Timing data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving timing data: {e}")
    
    async def get_timing_statistics(self) -> Dict[str, Any]:
        """Get statistics about timing optimization."""
        if not self.intervention_history:
            return {'message': 'No timing data available'}
        
        # Calculate metrics
        total = len(self.intervention_history)
        successful = sum(1 for i in self.intervention_history if i.outcome == 'accepted')
        
        # Average engagement by hour
        hourly_engagement = defaultdict(list)
        for intervention in self.intervention_history:
            if intervention.actual_time:
                hour = intervention.actual_time.hour
                hourly_engagement[hour].append(intervention.engagement_score)
        
        avg_by_hour = {
            hour: np.mean(scores) 
            for hour, scores in hourly_engagement.items() 
            if len(scores) >= 3
        }
        
        # Best and worst hours
        best_hours = []
        worst_hours = []
        if avg_by_hour:
            sorted_hours = sorted(avg_by_hour.items(), key=lambda x: x[1], reverse=True)
            best_hours = [hour for hour, _ in sorted_hours[:3]]
            worst_hours = [hour for hour, _ in sorted_hours[-3:]]
        
        # Average response time
        response_times = [
            i.response_time.total_seconds() 
            for i in self.intervention_history 
            if i.response_time is not None
        ]
        avg_response = np.mean(response_times) if response_times else None
        
        return {
            'total_interventions': total,
            'success_rate': successful / total if total > 0 else 0,
            'average_engagement': np.mean([i.engagement_score for i in self.intervention_history]),
            'best_hours': best_hours,
            'worst_hours': worst_hours,
            'average_response_time_seconds': avg_response,
            'optimal_windows_count': sum(len(w) for w in self.optimal_windows.values()),
            'pending_interventions': len(self.pending_interventions)
        }
    
    async def should_intervene_now(self,
                                 suggestion_id: str,
                                 current_context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determine if now is a good time to intervene.
        
        Args:
            suggestion_id: ID of the suggestion
            current_context: Current context
            
        Returns:
            Tuple of (should_intervene, reason)
        """
        # Check if suggestion is pending
        if suggestion_id not in self.pending_interventions:
            return False, "Suggestion not in pending list"
        
        pending = self.pending_interventions[suggestion_id]
        optimal_time = datetime.fromisoformat(pending['optimal_time'])
        now = datetime.now()
        
        # Check if within optimal window
        context_key = self._get_context_key(current_context)
        windows = self.optimal_windows.get(context_key, [])
        
        for window in windows:
            if window.start_time <= now <= window.end_time:
                return True, f"Within optimal window (confidence: {window.confidence:.2f})"
        
        # Check time difference
        time_diff = abs((now - optimal_time).total_seconds())
        
        if time_diff < 300:  # Within 5 minutes
            return True, "Close to optimal time"
        elif time_diff < 900:  # Within 15 minutes
            # Check engagement level
            engagement = self._estimate_engagement_level(
                TimingWindow(now, now + timedelta(minutes=5), 0.5, "", EngagementLevel.MEDIUM),
                current_context
            )
            if engagement in [EngagementLevel.HIGH, EngagementLevel.OPTIMAL]:
                return True, f"Good engagement opportunity ({engagement.value})"
        
        return False, "Not an optimal time"