"""
Difficulty Tracker Module - Enhanced version
Tracks and analyzes task difficulty levels and user performance patterns.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass, field
import json
from pathlib import Path
import asyncio
from scipy import stats
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class DifficultyLevel(Enum):
    """Enum for difficulty levels."""
    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"
    
    @property
    def value_numeric(self) -> int:
        """Get numeric value for calculations."""
        mapping = {
            "very_easy": 1,
            "easy": 2,
            "medium": 3,
            "hard": 4,
            "very_hard": 5
        }
        return mapping[self.value]
    
    @classmethod
    def from_numeric(cls, value: float) -> 'DifficultyLevel':
        """Convert numeric value to DifficultyLevel."""
        if value < 1.5:
            return cls.VERY_EASY
        elif value < 2.5:
            return cls.EASY
        elif value < 3.5:
            return cls.MEDIUM
        elif value < 4.5:
            return cls.HARD
        else:
            return cls.VERY_HARD

class TaskType(Enum):
    """Types of tasks that can be tracked."""
    CODING = "coding"
    LEARNING = "learning"
    READING = "reading"
    WRITING = "writing"
    PROBLEM_SOLVING = "problem_solving"
    RESEARCH = "research"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"

@dataclass
class TaskDifficulty:
    """Data class for task difficulty information."""
    task_id: str
    task_type: TaskType
    difficulty_level: DifficultyLevel
    time_taken: timedelta
    expected_time: timedelta
    success_rate: float
    attempts: int
    completion_time: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DifficultyTrend:
    """Data class for difficulty trends."""
    task_type: TaskType
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    slope: float
    confidence: float
    average_difficulty: float
    variability: float
    recommendations: List[str] = field(default_factory=list)

class DifficultyTracker:
    """
    Enhanced difficulty tracker that analyzes task difficulty patterns
    and provides insights for optimal challenge levels.
    """
    
    def __init__(self, storage_path: str = "data/patterns/difficulty"):
        """
        Initialize the difficulty tracker.
        
        Args:
            storage_path: Path to store difficulty data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Task history storage
        self.task_history: List[TaskDifficulty] = []
        self.current_tasks: Dict[str, TaskDifficulty] = {}
        
        # Difficulty metrics
        self.user_skill_level: Dict[TaskType, float] = defaultdict(lambda: 3.0)  # 1-5 scale
        self.difficulty_distribution: Dict[TaskType, Dict[DifficultyLevel, int]] = defaultdict(lambda: defaultdict(int))
        self.performance_by_difficulty: Dict[TaskType, Dict[DifficultyLevel, float]] = defaultdict(lambda: defaultdict(float))
        
        # Learning parameters
        self.adaptation_rate = 0.1
        self.confidence_threshold = 0.7
        self.optimal_difficulty_range = (2.5, 4.0)  # Between easy and hard
        
        # Time-based windows
        self.recent_window = timedelta(days=7)
        self.long_term_window = timedelta(days=30)
        
        # Load existing data
        self._load_data()
        
        logger.info("DifficultyTracker initialized successfully")
    
    def _load_data(self):
        """Load difficulty data from storage."""
        history_file = self.storage_path / "task_history.json"
        skill_file = self.storage_path / "user_skill.json"
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        task = TaskDifficulty(
                            task_id=item['task_id'],
                            task_type=TaskType(item['task_type']),
                            difficulty_level=DifficultyLevel(item['difficulty_level']),
                            time_taken=timedelta(seconds=item['time_taken']),
                            expected_time=timedelta(seconds=item['expected_time']),
                            success_rate=item['success_rate'],
                            attempts=item['attempts'],
                            completion_time=datetime.fromisoformat(item['completion_time']),
                            context=item.get('context', {}),
                            metadata=item.get('metadata', {})
                        )
                        self.task_history.append(task)
                logger.info(f"Loaded {len(self.task_history)} task records")
            except Exception as e:
                logger.error(f"Error loading task history: {e}")
        
        if skill_file.exists():
            try:
                with open(skill_file, 'r') as f:
                    skill_data = json.load(f)
                    for task_type_str, level in skill_data.items():
                        self.user_skill_level[TaskType(task_type_str)] = level
                logger.info("Loaded user skill levels")
            except Exception as e:
                logger.error(f"Error loading skill levels: {e}")
    
    async def record_task_completion(self,
                                    task_id: str,
                                    task_type: TaskType,
                                    time_taken: timedelta,
                                    expected_time: timedelta,
                                    success: bool,
                                    attempts: int = 1,
                                    context: Optional[Dict] = None,
                                    metadata: Optional[Dict] = None) -> TaskDifficulty:
        """
        Record completion of a task for difficulty analysis.
        
        Args:
            task_id: Unique task identifier
            task_type: Type of task
            time_taken: Actual time taken
            expected_time: Expected/estimated time
            success: Whether task was successful
            attempts: Number of attempts made
            context: Context information
            metadata: Additional metadata
            
        Returns:
            TaskDifficulty object with analysis
        """
        try:
            # Calculate difficulty based on performance
            difficulty = self._calculate_difficulty(
                time_taken, expected_time, success, attempts
            )
            
            # Create task difficulty record
            task = TaskDifficulty(
                task_id=task_id,
                task_type=task_type,
                difficulty_level=difficulty,
                time_taken=time_taken,
                expected_time=expected_time,
                success_rate=1.0 if success else 0.0,
                attempts=attempts,
                completion_time=datetime.now(),
                context=context or {},
                metadata=metadata or {}
            )
            
            # Add to history
            self.task_history.append(task)
            
            # Update metrics
            self._update_difficulty_metrics(task)
            
            # Update user skill level
            self._update_skill_level(task)
            
            # Remove from current tasks if present
            if task_id in self.current_tasks:
                del self.current_tasks[task_id]
            
            # Trim history
            self._trim_history()
            
            # Save data
            await self._save_data()
            
            logger.info(f"Recorded task completion: {task_id} with difficulty {difficulty.value}")
            
            return task
            
        except Exception as e:
            logger.error(f"Error recording task completion: {e}")
            raise
    
    def _calculate_difficulty(self,
                            time_taken: timedelta,
                            expected_time: timedelta,
                            success: bool,
                            attempts: int) -> DifficultyLevel:
        """
        Calculate difficulty level based on performance metrics.
        
        Args:
            time_taken: Actual time taken
            expected_time: Expected time
            success: Whether task was successful
            attempts: Number of attempts
            
        Returns:
            Calculated DifficultyLevel
        """
        # Time ratio (actual / expected)
        time_ratio = time_taken.total_seconds() / max(expected_time.total_seconds(), 1)
        
        # Base difficulty on time ratio
        if time_ratio < 0.5:
            base_difficulty = 1.5  # Very easy
        elif time_ratio < 0.8:
            base_difficulty = 2.5  # Easy
        elif time_ratio < 1.2:
            base_difficulty = 3.5  # Medium
        elif time_ratio < 1.8:
            base_difficulty = 4.5  # Hard
        else:
            base_difficulty = 5.0  # Very hard
        
        # Adjust for success
        if not success:
            base_difficulty += 0.5
        
        # Adjust for attempts
        if attempts > 1:
            base_difficulty += 0.2 * (attempts - 1)
        
        # Ensure within bounds
        final_difficulty = max(1.0, min(5.0, base_difficulty))
        
        return DifficultyLevel.from_numeric(final_difficulty)
    
    def _update_difficulty_metrics(self, task: TaskDifficulty):
        """Update difficulty distribution and performance metrics."""
        task_type = task.task_type
        difficulty = task.difficulty_level
        
        # Update distribution
        self.difficulty_distribution[task_type][difficulty] += 1
        
        # Update performance metrics
        current_perf = self.performance_by_difficulty[task_type][difficulty]
        new_perf = 0.7 * current_perf + 0.3 * task.success_rate
        self.performance_by_difficulty[task_type][difficulty] = new_perf
    
    def _update_skill_level(self, task: TaskDifficulty):
        """Update user skill level based on task performance."""
        task_type = task.task_type
        current_skill = self.user_skill_level[task_type]
        
        # Calculate performance delta
        task_difficulty_numeric = task.difficulty_level.value_numeric
        
        # If task was successful at or above current skill level
        if task.success_rate > 0.7 and task_difficulty_numeric >= current_skill:
            # Skill improvement
            delta = self.adaptation_rate * (task_difficulty_numeric - current_skill)
            self.user_skill_level[task_type] = min(5.0, current_skill + delta)
        
        # If task was unsuccessful at or below current skill level
        elif task.success_rate < 0.3 and task_difficulty_numeric <= current_skill:
            # Skill might be overestimated
            delta = self.adaptation_rate * (current_skill - task_difficulty_numeric)
            self.user_skill_level[task_type] = max(1.0, current_skill - delta)
        
        logger.debug(f"Updated skill for {task_type.value}: {current_skill:.2f} -> {self.user_skill_level[task_type]:.2f}")
    
    async def get_task_difficulty_analysis(self,
                                         task_type: Optional[TaskType] = None,
                                         days: int = 30) -> Dict[str, Any]:
        """
        Get detailed difficulty analysis.
        
        Args:
            task_type: Optional task type filter
            days: Number of days to analyze
            
        Returns:
            Dictionary with difficulty analysis
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter tasks
        tasks = [
            t for t in self.task_history
            if t.completion_time > cutoff_date
        ]
        
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        
        if not tasks:
            return {'message': 'No task data available for analysis'}
        
        # Calculate statistics
        difficulty_counts = defaultdict(int)
        success_by_difficulty = defaultdict(list)
        time_ratios_by_difficulty = defaultdict(list)
        
        for task in tasks:
            difficulty_counts[task.difficulty_level] += 1
            success_by_difficulty[task.difficulty_level].append(task.success_rate)
            time_ratio = task.time_taken.total_seconds() / max(task.expected_time.total_seconds(), 1)
            time_ratios_by_difficulty[task.difficulty_level].append(time_ratio)
        
        # Calculate optimal difficulty
        optimal_difficulty = self._find_optimal_difficulty(success_by_difficulty)
        
        # Generate trends
        trends = await self.analyze_difficulty_trends(task_type)
        
        # Calculate skill progression
        skill_progression = self._calculate_skill_progression(tasks)
        
        return {
            'total_tasks_analyzed': len(tasks),
            'difficulty_distribution': {
                d.value: count for d, count in difficulty_counts.items()
            },
            'success_rates': {
                d.value: np.mean(scores) for d, scores in success_by_difficulty.items()
            },
            'average_time_ratios': {
                d.value: np.mean(ratios) for d, ratios in time_ratios_by_difficulty.items()
            },
            'optimal_difficulty': optimal_difficulty.value if optimal_difficulty else None,
            'current_skill_level': {
                task_type.value: level for task_type, level in self.user_skill_level.items()
            } if not task_type else {task_type.value: self.user_skill_level[task_type]},
            'skill_progression': skill_progression,
            'trends': [self._trend_to_dict(t) for t in trends],
            'recommendations': self._generate_difficulty_recommendations(tasks, optimal_difficulty)
        }
    
    def _find_optimal_difficulty(self,
                               success_by_difficulty: Dict[DifficultyLevel, List[float]]) -> Optional[DifficultyLevel]:
        """Find the difficulty level with optimal learning potential."""
        optimal_score = -1
        optimal_difficulty = None
        
        for difficulty, success_rates in success_by_difficulty.items():
            if len(success_rates) < 3:
                continue
            
            avg_success = np.mean(success_rates)
            
            # Optimal difficulty should have moderate success rate (challenging but achievable)
            if 0.6 <= avg_success <= 0.85:
                # Score based on how close to optimal range and consistency
                score = 1.0 - abs(0.7 - avg_success)  # Peak at 70% success
                
                # Adjust for variability (lower variability is better)
                variability = np.std(success_rates) if len(success_rates) > 1 else 0
                score *= (1 - variability)
                
                if score > optimal_score:
                    optimal_score = score
                    optimal_difficulty = difficulty
        
        return optimal_difficulty
    
    def _calculate_skill_progression(self, tasks: List[TaskDifficulty]) -> Dict[str, Any]:
        """Calculate skill progression over time."""
        if len(tasks) < 5:
            return {'message': 'Insufficient data for progression analysis'}
        
        # Sort by time
        sorted_tasks = sorted(tasks, key=lambda t: t.completion_time)
        
        # Calculate moving average of difficulty handled
        window_size = min(10, len(sorted_tasks) // 3)
        difficulties = [t.difficulty_level.value_numeric for t in sorted_tasks]
        
        if window_size > 1:
            weights = np.ones(window_size) / window_size
            smoothed = np.convolve(difficulties, weights, mode='valid')
        else:
            smoothed = difficulties
        
        # Calculate trend
        x = np.arange(len(smoothed))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, smoothed)
        
        # Determine progression rate
        if slope > 0.05:
            progression_rate = 'improving'
        elif slope < -0.05:
            progression_rate = 'declining'
        else:
            progression_rate = 'stable'
        
        return {
            'current_level': difficulties[-1] if difficulties else 3.0,
            'starting_level': difficulties[0] if difficulties else 3.0,
            'progression_rate': progression_rate,
            'slope': slope,
            'confidence': r_value ** 2,
            'volatility': np.std(difficulties) if len(difficulties) > 1 else 0
        }
    
    async def analyze_difficulty_trends(self,
                                       task_type: Optional[TaskType] = None) -> List[DifficultyTrend]:
        """Analyze trends in difficulty over time."""
        trends = []
        
        types_to_analyze = [task_type] if task_type else list(TaskType)
        
        for t_type in types_to_analyze:
            # Get tasks for this type
            type_tasks = [
                t for t in self.task_history
                if t.task_type == t_type
            ]
            
            if len(type_tasks) < 10:
                continue
            
            # Sort by time
            sorted_tasks = sorted(type_tasks, key=lambda t: t.completion_time)
            
            # Extract difficulty values
            difficulties = [t.difficulty_level.value_numeric for t in sorted_tasks]
            x = np.arange(len(difficulties))
            
            # Linear regression for trend
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, difficulties)
            
            # Determine trend direction
            if slope > 0.02 and p_value < 0.1:
                direction = 'increasing'
            elif slope < -0.02 and p_value < 0.1:
                direction = 'decreasing'
            else:
                direction = 'stable'
            
            # Calculate variability
            variability = np.std(difficulties)
            
            # Generate recommendations
            recommendations = self._generate_trend_recommendations(
                t_type, direction, slope, difficulties[-1] if difficulties else 3.0
            )
            
            trend = DifficultyTrend(
                task_type=t_type,
                trend_direction=direction,
                slope=slope,
                confidence=r_value ** 2,
                average_difficulty=np.mean(difficulties),
                variability=variability,
                recommendations=recommendations
            )
            
            trends.append(trend)
        
        return trends
    
    def _generate_trend_recommendations(self,
                                       task_type: TaskType,
                                       direction: str,
                                       slope: float,
                                       current_difficulty: float) -> List[str]:
        """Generate recommendations based on difficulty trends."""
        recommendations = []
        
        if direction == 'increasing' and slope > 0.1:
            recommendations.append(
                f"You're tackling increasingly difficult {task_type.value} tasks. "
                "Consider reviewing fundamentals to ensure strong foundation."
            )
        elif direction == 'decreasing' and slope < -0.1:
            recommendations.append(
                f"Task difficulty has been decreasing. Challenge yourself with "
                f"more complex {task_type.value} tasks to promote growth."
            )
        
        # Compare with optimal range
        if current_difficulty < self.optimal_difficulty_range[0]:
            recommendations.append(
                f"Current tasks are below optimal challenge level. "
                f"Increase difficulty to around {self.optimal_difficulty_range[0]:.1f} for better learning."
            )
        elif current_difficulty > self.optimal_difficulty_range[1]:
            recommendations.append(
                f"Tasks might be too challenging. Consider taking a step back "
                f"to build confidence with medium-difficulty tasks."
            )
        
        return recommendations
    
    def _generate_difficulty_recommendations(self,
                                           tasks: List[TaskDifficulty],
                                           optimal_difficulty: Optional[DifficultyLevel]) -> List[str]:
        """Generate recommendations for optimal difficulty management."""
        recommendations = []
        
        if optimal_difficulty:
            recommendations.append(
                f"Your optimal learning difficulty is {optimal_difficulty.value}. "
                "Aim for tasks at this level for best progress."
            )
        
        # Analyze recent performance
        recent_tasks = [t for t in tasks if t.completion_time > datetime.now() - timedelta(days=7)]
        
        if recent_tasks:
            success_rate = np.mean([t.success_rate for t in recent_tasks])
            
            if success_rate < 0.5:
                recommendations.append(
                    "Recent tasks have low success rate. Consider reviewing "
                    "prerequisites or reducing difficulty temporarily."
                )
            elif success_rate > 0.9:
                recommendations.append(
                    "Excellent performance! You might be ready for more "
                    "challenging tasks to continue growing."
                )
        
        # Check for balance
        task_types = set(t.task_type for t in tasks)
        if len(task_types) > 1:
            recommendations.append(
                f"You're working on {len(task_types)} different task types. "
                "Consider focusing on one area to build deeper expertise."
            )
        
        return recommendations
    
    def _trend_to_dict(self, trend: DifficultyTrend) -> Dict:
        """Convert DifficultyTrend to dictionary."""
        return {
            'task_type': trend.task_type.value,
            'trend_direction': trend.trend_direction,
            'slope': trend.slope,
            'confidence': trend.confidence,
            'average_difficulty': trend.average_difficulty,
            'variability': trend.variability,
            'recommendations': trend.recommendations
        }
    
    async def predict_task_difficulty(self,
                                    task_type: TaskType,
                                    estimated_time: timedelta,
                                    context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Predict difficulty level for a new task.
        
        Args:
            task_type: Type of task
            estimated_time: Estimated time for task
            context: Context information
            
        Returns:
            Dictionary with difficulty prediction
        """
        # Get user skill for this task type
        user_skill = self.user_skill_level[task_type]
        
        # Get historical data for similar tasks
        similar_tasks = [
            t for t in self.task_history[-50:]  # Last 50 tasks
            if t.task_type == task_type
        ]
        
        if similar_tasks:
            # Calculate average difficulty for tasks with similar estimated time
            time_tolerance = timedelta(minutes=15)
            similar_time_tasks = [
                t for t in similar_tasks
                if abs((t.expected_time - estimated_time).total_seconds()) < time_tolerance.total_seconds()
            ]
            
            if similar_time_tasks:
                avg_difficulty = np.mean([t.difficulty_level.value_numeric for t in similar_time_tasks])
                confidence = min(1.0, len(similar_time_tasks) / 10)
            else:
                # Use all tasks of this type
                avg_difficulty = np.mean([t.difficulty_level.value_numeric for t in similar_tasks])
                confidence = 0.5
        else:
            # No history, base on skill level
            avg_difficulty = user_skill
            confidence = 0.3
        
        # Adjust for user skill
        if avg_difficulty > user_skill + 1.0:
            predicted = user_skill + 1.0
            reason = "Task may be challenging based on current skill level"
        elif avg_difficulty < user_skill - 1.0:
            predicted = user_skill - 0.5
            reason = "Task should be manageable given your skill level"
        else:
            predicted = avg_difficulty
            reason = "Task difficulty aligns with your current capabilities"
        
        # Adjust based on context
        if context:
            if context.get('energy_level', 0.5) < 0.3:
                predicted += 0.5  # Task will feel harder with low energy
                reason += " (low energy may increase perceived difficulty)"
            elif context.get('focus_level', 0.5) > 0.8:
                predicted -= 0.3  # Task may feel easier with high focus
        
        # Ensure within bounds
        predicted = max(1.0, min(5.0, predicted))
        
        return {
            'task_type': task_type.value,
            'predicted_difficulty': DifficultyLevel.from_numeric(predicted).value,
            'predicted_numeric': predicted,
            'confidence': confidence,
            'reason': reason,
            'user_skill_level': user_skill,
            'historical_basis': len(similar_tasks) if similar_tasks else 0
        }
    
    async def get_optimal_task_suggestion(self,
                                        available_time: timedelta,
                                        preferred_types: Optional[List[TaskType]] = None) -> Dict[str, Any]:
        """
        Suggest optimal task based on difficulty and available time.
        
        Args:
            available_time: Time available for task
            preferred_types: Preferred task types
            
        Returns:
            Dictionary with task suggestion
        """
        # Get all task types or preferred ones
        task_types = preferred_types if preferred_types else list(TaskType)
        
        suggestions = []
        
        for task_type in task_types:
            # Get recent tasks of this type
            recent_tasks = [
                t for t in self.task_history[-20:]
                if t.task_type == task_type
            ]
            
            if not recent_tasks:
                continue
            
            # Calculate average time for this task type
            avg_time = np.mean([t.time_taken.total_seconds() for t in recent_tasks])
            
            # Check if fits in available time
            if avg_time > available_time.total_seconds() * 1.2:
                continue  # Task too long
            
            # Get user skill and optimal difficulty
            user_skill = self.user_skill_level[task_type]
            optimal_difficulty = self._find_optimal_difficulty_for_type(task_type)
            
            # Calculate score for this task type
            time_score = 1.0 - (avg_time / available_time.total_seconds()) if avg_time <= available_time.total_seconds() else 0
            
            # Difficulty score (prefer tasks near optimal difficulty)
            if optimal_difficulty:
                difficulty_score = 1.0 - abs(optimal_difficulty.value_numeric - user_skill) / 4.0
            else:
                difficulty_score = 0.5
            
            # Variety score (avoid same type if done recently)
            last_task_time = max([t.completion_time for t in recent_tasks]) if recent_tasks else datetime.min
            hours_since = (datetime.now() - last_task_time).total_seconds() / 3600
            variety_score = min(1.0, hours_since / 24)  # Prefer if not done in last 24 hours
            
            # Combined score
            total_score = 0.4 * time_score + 0.4 * difficulty_score + 0.2 * variety_score
            
            suggestions.append({
                'task_type': task_type.value,
                'estimated_time': avg_time,
                'difficulty_level': user_skill,
                'optimal_difficulty': optimal_difficulty.value if optimal_difficulty else None,
                'score': total_score,
                'reason': self._generate_suggestion_reason(task_type, user_skill, hours_since)
            })
        
        # Sort by score
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'available_time_minutes': available_time.total_seconds() / 60,
            'suggestions': suggestions[:3],  # Top 3 suggestions
            'best_match': suggestions[0] if suggestions else None
        }
    
    def _find_optimal_difficulty_for_type(self, task_type: TaskType) -> Optional[DifficultyLevel]:
        """Find optimal difficulty for a specific task type."""
        success_by_difficulty = defaultdict(list)
        
        for task in self.task_history:
            if task.task_type == task_type:
                success_by_difficulty[task.difficulty_level].append(task.success_rate)
        
        return self._find_optimal_difficulty(success_by_difficulty)
    
    def _generate_suggestion_reason(self,
                                  task_type: TaskType,
                                  difficulty: float,
                                  hours_since: float) -> str:
        """Generate reason for task suggestion."""
        if hours_since < 4:
            return f"Quick {task_type.value} task to maintain momentum"
        elif hours_since < 24:
            return f"Good time for a {task_type.value} session"
        else:
            return f"Haven't done {task_type.value} recently - time to practice"
    
    def _trim_history(self, max_entries: int = 10000):
        """Trim task history to prevent unlimited growth."""
        if len(self.task_history) > max_entries:
            self.task_history = self.task_history[-max_entries:]
    
    async def _save_data(self):
        """Save difficulty data to storage."""
        try:
            # Save task history
            history_file = self.storage_path / "task_history.json"
            with open(history_file, 'w') as f:
                json.dump([
                    {
                        'task_id': t.task_id,
                        'task_type': t.task_type.value,
                        'difficulty_level': t.difficulty_level.value,
                        'time_taken': t.time_taken.total_seconds(),
                        'expected_time': t.expected_time.total_seconds(),
                        'success_rate': t.success_rate,
                        'attempts': t.attempts,
                        'completion_time': t.completion_time.isoformat(),
                        'context': t.context,
                        'metadata': t.metadata
                    }
                    for t in self.task_history[-1000:]  # Save last 1000
                ], f, indent=2, default=str)
            
            # Save user skill levels
            skill_file = self.storage_path / "user_skill.json"
            with open(skill_file, 'w') as f:
                json.dump({
                    task_type.value: level
                    for task_type, level in self.user_skill_level.items()
                }, f, indent=2)
            
            logger.debug("Difficulty data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving difficulty data: {e}")