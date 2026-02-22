"""
Time Analyzer Module - Enhanced version
Analyzes time usage patterns and provides productivity optimization insights.
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
from scipy import stats, signal
from sklearn.cluster import DBSCAN
import pandas as pd

logger = logging.getLogger(__name__)

class TimePattern(Enum):
    """Enum for time patterns."""
    PEAK_PRODUCTIVITY = "peak_productivity"
    DEEP_WORK = "deep_work"
    SHALLOW_WORK = "shallow_work"
    BREAK = "break"
    DISTRACTED = "distracted"
    LEARNING = "learning"
    COMMUNICATION = "communication"
    PLANNING = "planning"

class ProductivityWindow(Enum):
    """Enum for productivity windows."""
    OPTIMAL = "optimal"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    AVOID = "avoid"

@dataclass
class TimeBlock:
    """Data class for time blocks."""
    start_time: datetime
    end_time: datetime
    pattern: TimePattern
    productivity_score: float  # 0-1
    task_type: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    interruptions: int = 0
    energy_level: float = 0.5

@dataclass
class DailyRhythm:
    """Data class for daily rhythm analysis."""
    date: datetime.date
    peak_hours: List[int]
    trough_hours: List[int]
    optimal_windows: List[Tuple[datetime, datetime]]
    energy_curve: List[float]
    consistency_score: float

@dataclass
class TimeSavingSuggestion:
    """Data class for time-saving suggestions."""
    category: str
    current_time: float  # Current time spent (minutes)
    optimized_time: float  # Optimized time (minutes)
    savings: float  # Time saved (minutes)
    strategy: str
    confidence: float
    actionable: bool

class TimeAnalyzer:
    """
    Enhanced time analyzer that identifies patterns in time usage
    and provides optimization suggestions.
    """
    
    def __init__(self, storage_path: str = "data/patterns/time"):
        """
        Initialize the time analyzer.
        
        Args:
            storage_path: Path to store time analysis data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Time data storage
        self.time_blocks: List[TimeBlock] = []
        self.daily_rhythms: List[DailyRhythm] = []
        self.interruption_log: List[Dict] = []
        
        # Analysis metrics
        self.productivity_by_hour: Dict[int, List[float]] = defaultdict(list)
        self.pattern_durations: Dict[TimePattern, List[float]] = defaultdict(list)
        self.transition_matrix: Dict[TimePattern, Dict[TimePattern, int]] = defaultdict(lambda: defaultdict(int))
        
        # User preferences
        self.preferred_work_hours: Tuple[int, int] = (9, 17)  # 9 AM to 5 PM
        self.optimal_session_length = timedelta(minutes=90)
        self.break_frequency = timedelta(minutes=45)
        
        # Load existing data
        self._load_data()
        
        logger.info("TimeAnalyzer initialized successfully")
    
    def _load_data(self):
        """Load time analysis data from storage."""
        blocks_file = self.storage_path / "time_blocks.json"
        rhythms_file = self.storage_path / "daily_rhythms.json"
        
        if blocks_file.exists():
            try:
                with open(blocks_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        block = TimeBlock(
                            start_time=datetime.fromisoformat(item['start_time']),
                            end_time=datetime.fromisoformat(item['end_time']),
                            pattern=TimePattern(item['pattern']),
                            productivity_score=item['productivity_score'],
                            task_type=item.get('task_type'),
                            context=item.get('context', {}),
                            interruptions=item.get('interruptions', 0),
                            energy_level=item.get('energy_level', 0.5)
                        )
                        self.time_blocks.append(block)
                        
                        # Update metrics
                        self._update_block_metrics(block)
                logger.info(f"Loaded {len(self.time_blocks)} time blocks")
            except Exception as e:
                logger.error(f"Error loading time blocks: {e}")
        
        if rhythms_file.exists():
            try:
                with open(rhythms_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        rhythm = DailyRhythm(
                            date=datetime.fromisoformat(item['date']).date(),
                            peak_hours=item['peak_hours'],
                            trough_hours=item['trough_hours'],
                            optimal_windows=[
                                (datetime.fromisoformat(start), datetime.fromisoformat(end))
                                for start, end in item['optimal_windows']
                            ],
                            energy_curve=item['energy_curve'],
                            consistency_score=item['consistency_score']
                        )
                        self.daily_rhythms.append(rhythm)
                logger.info(f"Loaded {len(self.daily_rhythms)} daily rhythms")
            except Exception as e:
                logger.error(f"Error loading daily rhythms: {e}")
    
    def _update_block_metrics(self, block: TimeBlock):
        """Update metrics with new time block."""
        hour = block.start_time.hour
        self.productivity_by_hour[hour].append(block.productivity_score)
        
        duration = (block.end_time - block.start_time).total_seconds() / 60
        self.pattern_durations[block.pattern].append(duration)
    
    async def record_time_block(self, block: TimeBlock) -> None:
        """
        Record a time block for analysis.
        
        Args:
            block: Time block to record
        """
        self.time_blocks.append(block)
        self._update_block_metrics(block)
        
        # Update transition matrix if we have previous block
        if len(self.time_blocks) > 1:
            prev_block = self.time_blocks[-2]
            self.transition_matrix[prev_block.pattern][block.pattern] += 1
        
        # Trim history
        self._trim_history()
        
        # Save data
        await self._save_data()
        
        logger.info(f"Recorded time block: {block.pattern.value} from {block.start_time}")
    
    async def record_interruption(self,
                                time: datetime,
                                interruption_type: str,
                                duration: timedelta,
                                context: Dict[str, Any]) -> None:
        """
        Record an interruption.
        
        Args:
            time: Time of interruption
            interruption_type: Type of interruption
            duration: Duration of interruption
            context: Context information
        """
        interruption = {
            'time': time.isoformat(),
            'type': interruption_type,
            'duration_seconds': duration.total_seconds(),
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        self.interruption_log.append(interruption)
        
        # Update the current time block's interruption count
        if self.time_blocks:
            current_block = self.time_blocks[-1]
            if current_block.start_time <= time <= current_block.end_time:
                current_block.interruptions += 1
        
        logger.info(f"Recorded interruption: {interruption_type} for {duration.total_seconds()}s")
    
    async def analyze_daily_patterns(self, date: Optional[datetime.date] = None) -> DailyRhythm:
        """
        Analyze patterns for a specific day.
        
        Args:
            date: Date to analyze (today if None)
            
        Returns:
            DailyRhythm object with analysis
        """
        target_date = date or datetime.now().date()
        
        # Get blocks for this day
        day_blocks = [
            b for b in self.time_blocks
            if b.start_time.date() == target_date
        ]
        
        if len(day_blocks) < 3:
            logger.warning(f"Insufficient data for {target_date}")
            return None
        
        # Calculate productivity by hour
        hourly_productivity = defaultdict(list)
        for block in day_blocks:
            for hour in range(block.start_time.hour, block.end_time.hour + 1):
                if 0 <= hour < 24:
                    hourly_productivity[hour].append(block.productivity_score)
        
        # Average productivity by hour
        avg_by_hour = {
            hour: np.mean(scores)
            for hour, scores in hourly_productivity.items()
            if scores
        }
        
        # Find peak and trough hours
        if avg_by_hour:
            sorted_hours = sorted(avg_by_hour.items(), key=lambda x: x[1], reverse=True)
            peak_hours = [hour for hour, _ in sorted_hours[:3]]
            trough_hours = [hour for hour, _ in sorted_hours[-3:]]
        else:
            peak_hours = []
            trough_hours = []
        
        # Find optimal windows (continuous periods of high productivity)
        optimal_windows = []
        current_window = None
        
        for hour in range(24):
            productivity = avg_by_hour.get(hour, 0)
            
            if productivity > 0.7:  # High productivity threshold
                if current_window is None:
                    current_window = [datetime.combine(target_date, datetime.min.time()) + timedelta(hours=hour)]
                elif hour == 23:
                    current_window.append(
                        datetime.combine(target_date, datetime.min.time()) + timedelta(hours=hour, minutes=59)
                    )
                    optimal_windows.append((current_window[0], current_window[1]))
            else:
                if current_window is not None:
                    current_window.append(
                        datetime.combine(target_date, datetime.min.time()) + timedelta(hours=hour-1, minutes=59)
                    )
                    optimal_windows.append((current_window[0], current_window[1]))
                    current_window = None
        
        # Generate energy curve
        energy_curve = [avg_by_hour.get(hour, 0.5) for hour in range(24)]
        
        # Calculate consistency score
        if len(day_blocks) > 1:
            productivity_variance = np.var([b.productivity_score for b in day_blocks])
            consistency_score = 1 / (1 + productivity_variance)  # Normalize to 0-1
        else:
            consistency_score = 1.0
        
        rhythm = DailyRhythm(
            date=target_date,
            peak_hours=peak_hours,
            trough_hours=trough_hours,
            optimal_windows=optimal_windows,
            energy_curve=energy_curve,
            consistency_score=consistency_score
        )
        
        self.daily_rhythms.append(rhythm)
        
        return rhythm
    
    async def get_productivity_windows(self,
                                     date: Optional[datetime.date] = None,
                                     min_duration: timedelta = timedelta(minutes=30)) -> List[Tuple[datetime, datetime, ProductivityWindow]]:
        """
        Get productivity windows for a specific date.
        
        Args:
            date: Date to analyze (today if None)
            min_duration: Minimum window duration
            
        Returns:
            List of (start, end, window_type) tuples
        """
        target_date = date or datetime.now().date()
        
        # Get or analyze rhythm for this date
        rhythm = next(
            (r for r in self.daily_rhythms if r.date == target_date),
            None
        )
        
        if not rhythm:
            rhythm = await self.analyze_daily_patterns(target_date)
        
        if not rhythm:
            return []
        
        windows = []
        
        # Classify each hour
        for hour in range(24):
            productivity = rhythm.energy_curve[hour]
            
            # Determine window type
            if productivity > 0.8:
                window_type = ProductivityWindow.OPTIMAL
            elif productivity > 0.6:
                window_type = ProductivityWindow.GOOD
            elif productivity > 0.4:
                window_type = ProductivityWindow.MODERATE
            elif productivity > 0.2:
                window_type = ProductivityWindow.POOR
            else:
                window_type = ProductivityWindow.AVOID
            
            start = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=hour)
            end = start + timedelta(hours=1)
            
            windows.append((start, end, window_type))
        
        # Merge consecutive windows of same type
        merged = []
        current = None
        
        for start, end, wtype in windows:
            if current is None:
                current = [start, end, wtype]
            elif wtype == current[2] and start == current[1]:
                current[1] = end
            else:
                if current[1] - current[0] >= min_duration:
                    merged.append(tuple(current))
                current = [start, end, wtype]
        
        if current and current[1] - current[0] >= min_duration:
            merged.append(tuple(current))
        
        return merged
    
    async def find_time_saving_opportunities(self, days: int = 30) -> List[TimeSavingSuggestion]:
        """
        Find opportunities to save time based on patterns.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of time-saving suggestions
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_blocks = [
            b for b in self.time_blocks
            if b.start_time > cutoff_date
        ]
        
        if len(recent_blocks) < 10:
            return []
        
        suggestions = []
        
        # 1. Analyze meeting/communication patterns
        comm_blocks = [
            b for b in recent_blocks
            if b.pattern in [TimePattern.COMMUNICATION]
        ]
        
        if comm_blocks:
            total_comm_time = sum(
                (b.end_time - b.start_time).total_seconds() / 60
                for b in comm_blocks
            )
            
            # Check if communication could be batched
            avg_session_length = np.mean([
                (b.end_time - b.start_time).total_seconds() / 60
                for b in comm_blocks
            ])
            
            if avg_session_length < 15:  # Many short communications
                optimized_time = total_comm_time * 0.7  # 30% savings through batching
                
                suggestions.append(TimeSavingSuggestion(
                    category='communication',
                    current_time=total_comm_time,
                    optimized_time=optimized_time,
                    savings=total_comm_time - optimized_time,
                    strategy="Batch short communications into dedicated time blocks",
                    confidence=0.8,
                    actionable=True
                ))
        
        # 2. Analyze interruption patterns
        if self.interruption_log:
            recent_interruptions = [
                i for i in self.interruption_log[-100:]
                if datetime.fromisoformat(i['time']) > cutoff_date
            ]
            
            if recent_interruptions:
                total_interruption_time = sum(
                    i['duration_seconds'] for i in recent_interruptions
                ) / 60  # Minutes
                
                # Group by type
                by_type = defaultdict(float)
                for i in recent_interruptions:
                    by_type[i['type']] += i['duration_seconds'] / 60
                
                # Suggest strategies for top interruption types
                for itype, duration in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:3]:
                    if duration > 30:  # More than 30 minutes lost
                        suggestions.append(TimeSavingSuggestion(
                            category=f'interruption_{itype}',
                            current_time=duration,
                            optimized_time=duration * 0.5,
                            savings=duration * 0.5,
                            strategy=f"Use 'Do Not Disturb' mode during focus time to reduce {itype} interruptions",
                            confidence=0.7,
                            actionable=True
                        ))
        
        # 3. Analyze task switching costs
        if len(recent_blocks) > 5:
            # Calculate average time between pattern changes
            pattern_changes = 0
            for i in range(1, len(recent_blocks)):
                if recent_blocks[i].pattern != recent_blocks[i-1].pattern:
                    pattern_changes += 1
            
            avg_time_between_changes = (len(recent_blocks) * self.optimal_session_length.total_seconds() / 60) / max(pattern_changes, 1)
            
            if avg_time_between_changes < 30:  # Switching too often
                suggestions.append(TimeSavingSuggestion(
                    category='task_switching',
                    current_time=avg_time_between_changes,
                    optimized_time=45,  # Aim for 45-minute focus blocks
                    savings=45 - avg_time_between_changes,
                    strategy="Reduce task switching by grouping similar tasks together",
                    confidence=0.6,
                    actionable=True
                ))
        
        # 4. Analyze deep work opportunities
        deep_work_blocks = [
            b for b in recent_blocks
            if b.pattern == TimePattern.DEEP_WORK
        ]
        
        if deep_work_blocks:
            total_deep_work = sum(
                (b.end_time - b.start_time).total_seconds() / 3600
                for b in deep_work_blocks
            )
            
            # Calculate average per day
            days_analyzed = days
            avg_daily_deep_work = total_deep_work / days_analyzed
            
            if avg_daily_deep_work < 2:  # Less than 2 hours of deep work per day
                suggestions.append(TimeSavingSuggestion(
                    category='deep_work',
                    current_time=avg_daily_deep_work * 60,  # Convert to minutes
                    optimized_time=120,  # Target 2 hours
                    savings=120 - (avg_daily_deep_work * 60),
                    strategy="Schedule deep work during your peak productivity hours",
                    confidence=0.9,
                    actionable=True
                ))
        
        return sorted(suggestions, key=lambda x: x.savings, reverse=True)
    
    async def predict_optimal_task_time(self,
                                      task_type: str,
                                      duration: timedelta,
                                      preferred_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Predict optimal time for a specific task.
        
        Args:
            task_type: Type of task
            duration: Expected duration
            preferred_time: User's preferred time if any
            
        Returns:
            Dictionary with optimal time recommendations
        """
        # Get recent productivity patterns
        recent_blocks = self.time_blocks[-50:] if len(self.time_blocks) > 50 else self.time_blocks
        
        if len(recent_blocks) < 10:
            return {
                'optimal_time': preferred_time or datetime.now(),
                'confidence': 0.3,
                'reason': 'Insufficient data for accurate prediction'
            }
        
        # Calculate productivity by hour for similar task types
        similar_tasks = [
            b for b in recent_blocks
            if b.task_type == task_type
        ]
        
        hourly_scores = defaultdict(list)
        
        if similar_tasks:
            for block in similar_tasks:
                for hour in range(block.start_time.hour, block.end_time.hour + 1):
                    hourly_scores[hour].append(block.productivity_score)
        
        # Also consider general productivity patterns
        for hour, scores in self.productivity_by_hour.items():
            hourly_scores[hour].extend(scores)
        
        # Calculate weighted scores
        weighted_scores = {}
        for hour, scores in hourly_scores.items():
            if len(scores) >= 3:
                # Weight more recent scores higher
                weighted_score = np.mean(scores)
                weighted_scores[hour] = weighted_score
        
        if not weighted_scores:
            return {
                'optimal_time': preferred_time or datetime.now(),
                'confidence': 0.4,
                'reason': 'Using default scheduling'
            }
        
        # Find best time slot
        best_hour = max(weighted_scores.items(), key=lambda x: x[1])[0]
        
        # Adjust for task duration
        if duration > timedelta(hours=2):
            # Need a longer block, look for consecutive high-scoring hours
            best_blocks = []
            for start_hour in range(24):
                end_hour = start_hour + int(duration.total_seconds() / 3600)
                if end_hour > 23:
                    continue
                
                block_scores = [
                    weighted_scores.get(h, 0)
                    for h in range(start_hour, end_hour + 1)
                ]
                avg_score = np.mean(block_scores)
                best_blocks.append((start_hour, avg_score))
            
            if best_blocks:
                best_hour = max(best_blocks, key=lambda x: x[1])[0]
        
        # Consider preferred time
        if preferred_time:
            pref_hour = preferred_time.hour
            if pref_hour in weighted_scores:
                # Blend preferred and optimal
                pref_score = weighted_scores[pref_hour]
                opt_score = weighted_scores[best_hour]
                
                if pref_score > opt_score * 0.8:  # If preferred time is reasonably good
                    best_hour = pref_hour
                    reason = "Preferred time is also productive"
                else:
                    reason = f"Optimal time ({best_hour}:00) is significantly more productive"
            else:
                reason = f"Insufficient data for preferred time, using optimal ({best_hour}:00)"
        else:
            reason = f"Based on your patterns, {best_hour}:00 is optimal for this task"
        
        # Calculate confidence
        confidence = len(weighted_scores) / 24  # More hours with data = higher confidence
        confidence *= min(1.0, len(similar_tasks) / 10)  # Adjust for task-specific data
        
        optimal_time = datetime.now().replace(
            hour=best_hour,
            minute=0,
            second=0,
            microsecond=0
        )
        
        # If time has passed, suggest next occurrence
        if optimal_time < datetime.now():
            optimal_time += timedelta(days=1)
        
        return {
            'optimal_time': optimal_time.isoformat(),
            'confidence': min(1.0, confidence),
            'reason': reason,
            'expected_productivity': weighted_scores.get(best_hour, 0.5),
            'alternative_times': [
                h for h, s in sorted(weighted_scores.items(), key=lambda x: x[1], reverse=True)[1:4]
            ]
        }
    
    async def get_time_usage_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get summary of time usage patterns.
        
        Args:
            days: Number of days to summarize
            
        Returns:
            Dictionary with time usage summary
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_blocks = [
            b for b in self.time_blocks
            if b.start_time > cutoff_date
        ]
        
        if not recent_blocks:
            return {'message': 'No recent time data'}
        
        # Calculate total time by pattern
        time_by_pattern = defaultdict(float)
        for block in recent_blocks:
            duration = (block.end_time - block.start_time).total_seconds() / 3600
            time_by_pattern[block.pattern.value] += duration
        
        total_time = sum(time_by_pattern.values())
        
        # Calculate productivity metrics
        avg_productivity = np.mean([b.productivity_score for b in recent_blocks])
        productivity_trend = self._calculate_productivity_trend(recent_blocks)
        
        # Calculate focus metrics
        deep_work_time = time_by_pattern.get(TimePattern.DEEP_WORK.value, 0)
        deep_work_ratio = deep_work_time / max(total_time, 1)
        
        # Calculate interruption metrics
        total_interruptions = sum(b.interruptions for b in recent_blocks)
        interruptions_per_hour = total_interruptions / max(total_time, 1)
        
        # Find most productive time
        hourly_productivity = defaultdict(list)
        for block in recent_blocks:
            hourly_productivity[block.start_time.hour].append(block.productivity_score)
        
        best_hour = max(
            [(hour, np.mean(scores)) for hour, scores in hourly_productivity.items() if len(scores) >= 3],
            key=lambda x: x[1],
            default=(9, 0.5)
        )[0]
        
        # Get time-saving opportunities
        savings = await self.find_time_saving_opportunities(days)
        
        return {
            'period_days': days,
            'total_time_hours': total_time,
            'time_distribution': dict(time_by_pattern),
            'average_productivity': avg_productivity,
            'productivity_trend': productivity_trend,
            'deep_work_ratio': deep_work_ratio,
            'interruptions_per_hour': interruptions_per_hour,
            'most_productive_hour': best_hour,
            'potential_time_savings': [
                {
                    'category': s.category,
                    'savings_minutes': s.savings,
                    'strategy': s.strategy
                }
                for s in savings[:5]
            ],
            'total_potential_savings': sum(s.savings for s in savings)
        }
    
    def _calculate_productivity_trend(self, blocks: List[TimeBlock]) -> str:
        """Calculate productivity trend from time blocks."""
        if len(blocks) < 5:
            return 'insufficient_data'
        
        # Group by day
        daily_productivity = defaultdict(list)
        for block in blocks:
            daily_productivity[block.start_time.date()].append(block.productivity_score)
        
        # Calculate daily averages
        dates = []
        averages = []
        for date, scores in sorted(daily_productivity.items()):
            dates.append(date)
            averages.append(np.mean(scores))
        
        if len(averages) < 3:
            return 'insufficient_data'
        
        # Linear regression
        x = np.arange(len(averages))
        slope, _, _, _, _ = stats.linregress(x, averages)
        
        if slope > 0.02:
            return 'improving'
        elif slope < -0.02:
            return 'declining'
        else:
            return 'stable'
    
    async def recommend_break_schedule(self,
                                     start_time: datetime,
                                     end_time: datetime) -> List[Dict[str, Any]]:
        """
        Recommend optimal break schedule for a work session.
        
        Args:
            start_time: Session start time
            end_time: Session end time
            
        Returns:
            List of recommended break times
        """
        session_duration = (end_time - start_time).total_seconds() / 3600
        
        # Default: Pomodoro-style (25 min work, 5 min break)
        if session_duration <= 1:
            # Short session
            return [{
                'time': (start_time + timedelta(minutes=25)).isoformat(),
                'duration_minutes': 5,
                'type': 'short',
                'reason': 'Pomodoro break'
            }]
        
        # Analyze optimal break patterns from history
        break_blocks = [
            b for b in self.time_blocks[-50:]
            if b.pattern == TimePattern.BREAK
        ]
        
        if break_blocks:
            # Calculate average break duration and interval
            avg_break_duration = np.mean([
                (b.end_time - b.start_time).total_seconds() / 60
                for b in break_blocks
            ])
            
            # Find patterns in when breaks are taken
            break_times = [b.start_time.hour + b.start_time.minute/60 for b in break_blocks]
            if break_times:
                # Cluster break times
                clustering = DBSCAN(eps=0.5, min_samples=2).fit(np.array(break_times).reshape(-1, 1))
                unique_clusters = set(clustering.labels_)
                
                if len(unique_clusters) > 1:  # Found patterns
                    # Recommend breaks at similar times
                    recommendations = []
                    current_time = start_time
                    
                    while current_time < end_time:
                        # Find closest cluster center
                        hour = current_time.hour + current_time.minute/60
                        cluster_distances = []
                        
                        for label in unique_clusters:
                            if label >= 0:
                                cluster_points = [break_times[i] for i, l in enumerate(clustering.labels_) if l == label]
                                center = np.mean(cluster_points)
                                cluster_distances.append((abs(hour - center), center))
                        
                        if cluster_distances:
                            closest_center = min(cluster_distances, key=lambda x: x[0])[1]
                            time_diff = (closest_center - hour) % 24
                            
                            if time_diff < 2:  # Within 2 hours of pattern
                                break_time = current_time + timedelta(hours=time_diff)
                                if break_time < end_time:
                                    recommendations.append({
                                        'time': break_time.isoformat(),
                                        'duration_minutes': avg_break_duration,
                                        'type': 'pattern_based',
                                        'reason': 'Based on your break patterns'
                                    })
                                    current_time = break_time + timedelta(minutes=avg_break_duration)
                                    continue
                        
                        # Fallback to regular intervals
                        current_time += timedelta(minutes=45)
                    
                    return recommendations
        
        # Default schedule based on work duration
        recommendations = []
        
        if session_duration <= 2:
            # 2 short breaks
            intervals = [45, 45]
        elif session_duration <= 4:
            # 3 breaks (2 short, 1 long)
            intervals = [45, 90, 45]
        else:
            # Multiple breaks with a lunch break
            intervals = [45, 90, 45, 120, 45]
        
        current = start_time
        for i, interval in enumerate(intervals):
            current += timedelta(minutes=interval)
            if current < end_time:
                break_type = 'lunch' if interval > 90 else 'short'
                recommendations.append({
                    'time': current.isoformat(),
                    'duration_minutes': 15 if break_type == 'lunch' else 5,
                    'type': break_type,
                    'reason': f'Recommended {break_type} break after {interval} minutes'
                })
        
        return recommendations
    
    async def get_weekly_patterns(self) -> Dict[str, Any]:
        """Analyze patterns across weeks."""
        if len(self.time_blocks) < 7 * 5:  # At least a week of data
            return {'message': 'Insufficient data for weekly analysis'}
        
        # Group by day of week
        daily_stats = defaultdict(lambda: {
            'blocks': [],
            'total_time': 0,
            'avg_productivity': []
        })
        
        for block in self.time_blocks[-7*4:]:  # Last 4 weeks
            dow = block.start_time.strftime('%A')
            daily_stats[dow]['blocks'].append(block)
            duration = (block.end_time - block.start_time).total_seconds() / 3600
            daily_stats[dow]['total_time'] += duration
            daily_stats[dow]['avg_productivity'].append(block.productivity_score)
        
        # Calculate averages
        for dow in daily_stats:
            if daily_stats[dow]['avg_productivity']:
                daily_stats[dow]['avg_productivity'] = np.mean(daily_stats[dow]['avg_productivity'])
            else:
                daily_stats[dow]['avg_productivity'] = 0
        
        # Find best and worst days
        sorted_days = sorted(
            daily_stats.items(),
            key=lambda x: x[1]['avg_productivity'],
            reverse=True
        )
        
        best_day = sorted_days[0][0] if sorted_days else None
        worst_day = sorted_days[-1][0] if sorted_days else None
        
        # Calculate consistency across weeks
        weekly_patterns = []
        for week in range(4):
            week_start = datetime.now() - timedelta(weeks=week+1)
            week_end = week_start + timedelta(days=7)
            
            week_blocks = [
                b for b in self.time_blocks
                if week_start <= b.start_time < week_end
            ]
            
            if week_blocks:
                weekly_patterns.append({
                    'week': week + 1,
                    'total_hours': sum(
                        (b.end_time - b.start_time).total_seconds() / 3600
                        for b in week_blocks
                    ),
                    'avg_productivity': np.mean([b.productivity_score for b in week_blocks])
                })
        
        return {
            'best_day': best_day,
            'worst_day': worst_day,
            'daily_averages': {
                dow: {
                    'hours': stats['total_time'],
                    'productivity': stats['avg_productivity']
                }
                for dow, stats in daily_stats.items()
            },
            'weekly_patterns': weekly_patterns,
            'consistency_score': 1 - np.std([w['total_hours'] for w in weekly_patterns]) / max(np.mean([w['total_hours'] for w in weekly_patterns]), 1) if weekly_patterns else 0
        }
    
    def _trim_history(self, max_blocks: int = 10000, max_interruptions: int = 5000):
        """Trim history to prevent unlimited growth."""
        if len(self.time_blocks) > max_blocks:
            self.time_blocks = self.time_blocks[-max_blocks:]
        
        if len(self.interruption_log) > max_interruptions:
            self.interruption_log = self.interruption_log[-max_interruptions:]
        
        if len(self.daily_rhythms) > 365:  # Keep 1 year of daily rhythms
            self.daily_rhythms = self.daily_rhythms[-365:]
    
    async def _save_data(self):
        """Save time analysis data to storage."""
        try:
            # Save time blocks
            blocks_file = self.storage_path / "time_blocks.json"
            with open(blocks_file, 'w') as f:
                json.dump([
                    {
                        'start_time': b.start_time.isoformat(),
                        'end_time': b.end_time.isoformat(),
                        'pattern': b.pattern.value,
                        'productivity_score': b.productivity_score,
                        'task_type': b.task_type,
                        'context': b.context,
                        'interruptions': b.interruptions,
                        'energy_level': b.energy_level
                    }
                    for b in self.time_blocks[-1000:]  # Save last 1000
                ], f, indent=2, default=str)
            
            # Save daily rhythms
            rhythms_file = self.storage_path / "daily_rhythms.json"
            with open(rhythms_file, 'w') as f:
                json.dump([
                    {
                        'date': r.date.isoformat(),
                        'peak_hours': r.peak_hours,
                        'trough_hours': r.trough_hours,
                        'optimal_windows': [
                            (start.isoformat(), end.isoformat())
                            for start, end in r.optimal_windows
                        ],
                        'energy_curve': r.energy_curve,
                        'consistency_score': r.consistency_score
                    }
                    for r in self.daily_rhythms[-90:]  # Save last 90 days
                ], f, indent=2, default=str)
            
            # Save interruption log
            interruptions_file = self.storage_path / "interruptions.json"
            with open(interruptions_file, 'w') as f:
                json.dump(self.interruption_log[-500:], f, indent=2, default=str)
            
            logger.debug("Time analysis data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving time analysis data: {e}")