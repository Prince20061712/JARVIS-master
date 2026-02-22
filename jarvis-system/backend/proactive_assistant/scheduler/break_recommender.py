"""
Break Recommender Module - Enhanced version
Intelligently recommends optimal break times based on user activity, focus levels, and wellness metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import random
from enum import Enum
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass, field
import json
from pathlib import Path
import asyncio
from scipy import stats

logger = logging.getLogger(__name__)

class BreakType(Enum):
    """Types of breaks that can be recommended."""
    MICRO = "micro"  # 30-60 seconds
    SHORT = "short"  # 5-10 minutes
    LONG = "long"    # 15-30 minutes
    MEAL = "meal"    # 30-60 minutes
    WELLNESS = "wellness"  # Exercise, meditation, etc.
    SOCIAL = "social"      # Social interaction
    EYE = "eye"      # Eye strain relief (20-20-20 rule)
    PHYSICAL = "physical"  # Physical movement
    MENTAL = "mental"      # Mental reset

class BreakPriority(Enum):
    """Priority levels for breaks."""
    OPTIONAL = 1
    RECOMMENDED = 2
    IMPORTANT = 3
    CRITICAL = 4

@dataclass
class BreakSchedule:
    """Data class for break schedule."""
    break_id: str
    break_type: BreakType
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    priority: BreakPriority
    reason: str
    activities: List[str] = field(default_factory=list)
    completed: bool = False
    effectiveness_score: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WellnessMetrics:
    """Data class for wellness tracking."""
    timestamp: datetime
    focus_level: float  # 0-1
    energy_level: float  # 0-1
    eye_strain: float    # 0-1
    physical_discomfort: float  # 0-1
    mental_fatigue: float  # 0-1
    hydration_level: float  # 0-1
    hours_since_break: float
    emotional_state: Optional[str] = "neutral"
    wellbeing_score: Optional[float] = 0.5
    context: Dict[str, Any] = field(default_factory=dict)

class BreakRecommender:
    """
    Enhanced break recommender that uses physiological and cognitive models
    to suggest optimal break times and activities.
    """
    
    def __init__(self, storage_path: str = "data/scheduler/breaks"):
        """
        Initialize the break recommender.
        
        Args:
            storage_path: Path to store break data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Break data storage
        self.break_history: List[BreakSchedule] = []
        self.wellness_history: List[WellnessMetrics] = []
        self.active_breaks: Dict[str, BreakSchedule] = {}
        
        # User preferences
        self.preferences = {
            'preferred_break_duration': 15,  # minutes
            'preferred_break_types': [BreakType.SHORT, BreakType.WELLNESS],
            'max_breaks_per_hour': 2,
            'min_interval_between_breaks': 30,  # minutes
            'enable_wellness_tracking': True,
            'enable_eye_strain_prevention': True,
            'work_hours': (9, 17)  # 9 AM to 5 PM
        }
        
        # Cognitive models
        self.fatigue_model = {
            'base_decay_rate': 0.05,  # per minute
            'focus_recovery_rate': 0.15,  # per minute of break
            'energy_recovery_rate': 0.08,
            'mental_fatigue_threshold': 0.7,
            'physical_discomfort_threshold': 0.6
        }
        
        # Eye strain model (20-20-20 rule)
        self.eye_strain_model = {
            'screen_time_threshold': 20,  # minutes
            'break_duration': 20,  # seconds
            'look_distance': "20 feet"
        }
        
        # Activity suggestions by break type
        self.break_activities = {
            BreakType.MICRO: [
                "Deep breathing (3-5 breaths)",
                "Roll shoulders and neck",
                "Stretch fingers and wrists",
                "Blink rapidly for 10 seconds",
                "Look away from screen"
            ],
            BreakType.SHORT: [
                "Walk around the room",
                "Get a glass of water",
                "Quick stretching routine",
                "Step outside for fresh air",
                "Mindfulness minute"
            ],
            BreakType.LONG: [
                "Go for a short walk",
                "Prepare and enjoy a healthy snack",
                "Quick workout or yoga",
                "Read a few pages of a book",
                "Call a friend or family member"
            ],
            BreakType.MEAL: [
                "Prepare a nutritious meal",
                "Eat without screens",
                "Practice mindful eating",
                "Take time to digest",
                "Light walk after eating"
            ],
            BreakType.WELLNESS: [
                "Meditation session",
                "Full stretching routine",
                "Quick workout",
                "Journaling",
                "Gratitude practice"
            ],
            BreakType.EYE: [
                "Focus on distant object for 20 seconds",
                "Palming (cover eyes with palms)",
                "Eye rolling exercises",
                "Blink slowly and deliberately",
                "Look in different directions"
            ],
            BreakType.PHYSICAL: [
                "Desk exercises",
                "Jumping jacks",
                "Squats or lunges",
                "Yoga poses",
                "Dance to one song"
            ],
            BreakType.MENTAL: [
                "Quick puzzle or brain teaser",
                "Listen to calming music",
                "5-minute meditation",
                "Write down thoughts",
                "Practice visualization"
            ]
        }
        
        # Load existing data
        self._load_data()
        
        logger.info("BreakRecommender initialized successfully")
    
    def _load_data(self):
        """Load break data from storage."""
        history_file = self.storage_path / "break_history.json"
        wellness_file = self.storage_path / "wellness_history.json"
        prefs_file = self.storage_path / "preferences.json"
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        schedule = BreakSchedule(
                            break_id=item['break_id'],
                            break_type=BreakType(item['break_type']),
                            start_time=datetime.fromisoformat(item['start_time']),
                            end_time=datetime.fromisoformat(item['end_time']),
                            duration_minutes=item['duration_minutes'],
                            priority=BreakPriority(item['priority']),
                            reason=item['reason'],
                            activities=item.get('activities', []),
                            completed=item.get('completed', False),
                            effectiveness_score=item.get('effectiveness_score'),
                            context=item.get('context', {})
                        )
                        self.break_history.append(schedule)
                logger.info(f"Loaded {len(self.break_history)} break records")
            except Exception as e:
                logger.error(f"Error loading break history: {e}")
        
        if wellness_file.exists():
            try:
                with open(wellness_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        metrics = WellnessMetrics(
                            timestamp=datetime.fromisoformat(item['timestamp']),
                            focus_level=item['focus_level'],
                            energy_level=item['energy_level'],
                            eye_strain=item['eye_strain'],
                            physical_discomfort=item['physical_discomfort'],
                            mental_fatigue=item['mental_fatigue'],
                            hydration_level=item['hydration_level'],
                            hours_since_break=item['hours_since_break'],
                            context=item.get('context', {})
                        )
                        self.wellness_history.append(metrics)
                logger.info(f"Loaded {len(self.wellness_history)} wellness records")
            except Exception as e:
                logger.error(f"Error loading wellness history: {e}")
        
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r') as f:
                    loaded_prefs = json.load(f)
                    # Convert break types back to enums
                    if 'preferred_break_types' in loaded_prefs:
                        loaded_prefs['preferred_break_types'] = [
                            BreakType(bt) for bt in loaded_prefs['preferred_break_types']
                        ]
                    self.preferences.update(loaded_prefs)
                logger.info("Loaded break preferences")
            except Exception as e:
                logger.error(f"Error loading preferences: {e}")
    
    async def update_wellness_metrics(self,
                                     focus_level: float,
                                     energy_level: float,
                                     eye_strain: Optional[float] = None,
                                     physical_discomfort: Optional[float] = None,
                                     mental_fatigue: Optional[float] = None,
                                     hydration_level: Optional[float] = None,
                                     emotional_state: Optional[str] = None,
                                     wellbeing_score: Optional[float] = None,
                                     context: Optional[Dict] = None) -> WellnessMetrics:
        """
        Update current wellness metrics.
        
        Args:
            focus_level: Current focus level (0-1)
            energy_level: Current energy level (0-1)
            eye_strain: Current eye strain level (0-1)
            physical_discomfort: Current physical discomfort (0-1)
            mental_fatigue: Current mental fatigue (0-1)
            hydration_level: Current hydration level (0-1)
            context: Additional context
            
        Returns:
            Updated WellnessMetrics object
        """
        # Calculate time since last break
        last_break = self._get_last_break_time()
        hours_since_break = (datetime.now() - last_break).total_seconds() / 3600 if last_break else 0
        
        metrics = WellnessMetrics(
            timestamp=datetime.now(),
            focus_level=focus_level,
            energy_level=energy_level,
            eye_strain=eye_strain or self._estimate_eye_strain(),
            physical_discomfort=physical_discomfort or 0.3,
            mental_fatigue=mental_fatigue or (1 - focus_level) * 0.7,
            hydration_level=hydration_level or 0.5,
            hours_since_break=hours_since_break,
            emotional_state=emotional_state or "neutral",
            wellbeing_score=wellbeing_score if wellbeing_score is not None else 0.5,
            context=context or {}
        )
        
        self.wellness_history.append(metrics)
        
        # Trim history
        if len(self.wellness_history) > 1000:
            self.wellness_history = self.wellness_history[-1000:]
        
        logger.debug(f"Wellness metrics updated: focus={focus_level:.2f}, energy={energy_level:.2f}")
        
        return metrics
    
    def _estimate_eye_strain(self) -> float:
        """Estimate eye strain based on screen time and breaks."""
        if not self.wellness_history:
            return 0.3
        
        # Get recent screen time
        recent_metrics = self.wellness_history[-10:]
        if len(recent_metrics) < 2:
            return 0.3
        
        # Calculate time difference
        time_diff = (recent_metrics[-1].timestamp - recent_metrics[0].timestamp).total_seconds() / 60
        
        # Estimate strain based on continuous screen time
        strain = min(1.0, time_diff / 120)  # Max strain after 2 hours
        
        # Check if eye breaks were taken
        recent_breaks = [
            b for b in self.break_history[-5:]
            if b.break_type == BreakType.EYE and b.completed
        ]
        
        if recent_breaks:
            strain *= 0.7  # Reduce strain if eye breaks were taken
        
        return strain
    
    def _get_last_break_time(self) -> Optional[datetime]:
        """Get the time of the last completed break."""
        completed_breaks = [b for b in self.break_history if b.completed]
        if completed_breaks:
            return max(b.end_time for b in completed_breaks)
        return None
    
    async def recommend_break(self,
                            current_activity: str,
                            duration_worked: float,  # minutes
                            wellness_metrics: Optional[WellnessMetrics] = None,
                            preferred_type: Optional[BreakType] = None) -> Optional[BreakSchedule]:
        """
        Recommend an optimal break based on current state.
        
        Args:
            current_activity: Current activity type
            duration_worked: Minutes worked continuously
            wellness_metrics: Current wellness metrics
            preferred_type: User's preferred break type
            
        Returns:
            BreakSchedule if break is recommended, None otherwise
        """
        # Check if we're within work hours
        current_hour = datetime.now().hour
        if current_hour < self.preferences['work_hours'][0] or current_hour > self.preferences['work_hours'][1]:
            return None
        
        # Get or estimate wellness metrics
        if not wellness_metrics and self.wellness_history:
            wellness_metrics = self.wellness_history[-1]
        elif not wellness_metrics:
            wellness_metrics = await self.update_wellness_metrics(
                focus_level=0.7,
                energy_level=0.6
            )
        
        # Calculate break urgency and type
        urgency_score, break_type, reason = self._calculate_break_urgency(
            duration_worked, wellness_metrics, current_activity
        )
        
        # Override with preferred type if specified
        if preferred_type and preferred_type in self.preferences['preferred_break_types']:
            break_type = preferred_type
        
        # Check cooldown
        if not self._can_take_break(break_type):
            return None
        
        # Determine break duration
        duration = self._get_break_duration(break_type, urgency_score)
        
        # Generate break activities
        activities = self._get_break_activities(break_type, urgency_score)
        
        # Create break schedule
        now = datetime.now()
        break_schedule = BreakSchedule(
            break_id=self._generate_break_id(),
            break_type=break_type,
            start_time=now,
            end_time=now + timedelta(minutes=duration),
            duration_minutes=duration,
            priority=BreakPriority(urgency_score),
            reason=reason,
            activities=activities,
            context={
                'current_activity': current_activity,
                'duration_worked': duration_worked,
                'wellness_metrics': {
                    'focus': wellness_metrics.focus_level,
                    'energy': wellness_metrics.energy_level,
                    'eye_strain': wellness_metrics.eye_strain
                }
            }
        )
        
        # Store active break
        self.active_breaks[break_schedule.break_id] = break_schedule
        
        logger.info(f"Recommended {break_type.value} break: {reason}")
        
        return break_schedule
    
    def _calculate_break_urgency(self,
                                duration_worked: float,
                                metrics: WellnessMetrics,
                                activity: str) -> Tuple[int, BreakType, str]:
        """
        Calculate break urgency and determine appropriate break type.
        
        Returns:
            Tuple of (urgency_score 1-4, break_type, reason)
        """
        urgency_score = 1  # Start at optional
        
        # Factor 1: Continuous work duration
        if duration_worked >= 120:  # 2+ hours
            urgency_score += 2
            duration_reason = "very long work session"
            recommended_type = BreakType.LONG
        elif duration_worked >= 90:  # 1.5 hours
            urgency_score += 1
            duration_reason = "long work session"
            recommended_type = BreakType.LONG
        elif duration_worked >= 45:  # 45 minutes
            urgency_score += 0
            duration_reason = "standard work session"
            recommended_type = BreakType.SHORT
        else:
            duration_reason = "short work session"
            recommended_type = BreakType.MICRO
        
        # Factor 2: Focus level
        if metrics.focus_level < 0.4:
            urgency_score += 2
            focus_reason = "very low focus"
            recommended_type = BreakType.MENTAL
        elif metrics.focus_level < 0.6:
            urgency_score += 1
            focus_reason = "declining focus"
            recommended_type = BreakType.SHORT
        else:
            focus_reason = "good focus"
        
        # Factor 3: Energy level
        if metrics.energy_level < 0.3:
            urgency_score += 2
            energy_reason = "very low energy"
            recommended_type = BreakType.WELLNESS
        elif metrics.energy_level < 0.5:
            urgency_reason = "low energy"
            recommended_type = BreakType.PHYSICAL
        else:
            energy_reason = "good energy"
        
        # Factor 4: Eye strain
        if self.preferences['enable_eye_strain_prevention'] and metrics.eye_strain > 0.7:
            urgency_score += 2
            eye_reason = "high eye strain"
            recommended_type = BreakType.EYE
        elif metrics.eye_strain > 0.5:
            urgency_score += 1
            eye_reason = "moderate eye strain"
            recommended_type = BreakType.EYE
        else:
            eye_reason = "normal eyes"
        
        # Factor 5: Physical discomfort
        if metrics.physical_discomfort > 0.7:
            urgency_score += 2
            physical_reason = "significant discomfort"
            recommended_type = BreakType.PHYSICAL
        elif metrics.physical_discomfort > 0.5:
            urgency_score += 1
            physical_reason = "mild discomfort"
            recommended_type = BreakType.PHYSICAL
        else:
            physical_reason = "comfortable"
        
        # Factor 6: Time since last break
        if metrics.hours_since_break > 3:
            urgency_score += 2
            break_reason = "no breaks for 3+ hours"
            recommended_type = BreakType.LONG
        elif metrics.hours_since_break > 2:
            urgency_score += 1
            break_reason = "no breaks for 2+ hours"
            recommended_type = BreakType.SHORT
        else:
            break_reason = "recent break taken"
        
        # Factor 7: Emotional State
        emotional_reason = ""
        if metrics.emotional_state in ['frustration', 'anxiety', 'overwhelmed', 'burnout', 'stress']:
            urgency_score += 2
            emotional_reason = f"high {metrics.emotional_state} detected"
            recommended_type = BreakType.MENTAL
        elif metrics.wellbeing_score < 0.4:
            urgency_score += 1
            emotional_reason = "low wellbeing score"
            recommended_type = BreakType.WELLNESS
        
        # Combine reasons
        reasons = []
        if duration_worked > 0:
            reasons.append(duration_reason)
        if metrics.focus_level < 0.6:
            reasons.append(focus_reason)
        if metrics.energy_level < 0.5:
            reasons.append(energy_reason)
        if metrics.eye_strain > 0.5:
            reasons.append(eye_reason)
        if metrics.physical_discomfort > 0.5:
            reasons.append(physical_reason)
        if metrics.hours_since_break > 2:
            reasons.append(break_reason)
        if emotional_reason:
            reasons.append(emotional_reason)
        
        # Clamp urgency score
        urgency_score = max(1, min(4, urgency_score))
        
        # Adjust break type based on activity
        if activity in ['coding', 'writing', 'design']:
            # Creative work benefits from longer, refreshing breaks
            if urgency_score >= 3:
                recommended_type = BreakType.LONG
            elif urgency_score >= 2:
                recommended_type = BreakType.WELLNESS
        elif activity in ['reading', 'research']:
            # Reading benefits from eye breaks
            if metrics.eye_strain > 0.4:
                recommended_type = BreakType.EYE
        
        reason = " | ".join(reasons[:3])  # Top 3 reasons
        
        return urgency_score, recommended_type, reason
    
    def _can_take_break(self, break_type: BreakType) -> bool:
        """Check if a break can be taken now based on cooldowns."""
        # Check rate limiting
        last_hour = datetime.now() - timedelta(hours=1)
        recent_breaks = [
            b for b in self.break_history
            if b.start_time > last_hour and b.completed
        ]
        
        if len(recent_breaks) >= self.preferences['max_breaks_per_hour']:
            return False
        
        # Check minimum interval
        if recent_breaks:
            last_break_time = max(b.end_time for b in recent_breaks)
            minutes_since = (datetime.now() - last_break_time).total_seconds() / 60
            if minutes_since < self.preferences['min_interval_between_breaks']:
                return False
        
        return True
    
    def _get_break_duration(self, break_type: BreakType, urgency: int) -> float:
        """Get appropriate break duration based on type and urgency."""
        duration_map = {
            BreakType.MICRO: (0.5, 1),    # 30-60 seconds
            BreakType.SHORT: (5, 10),      # 5-10 minutes
            BreakType.LONG: (15, 30),       # 15-30 minutes
            BreakType.MEAL: (30, 60),       # 30-60 minutes
            BreakType.WELLNESS: (10, 20),   # 10-20 minutes
            BreakType.SOCIAL: (10, 30),     # 10-30 minutes
            BreakType.EYE: (0.33, 1),       # 20-60 seconds
            BreakType.PHYSICAL: (5, 15),    # 5-15 minutes
            BreakType.MENTAL: (5, 10)       # 5-10 minutes
        }
        
        min_dur, max_dur = duration_map.get(break_type, (5, 15))
        
        # Scale with urgency
        if urgency >= 3:
            return max_dur
        elif urgency >= 2:
            return (min_dur + max_dur) / 2
        else:
            return min_dur
    
    def _get_break_activities(self, break_type: BreakType, urgency: int) -> List[str]:
        """Get suggested activities for the break."""
        activities = self.break_activities.get(break_type, ["Take a break"])
        
        # If urgent, suggest quick, effective activities
        if urgency >= 3 and len(activities) >= 2:
            return activities[:2] # Return top 2 activities
        elif activities:
            return [random.choice(activities)] # Return a single random activity
        return ["Take a break"] # Fallback
    
    def _generate_break_id(self) -> str:
        """Generate a unique break ID."""
        import hashlib
        
        unique_string = f"break_{datetime.now().isoformat()}_{random.random()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    async def complete_break(self,
                           break_id: str,
                           effectiveness_rating: Optional[int] = None,
                           notes: Optional[str] = None) -> bool:
        """
        Mark a break as completed and record its effectiveness.
        
        Args:
            break_id: ID of the break to complete
            effectiveness_rating: Rating 1-5 of break effectiveness
            notes: Optional notes about the break
            
        Returns:
            True if break was completed successfully
        """
        if break_id not in self.active_breaks:
            logger.warning(f"Break {break_id} not found in active breaks")
            return False
        
        break_schedule = self.active_breaks[break_id]
        break_schedule.completed = True
        break_schedule.end_time = datetime.now()
        
        if effectiveness_rating:
            break_schedule.effectiveness_score = effectiveness_rating / 5.0
        
        # Move to history
        self.break_history.append(break_schedule)
        del self.active_breaks[break_id]
        
        # Update wellness metrics post-break
        if self.wellness_history:
            last_metrics = self.wellness_history[-1]
            await self.update_wellness_metrics(
                focus_level=min(1.0, last_metrics.focus_level + 0.2),
                energy_level=min(1.0, last_metrics.energy_level + 0.15),
                eye_strain=max(0, last_metrics.eye_strain - 0.3),
                physical_discomfort=max(0, last_metrics.physical_discomfort - 0.2),
                mental_fatigue=max(0, last_metrics.mental_fatigue - 0.25),
                context={'break_taken': break_schedule.break_type.value}
            )
        
        logger.info(f"Break {break_id} completed with rating {effectiveness_rating}")
        
        # Save data
        await self._save_data()
        
        return True
    
    async def skip_break(self, break_id: str, reason: str = "User skipped") -> bool:
        """Skip a scheduled break."""
        if break_id in self.active_breaks:
            del self.active_breaks[break_id]
            logger.info(f"Break {break_id} skipped: {reason}")
            return True
        return False
    
    async def get_break_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get statistics about breaks taken."""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_breaks = [
            b for b in self.break_history
            if b.start_time > cutoff_date
        ]
        
        if not recent_breaks:
            return {'message': 'No break data available'}
        
        # Calculate statistics
        total_breaks = len(recent_breaks)
        breaks_by_type = defaultdict(int)
        total_duration = 0
        effectiveness_scores = []
        
        for break_sched in recent_breaks:
            breaks_by_type[break_sched.break_type.value] += 1
            duration = (break_sched.end_time - break_sched.start_time).total_seconds() / 60
            total_duration += duration
            if break_sched.effectiveness_score:
                effectiveness_scores.append(break_sched.effectiveness_score)
        
        # Calculate average break frequency
        active_days = len(set(b.start_time.date() for b in recent_breaks))
        avg_breaks_per_day = total_breaks / max(active_days, 1)
        
        # Analyze effectiveness by break type
        effectiveness_by_type = defaultdict(list)
        for break_sched in recent_breaks:
            if break_sched.effectiveness_score:
                effectiveness_by_type[break_sched.break_type.value].append(
                    break_sched.effectiveness_score
                )
        
        avg_effectiveness_by_type = {
            bt: np.mean(scores) for bt, scores in effectiveness_by_type.items() if scores
        }
        
        # Find optimal break patterns
        optimal_breaks = [
            b for b in recent_breaks
            if b.effectiveness_score and b.effectiveness_score > 0.8
        ]
        
        optimal_patterns = []
        for break_sched in optimal_breaks[:5]:
            optimal_patterns.append({
                'type': break_sched.break_type.value,
                'duration': break_sched.duration_minutes,
                'activities': break_sched.activities[:2]
            })
        
        return {
            'period_days': days,
            'total_breaks': total_breaks,
            'breaks_by_type': dict(breaks_by_type),
            'total_break_time_minutes': total_duration,
            'average_breaks_per_day': avg_breaks_per_day,
            'average_effectiveness': np.mean(effectiveness_scores) if effectiveness_scores else None,
            'effectiveness_by_type': avg_effectiveness_by_type,
            'optimal_patterns': optimal_patterns,
            'completion_rate': total_breaks / (total_breaks + len(self.active_breaks))
        }
    
    async def optimize_break_schedule(self,
                                    work_start: datetime,
                                    work_end: datetime,
                                    tasks: List[Dict[str, Any]]) -> List[BreakSchedule]:
        """
        Optimize break schedule for a work session.
        
        Args:
            work_start: Start time of work session
            work_end: End time of work session
            tasks: List of tasks with their estimated durations
            
        Returns:
            List of recommended breaks throughout the session
        """
        total_duration = (work_end - work_start).total_seconds() / 60
        breaks = []
        
        # Calculate optimal break intervals based on task complexity
        task_difficulties = [task.get('difficulty', 3) for task in tasks]
        avg_difficulty = np.mean(task_difficulties) if task_difficulties else 3
        
        # More frequent breaks for difficult tasks
        if avg_difficulty > 4:
            interval = 30  # Break every 30 minutes
            preferred_type = BreakType.SHORT
        elif avg_difficulty > 3:
            interval = 45  # Break every 45 minutes
            preferred_type = BreakType.SHORT
        else:
            interval = 60  # Break every 60 minutes
            preferred_type = BreakType.MICRO
        
        # Schedule breaks
        current_time = work_start
        break_count = 0
        
        while current_time < work_end:
            # Determine break type based on time of day
            hour = current_time.hour
            
            if 12 <= hour < 13:  # Lunch time
                break_type = BreakType.MEAL
                duration = 45
            elif 15 <= hour < 16:  # Afternoon slump
                break_type = BreakType.WELLNESS
                duration = 20
            elif break_count % 3 == 2:  # Every 3rd break is longer
                break_type = BreakType.LONG
                duration = 20
            else:
                break_type = preferred_type
                duration = self._get_break_duration(break_type, 2)
            
            # Calculate break time
            break_time = current_time + timedelta(minutes=interval)
            if break_time >= work_end:
                break
            
            # Generate activities
            activities = self._get_break_activities(break_type, 2)
            
            break_schedule = BreakSchedule(
                break_id=self._generate_break_id(),
                break_type=break_type,
                start_time=break_time,
                end_time=break_time + timedelta(minutes=duration),
                duration_minutes=duration,
                priority=BreakPriority.RECOMMENDED,
                reason=f"Scheduled {break_type.value} break",
                activities=activities,
                context={'scheduled': True, 'task_difficulty': avg_difficulty}
            )
            
            breaks.append(break_schedule)
            current_time = break_time + timedelta(minutes=duration)
            break_count += 1
        
        return breaks
    
    async def get_wellness_insights(self) -> Dict[str, Any]:
        """Get insights about wellness patterns."""
        if len(self.wellness_history) < 10:
            return {'message': 'Insufficient wellness data'}
        
        # Analyze patterns
        focus_trend = self._analyze_trend([m.focus_level for m in self.wellness_history[-50:]])
        energy_trend = self._analyze_trend([m.energy_level for m in self.wellness_history[-50:]])
        
        # Find correlations with breaks
        break_effectiveness = []
        for break_sched in self.break_history[-20:]:
            if break_sched.effectiveness_score:
                # Find wellness before break
                before_break = [
                    m for m in self.wellness_history
                    if abs((m.timestamp - break_sched.start_time).total_seconds()) < 300  # Within 5 minutes
                ]
                
                # Find wellness after break
                after_break = [
                    m for m in self.wellness_history
                    if abs((m.timestamp - break_sched.end_time).total_seconds()) < 300
                ]
                
                if before_break and after_break:
                    improvement = {
                        'focus': after_break[0].focus_level - before_break[0].focus_level,
                        'energy': after_break[0].energy_level - before_break[0].energy_level
                    }
                    break_effectiveness.append({
                        'break_type': break_sched.break_type.value,
                        'improvement': improvement,
                        'effectiveness': break_sched.effectiveness_score
                    })
        
        # Identify optimal break times
        optimal_times = defaultdict(list)
        for break_sched in self.break_history:
            if break_sched.effectiveness_score and break_sched.effectiveness_score > 0.8:
                optimal_times[break_sched.break_type.value].append(break_sched.start_time.hour)
        
        return {
            'current_wellness': {
                'focus': self.wellness_history[-1].focus_level,
                'energy': self.wellness_history[-1].energy_level,
                'eye_strain': self.wellness_history[-1].eye_strain
            },
            'trends': {
                'focus': focus_trend,
                'energy': energy_trend
            },
            'break_effectiveness': break_effectiveness[:5],
            'optimal_break_times': {
                bt: int(np.mean(hours)) if hours else None
                for bt, hours in optimal_times.items()
            },
            'recommendations': self._generate_wellness_recommendations()
        }
    
    def _analyze_trend(self, values: List[float]) -> str:
        """Analyze trend in a series of values."""
        if len(values) < 3:
            return 'insufficient_data'
        
        x = np.arange(len(values))
        slope, _, _, _, _ = stats.linregress(x, values)
        
        if slope > 0.01:
            return 'improving'
        elif slope < -0.01:
            return 'declining'
        else:
            return 'stable'
    
    def _generate_wellness_recommendations(self) -> List[str]:
        """Generate wellness recommendations based on patterns."""
        recommendations = []
        
        if len(self.wellness_history) < 10:
            return recommendations
        
        recent = self.wellness_history[-10:]
        avg_focus = np.mean([m.focus_level for m in recent])
        avg_energy = np.mean([m.energy_level for m in recent])
        avg_eye_strain = np.mean([m.eye_strain for m in recent])
        
        if avg_focus < 0.5:
            recommendations.append(
                "Your focus has been consistently low. Try taking more frequent short breaks "
                "and ensure you're getting adequate sleep."
            )
        
        if avg_energy < 0.4:
            recommendations.append(
                "Low energy levels detected. Consider adjusting your schedule to include "
                "physical activity and proper nutrition."
            )
        
        if avg_eye_strain > 0.6:
            recommendations.append(
                "High eye strain detected. Practice the 20-20-20 rule: every 20 minutes, "
                "look at something 20 feet away for 20 seconds."
            )
        
        # Check break effectiveness
        effective_breaks = [
            b for b in self.break_history[-20:]
            if b.effectiveness_score and b.effectiveness_score > 0.8
        ]
        
        if effective_breaks:
            best_break = max(effective_breaks, key=lambda b: b.effectiveness_score)
            recommendations.append(
                f"Your most effective breaks are {best_break.break_type.value} breaks "
                f"with activities like: {', '.join(best_break.activities[:2])}"
            )
        
        return recommendations
    
    async def update_preferences(self, new_preferences: Dict[str, Any]) -> None:
        """Update break preferences."""
        # Convert break types if present
        if 'preferred_break_types' in new_preferences:
            new_preferences['preferred_break_types'] = [
                BreakType(bt) if isinstance(bt, str) else bt
                for bt in new_preferences['preferred_break_types']
            ]
        
        self.preferences.update(new_preferences)
        await self._save_data()
        logger.info("Break preferences updated")
    
    async def _save_data(self):
        """Save break data to storage."""
        try:
            # Save break history
            history_file = self.storage_path / "break_history.json"
            with open(history_file, 'w') as f:
                json.dump([
                    {
                        'break_id': b.break_id,
                        'break_type': b.break_type.value,
                        'start_time': b.start_time.isoformat(),
                        'end_time': b.end_time.isoformat(),
                        'duration_minutes': b.duration_minutes,
                        'priority': b.priority.value,
                        'reason': b.reason,
                        'activities': b.activities,
                        'completed': b.completed,
                        'effectiveness_score': b.effectiveness_score,
                        'context': b.context
                    }
                    for b in self.break_history[-500:]  # Save last 500
                ], f, indent=2, default=str)
            
            # Save wellness history
            wellness_file = self.storage_path / "wellness_history.json"
            with open(wellness_file, 'w') as f:
                json.dump([
                    {
                        'timestamp': w.timestamp.isoformat(),
                        'focus_level': w.focus_level,
                        'energy_level': w.energy_level,
                        'eye_strain': w.eye_strain,
                        'physical_discomfort': w.physical_discomfort,
                        'mental_fatigue': w.mental_fatigue,
                        'hydration_level': w.hydration_level,
                        'hours_since_break': w.hours_since_break,
                        'context': w.context
                    }
                    for w in self.wellness_history[-500:]  # Save last 500
                ], f, indent=2, default=str)
            
            # Save preferences
            prefs_file = self.storage_path / "preferences.json"
            prefs_to_save = self.preferences.copy()
            # Convert break types to strings for JSON
            if 'preferred_break_types' in prefs_to_save:
                prefs_to_save['preferred_break_types'] = [
                    bt.value for bt in prefs_to_save['preferred_break_types']
                ]
            
            with open(prefs_file, 'w') as f:
                json.dump(prefs_to_save, f, indent=2)
            
            logger.debug("Break data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving break data: {e}")