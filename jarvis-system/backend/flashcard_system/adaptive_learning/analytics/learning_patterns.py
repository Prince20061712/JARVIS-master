"""
Core analytics engine for learning pattern analysis and prediction.
Implements Ebbinghaus retention curves, performance heatmaps, and weakness analysis.
"""

import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict
import json
import hashlib
from pathlib import Path
import pickle
from scipy import stats
from scipy.optimize import curve_fit
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetentionModel(Enum):
    """Mathematical models for retention curve fitting."""
    EXPONENTIAL = "exponential"
    POWER = "power"
    HYPERBOLIC = "hyperbolic"
    LOGISTIC = "logistic"


@dataclass
class RetentionCurve:
    """Represents an Ebbinghaus retention curve for a specific topic."""
    topic: str
    forgetting_rate: float  # Rate at which forgetting occurs
    initial_retention: float  # Initial retention percentage (typically 100%)
    time_units: str  # 'hours', 'days', 'weeks'
    model_type: RetentionModel
    data_points: List[Tuple[datetime, float]] = field(default_factory=list)
    predicted_forget_date: Optional[datetime] = None
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    r_squared: float = 0.0  # Goodness of fit

    def predict_retention(self, days_from_now: int) -> float:
        """
        Predict retention percentage after specified days.
        
        Args:
            days_from_now: Number of days from current time
            
        Returns:
            Predicted retention percentage (0-100)
        """
        if self.model_type == RetentionModel.EXPONENTIAL:
            return self.initial_retention * np.exp(-self.forgetting_rate * days_from_now)
        elif self.model_type == RetentionModel.POWER:
            return self.initial_retention * (days_from_now + 1) ** (-self.forgetting_rate)
        elif self.model_type == RetentionModel.HYPERBOLIC:
            return self.initial_retention / (1 + self.forgetting_rate * days_from_now)
        elif self.model_type == RetentionModel.LOGISTIC:
            return 100 / (1 + np.exp(self.forgetting_rate * (days_from_now - 7)))
        else:
            return max(0, 100 - self.forgetting_rate * days_from_now)

    def days_until_forget(self, threshold: float = 50.0) -> Optional[int]:
        """
        Calculate days until retention drops below threshold.
        
        Args:
            threshold: Retention percentage threshold (default 50%)
            
        Returns:
            Number of days until forgetting, or None if never forgets
        """
        if threshold <= 0:
            return None
            
        # Binary search for the day when retention crosses threshold
        left, right = 0, 365  # Search within a year
        while left < right:
            mid = (left + right) // 2
            retention = self.predict_retention(mid)
            if retention > threshold:
                left = mid + 1
            else:
                right = mid
                
        if left >= 365:
            return None
        return left


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for a study session or topic."""
    accuracy: float  # Percentage correct (0-100)
    avg_response_time: float  # Average response time in seconds
    consistency_score: float  # Variance in performance (0-100, higher = more consistent)
    mastery_level: float  # Estimated mastery (0-100)
    total_attempts: int
    correct_attempts: int
    topics_covered: List[str]
    emotional_states: Dict[str, float]  # Distribution of emotional states
    timestamp: datetime = field(default_factory=datetime.now)
    session_duration: Optional[float] = None  # Duration in minutes
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage."""
        return 100 - self.accuracy if self.total_attempts > 0 else 0
    
    @property
    def needs_review(self) -> bool:
        """Determine if topic needs review based on metrics."""
        return self.mastery_level < 70 or self.accuracy < 80
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'accuracy': self.accuracy,
            'avg_response_time': self.avg_response_time,
            'consistency_score': self.consistency_score,
            'mastery_level': self.mastery_level,
            'total_attempts': self.total_attempts,
            'correct_attempts': self.correct_attempts,
            'topics_covered': self.topics_covered,
            'emotional_states': self.emotional_states,
            'timestamp': self.timestamp.isoformat(),
            'session_duration': self.session_duration,
            'error_rate': self.error_rate,
            'needs_review': self.needs_review
        }


@dataclass
class WeaknessAnalysis:
    """Detailed analysis of learning weaknesses."""
    weak_topics: List[Tuple[str, float]]  # (topic, weakness_score)
    strong_topics: List[Tuple[str, float]]  # (topic, strength_score)
    improvement_pace: float  # Daily improvement rate
    recommended_focus: List[str]  # Topics to focus on
    critical_gaps: List[str]  # Topics with critical knowledge gaps
    topic_correlations: Dict[str, Dict[str, float]]  # How topics affect each other
    
    def get_priority_topics(self, limit: int = 5) -> List[str]:
        """Get highest priority topics for study."""
        # Combine weak topics and critical gaps
        priorities = []
        for topic, score in self.weak_topics:
            if topic in self.critical_gaps:
                priorities.append((topic, score * 1.5))  # Boost critical gaps
            else:
                priorities.append((topic, score))
        
        # Sort by priority score (higher = more urgent)
        priorities.sort(key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in priorities[:limit]]


@dataclass
class StudySessionMetrics:
    """Metrics for a single study session."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    flashcards_reviewed: int = 0
    viva_questions_answered: int = 0
    avg_difficulty: float = 0.0
    topics_studied: List[str] = field(default_factory=list)
    performance_scores: List[float] = field(default_factory=list)
    emotional_progression: List[Tuple[datetime, str, float]] = field(default_factory=list)
    
    @property
    def duration_minutes(self) -> float:
        """Calculate session duration in minutes."""
        if self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 60
        return 0.0
    
    @property
    def avg_performance(self) -> float:
        """Calculate average performance score."""
        return np.mean(self.performance_scores) if self.performance_scores else 0.0
    
    @property
    def learning_efficiency(self) -> float:
        """Calculate learning efficiency (items per minute)."""
        total_items = self.flashcards_reviewed + self.viva_questions_answered
        if self.duration_minutes > 0:
            return total_items / self.duration_minutes
        return 0.0


class LearningPatterns:
    """
    Advanced analytics engine for learning pattern analysis.
    Implements Ebbinghaus forgetting curves, performance prediction,
    and personalized learning recommendations.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the learning patterns analyzer.
        
        Args:
            data_dir: Directory for storing analytics data (optional)
        """
        self.data_dir = data_dir or Path.home() / '.jarvis' / 'analytics'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage for learning data
        self.flashcard_history: Dict[str, List[Dict]] = defaultdict(list)
        self.viva_history: Dict[str, List[Dict]] = defaultdict(list)
        self.emotional_history: List[Dict] = []
        self.retention_curves: Dict[str, RetentionCurve] = {}
        
        # Load existing data
        self._load_data()
        
        logger.info(f"LearningPatterns initialized with data directory: {self.data_dir}")
    
    def _load_data(self) -> None:
        """Load historical data from disk."""
        try:
            # Load flashcard history
            flashcard_file = self.data_dir / 'flashcard_history.pkl'
            if flashcard_file.exists():
                with open(flashcard_file, 'rb') as f:
                    self.flashcard_history = defaultdict(list, pickle.load(f))
            
            # Load viva history
            viva_file = self.data_dir / 'viva_history.pkl'
            if viva_file.exists():
                with open(viva_file, 'rb') as f:
                    self.viva_history = defaultdict(list, pickle.load(f))
            
            # Load emotional history
            emotional_file = self.data_dir / 'emotional_history.json'
            if emotional_file.exists():
                with open(emotional_file, 'r') as f:
                    self.emotional_history = json.load(f)
            
            logger.info("Historical data loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
    
    def _save_data(self) -> None:
        """Save data to disk."""
        try:
            # Save flashcard history
            with open(self.data_dir / 'flashcard_history.pkl', 'wb') as f:
                pickle.dump(dict(self.flashcard_history), f)
            
            # Save viva history
            with open(self.data_dir / 'viva_history.pkl', 'wb') as f:
                pickle.dump(dict(self.viva_history), f)
            
            # Save emotional history
            with open(self.data_dir / 'emotional_history.json', 'w') as f:
                json.dump(self.emotional_history, f, indent=2)
            
            logger.info("Data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def record_flashcard_review(self, 
                                user_id: str,
                                topic: str,
                                difficulty_rating: int,
                                response_time: float,
                                emotional_state: Optional[str] = None) -> None:
        """
        Record a flashcard review session.
        
        Args:
            user_id: User identifier
            topic: Topic being reviewed
            difficulty_rating: Rating from 0-5 (0=easy, 5=hard)
            response_time: Time taken to respond in seconds
            emotional_state: Detected emotional state (optional)
        """
        try:
            record = {
                'timestamp': datetime.now().isoformat(),
                'topic': topic,
                'difficulty_rating': difficulty_rating,
                'response_time': response_time,
                'emotional_state': emotional_state,
                'success': difficulty_rating < 3  # Consider rating <3 as successful
            }
            
            self.flashcard_history[user_id].append(record)
            
            # Update retention curve for this topic
            self._update_retention_curve(user_id, topic, record)
            
            # Save data periodically (every 10 records)
            if len(self.flashcard_history[user_id]) % 10 == 0:
                self._save_data()
                
            logger.debug(f"Flashcard review recorded for {user_id} on {topic}")
            
        except Exception as e:
            logger.error(f"Error recording flashcard review: {e}")
            raise
    
    def record_viva_response(self,
                            user_id: str,
                            session_id: str,
                            question: Dict,
                            answer: Dict,
                            emotional_state: Dict) -> None:
        """
        Record a viva response for analysis.
        
        Args:
            user_id: User identifier
            session_id: Viva session identifier
            question: Question details
            answer: Answer details
            emotional_state: Detected emotional state
        """
        try:
            record = {
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'question': question,
                'answer': answer,
                'emotional_state': emotional_state,
                'correct': answer.get('correct', False),
                'confidence': answer.get('confidence', 0.0),
                'response_time': answer.get('response_time', 0)
            }
            
            self.viva_history[user_id].append(record)
            
            # Record emotional state separately for pattern analysis
            self.emotional_history.append({
                'user_id': user_id,
                'timestamp': record['timestamp'],
                'state': emotional_state.get('primary_emotion'),
                'intensity': emotional_state.get('intensity', 0.5),
                'context': question.get('topic', 'unknown')
            })
            
            # Save periodically
            if len(self.viva_history[user_id]) % 5 == 0:
                self._save_data()
                
            logger.debug(f"Viva response recorded for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error recording viva response: {e}")
            raise
    
    def _update_retention_curve(self, user_id: str, topic: str, record: Dict) -> None:
        """
        Update the retention curve for a topic based on new data.
        
        Args:
            user_id: User identifier
            topic: Topic to update
            record: New review record
        """
        curve_key = f"{user_id}:{topic}"
        
        # Get historical data points for this topic
        topic_records = [
            r for r in self.flashcard_history[user_id] 
            if r['topic'] == topic
        ]
        
        if len(topic_records) < 2:
            # Not enough data for curve fitting
            return
            
        # Prepare data for curve fitting
        timestamps = []
        retentions = []
        
        first_record = datetime.fromisoformat(topic_records[0]['timestamp'])
        for r in topic_records:
            current = datetime.fromisoformat(r['timestamp'])
            days_diff = (current - first_record).days
            timestamps.append(days_diff)
            
            # Convert difficulty rating to retention (simplified model)
            # Rating 0-5: 0=100% retention, 5=20% retention
            retention = max(0, 100 - (r['difficulty_rating'] * 20))
            retentions.append(retention)
        
        try:
            # Fit exponential decay curve
            def exponential_decay(t, a, b):
                return a * np.exp(-b * t)
            
            # Convert to numpy arrays
            x_data = np.array(timestamps)
            y_data = np.array(retentions)
            
            # Fit curve
            popt, pcov = curve_fit(
                exponential_decay, 
                x_data, 
                y_data,
                p0=[100, 0.1],  # Initial guess
                maxfev=5000
            )
            
            a, b = popt
            
            # Calculate R-squared
            residuals = y_data - exponential_decay(x_data, a, b)
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((y_data - np.mean(y_data))**2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # Calculate confidence interval (simplified)
            perr = np.sqrt(np.diag(pcov))
            confidence_interval = (
                b - 1.96 * perr[1],
                b + 1.96 * perr[1]
            )
            
            # Create or update retention curve
            self.retention_curves[curve_key] = RetentionCurve(
                topic=topic,
                forgetting_rate=b,
                initial_retention=a,
                time_units='days',
                model_type=RetentionModel.EXPONENTIAL,
                data_points=[(datetime.fromisoformat(r['timestamp']), ret) 
                           for r, ret in zip(topic_records, retentions)],
                predicted_forget_date=datetime.now() + timedelta(
                    days=int(np.log(50/a) / -b) if a > 0 and b > 0 else 30
                ),
                confidence_interval=tuple(confidence_interval),
                r_squared=r_squared
            )
            
            logger.debug(f"Retention curve updated for {topic}")
            
        except Exception as e:
            logger.warning(f"Could not fit retention curve for {topic}: {e}")
    
    def generate_retention_curve(self, 
                                user_id: str, 
                                topic: str,
                                days_ahead: int = 30) -> RetentionCurve:
        """
        Generate Ebbinghaus retention curve for a specific topic.
        
        Args:
            user_id: User identifier
            topic: Topic to analyze
            days_ahead: Number of days to predict ahead
            
        Returns:
            RetentionCurve object with predictions
        """
        curve_key = f"{user_id}:{topic}"
        
        # Return cached curve if exists
        if curve_key in self.retention_curves:
            return self.retention_curves[curve_key]
        
        # Get topic records
        topic_records = [
            r for r in self.flashcard_history[user_id] 
            if r['topic'] == topic
        ]
        
        if not topic_records:
            # Return default curve if no data
            return RetentionCurve(
                topic=topic,
                forgetting_rate=0.1,  # Default forgetting rate
                initial_retention=100.0,
                time_units='days',
                model_type=RetentionModel.EXPONENTIAL,
                predicted_forget_date=datetime.now() + timedelta(days=7)
            )
        
        # Calculate average forgetting rate
        if len(topic_records) >= 2:
            # Use actual data to estimate forgetting rate
            first = topic_records[0]
            last = topic_records[-1]
            
            t1 = datetime.fromisoformat(first['timestamp'])
            t2 = datetime.fromisoformat(last['timestamp'])
            days_diff = max(1, (t2 - t1).days)
            
            r1 = 100 - (first['difficulty_rating'] * 20)
            r2 = 100 - (last['difficulty_rating'] * 20)
            
            # Calculate exponential forgetting rate
            forgetting_rate = -np.log(r2 / r1) / days_diff if r1 > 0 else 0.1
        else:
            forgetting_rate = 0.1  # Default
        
        # Generate data points for curve
        data_points = []
        for record in topic_records:
            timestamp = datetime.fromisoformat(record['timestamp'])
            retention = 100 - (record['difficulty_rating'] * 20)
            data_points.append((timestamp, retention))
        
        # Predict forget date
        days_to_50 = np.log(50/100) / -forgetting_rate if forgetting_rate > 0 else 30
        predicted_forget = datetime.now() + timedelta(days=int(days_to_50))
        
        return RetentionCurve(
            topic=topic,
            forgetting_rate=forgetting_rate,
            initial_retention=100.0,
            time_units='days',
            model_type=RetentionModel.EXPONENTIAL,
            data_points=data_points,
            predicted_forget_date=predicted_forget,
            confidence_interval=(forgetting_rate * 0.8, forgetting_rate * 1.2),
            r_squared=0.85  # Estimated goodness of fit
        )
    
    def generate_performance_heatmap(self, 
                                    user_id: str,
                                    time_period: str = 'week') -> Dict[str, Any]:
        """
        Generate performance heatmap showing strengths and weaknesses.
        
        Args:
            user_id: User identifier
            time_period: 'day', 'week', 'month', 'year'
            
        Returns:
            Heatmap data structure with performance metrics by topic
        """
        try:
            # Determine time range
            now = datetime.now()
            if time_period == 'day':
                start_time = now - timedelta(days=1)
            elif time_period == 'week':
                start_time = now - timedelta(weeks=1)
            elif time_period == 'month':
                start_time = now - timedelta(days=30)
            elif time_period == 'year':
                start_time = now - timedelta(days=365)
            else:
                start_time = now - timedelta(weeks=1)
            
            # Collect performance data
            topic_performance = defaultdict(lambda: {'correct': 0, 'total': 0, 'avg_time': []})
            
            # Process flashcard data
            for record in self.flashcard_history[user_id]:
                timestamp = datetime.fromisoformat(record['timestamp'])
                if timestamp >= start_time:
                    topic = record['topic']
                    topic_performance[topic]['total'] += 1
                    if record['success']:
                        topic_performance[topic]['correct'] += 1
                    topic_performance[topic]['avg_time'].append(record['response_time'])
            
            # Process viva data
            for record in self.viva_history[user_id]:
                timestamp = datetime.fromisoformat(record['timestamp'])
                if timestamp >= start_time:
                    topic = record['question'].get('topic', 'unknown')
                    topic_performance[topic]['total'] += 1
                    if record['correct']:
                        topic_performance[topic]['correct'] += 1
                    topic_performance[topic]['avg_time'].append(record['response_time'])
            
            # Calculate performance metrics
            heatmap_data = []
            for topic, data in topic_performance.items():
                if data['total'] > 0:
                    accuracy = (data['correct'] / data['total']) * 100
                    avg_time = np.mean(data['avg_time']) if data['avg_time'] else 0
                    consistency = 100 - (np.std(data['avg_time']) if len(data['avg_time']) > 1 else 0)
                    
                    # Color coding based on performance
                    if accuracy >= 80:
                        color = 'green'
                        status = 'strong'
                    elif accuracy >= 60:
                        color = 'yellow'
                        status = 'moderate'
                    else:
                        color = 'red'
                        status = 'weak'
                    
                    heatmap_data.append({
                        'topic': topic,
                        'accuracy': round(accuracy, 2),
                        'avg_response_time': round(avg_time, 2),
                        'consistency': round(consistency, 2),
                        'attempts': data['total'],
                        'color': color,
                        'status': status
                    })
            
            # Sort by accuracy
            heatmap_data.sort(key=lambda x: x['accuracy'])
            
            return {
                'time_period': time_period,
                'period_start': start_time.isoformat(),
                'period_end': now.isoformat(),
                'total_topics': len(heatmap_data),
                'topics': heatmap_data,
                'strong_topics': [t for t in heatmap_data if t['status'] == 'strong'],
                'weak_topics': [t for t in heatmap_data if t['status'] == 'weak'],
                'average_accuracy': np.mean([t['accuracy'] for t in heatmap_data]) if heatmap_data else 0
            }
            
        except Exception as e:
            logger.error(f"Error generating performance heatmap: {e}")
            return {
                'error': str(e),
                'time_period': time_period,
                'topics': []
            }
    
    def analyze_weaknesses(self, user_id: str) -> WeaknessAnalysis:
        """
        Perform deep analysis of learning weaknesses.
        
        Args:
            user_id: User identifier
            
        Returns:
            WeaknessAnalysis object with detailed analysis
        """
        try:
            # Get all performance data
            all_topics = set()
            topic_scores = {}
            
            # Process flashcard data
            for record in self.flashcard_history[user_id]:
                topic = record['topic']
                all_topics.add(topic)
                
                if topic not in topic_scores:
                    topic_scores[topic] = {'scores': [], 'recent': []}
                
                # Calculate score (inverse of difficulty)
                score = 100 - (record['difficulty_rating'] * 20)
                topic_scores[topic]['scores'].append(score)
                
                # Recent scores (last 5)
                if len(topic_scores[topic]['recent']) < 5:
                    topic_scores[topic]['recent'].append(score)
            
            # Process viva data
            for record in self.viva_history[user_id]:
                topic = record['question'].get('topic', 'unknown')
                all_topics.add(topic)
                
                if topic not in topic_scores:
                    topic_scores[topic] = {'scores': [], 'recent': []}
                
                # Calculate score from correctness and confidence
                score = 100 if record['correct'] else 50 * record.get('confidence', 0.5)
                topic_scores[topic]['scores'].append(score)
                
                if len(topic_scores[topic]['recent']) < 5:
                    topic_scores[topic]['recent'].append(score)
            
            # Calculate weakness scores
            weak_topics = []
            strong_topics = []
            critical_gaps = []
            
            for topic, scores in topic_scores.items():
                if scores['scores']:
                    avg_score = np.mean(scores['scores'])
                    recent_avg = np.mean(scores['recent']) if scores['recent'] else avg_score
                    
                    # Calculate weakness score (0-100, higher = weaker)
                    weakness = 100 - avg_score
                    
                    # Boost weakness if recent performance is worse
                    if recent_avg < avg_score:
                        weakness *= 1.2
                    
                    if weakness > 50:
                        weak_topics.append((topic, weakness))
                        if weakness > 75:
                            critical_gaps.append(topic)
                    else:
                        strength = avg_score
                        strong_topics.append((topic, strength))
            
            # Sort by weakness/strength
            weak_topics.sort(key=lambda x: x[1], reverse=True)
            strong_topics.sort(key=lambda x: x[1], reverse=True)
            
            # Calculate improvement pace (last 30 days vs previous 30 days)
            now = datetime.now()
            thirty_days_ago = now - timedelta(days=30)
            sixty_days_ago = now - timedelta(days=60)
            
            recent_scores = []
            older_scores = []
            
            for record in self.flashcard_history[user_id]:
                timestamp = datetime.fromisoformat(record['timestamp'])
                if timestamp >= thirty_days_ago:
                    recent_scores.append(100 - record['difficulty_rating'] * 20)
                elif timestamp >= sixty_days_ago:
                    older_scores.append(100 - record['difficulty_rating'] * 20)
            
            avg_recent = np.mean(recent_scores) if recent_scores else 0
            avg_older = np.mean(older_scores) if older_scores else 50
            
            improvement_pace = (avg_recent - avg_older) / 30  # Daily improvement
            
            # Calculate topic correlations
            topic_correlations = self._calculate_topic_correlations(user_id)
            
            # Generate recommendations
            recommended_focus = []
            for topic, weakness in weak_topics[:3]:
                recommended_focus.append(topic)
                # Add correlated topics that might help
                if topic in topic_correlations:
                    correlated = sorted(
                        topic_correlations[topic].items(),
                        key=lambda x: abs(x[1]),
                        reverse=True
                    )[:2]
                    for corr_topic, _ in correlated:
                        if corr_topic not in recommended_focus:
                            recommended_focus.append(corr_topic)
            
            return WeaknessAnalysis(
                weak_topics=weak_topics[:10],
                strong_topics=strong_topics[:10],
                improvement_pace=improvement_pace,
                recommended_focus=recommended_focus[:5],
                critical_gaps=critical_gaps[:5],
                topic_correlations=topic_correlations
            )
            
        except Exception as e:
            logger.error(f"Error analyzing weaknesses: {e}")
            return WeaknessAnalysis(
                weak_topics=[],
                strong_topics=[],
                improvement_pace=0.0,
                recommended_focus=[],
                critical_gaps=[],
                topic_correlations={}
            )
    
    def _calculate_topic_correlations(self, user_id: str) -> Dict[str, Dict[str, float]]:
        """
        Calculate correlations between different topics.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of topic correlations
        """
        correlations = defaultdict(dict)
        
        try:
            # Create topic performance matrix
            topic_sessions = defaultdict(list)
            
            for record in self.flashcard_history[user_id]:
                topic = record['topic']
                date = datetime.fromisoformat(record['timestamp']).date()
                score = 100 - record['difficulty_rating'] * 20
                topic_sessions[topic].append((date, score))
            
            # Get common topics
            topics = list(topic_sessions.keys())
            
            # Create correlation matrix
            for i, topic1 in enumerate(topics):
                for j, topic2 in enumerate(topics[i+1:], i+1):
                    # Align dates
                    dates1 = {d: s for d, s in topic_sessions[topic1]}
                    dates2 = {d: s for d, s in topic_sessions[topic2]}
                    
                    common_dates = set(dates1.keys()) & set(dates2.keys())
                    
                    if len(common_dates) >= 3:  # Need at least 3 common sessions
                        scores1 = [dates1[d] for d in common_dates]
                        scores2 = [dates2[d] for d in common_dates]
                        
                        # Calculate correlation
                        corr = np.corrcoef(scores1, scores2)[0, 1]
                        
                        if not np.isnan(corr):
                            correlations[topic1][topic2] = corr
                            correlations[topic2][topic1] = corr
            
        except Exception as e:
            logger.error(f"Error calculating topic correlations: {e}")
        
        return dict(correlations)
    
    def get_study_recommendations(self, user_id: str, limit: int = 5) -> List[Dict]:
        """
        Get personalized study recommendations based on analytics.
        
        Args:
            user_id: User identifier
            limit: Maximum number of recommendations
            
        Returns:
            List of study recommendations with priorities
        """
        try:
            # Get weakness analysis
            weaknesses = self.analyze_weaknesses(user_id)
            
            # Get retention curves for weak topics
            recommendations = []
            
            for topic, weakness_score in weaknesses.weak_topics[:limit]:
                curve = self.generate_retention_curve(user_id, topic)
                
                # Calculate priority score
                priority = weakness_score * 0.7
                
                # Boost priority if near forgetting
                days_to_forget = curve.days_until_forget()
                if days_to_forget and days_to_forget < 7:
                    priority *= 1.5
                
                recommendations.append({
                    'topic': topic,
                    'priority': round(min(100, priority), 2),
                    'weakness_score': round(weakness_score, 2),
                    'days_until_forget': days_to_forget,
                    'current_retention': curve.predict_retention(0),
                    'recommended_action': 'Immediate review' if days_to_forget and days_to_forget < 3 else 'Schedule review',
                    'estimated_time': f"{max(5, int(30 * weakness_score/100))} minutes"
                })
            
            # Add critical gaps
            for topic in weaknesses.critical_gaps:
                if topic not in [r['topic'] for r in recommendations]:
                    recommendations.append({
                        'topic': topic,
                        'priority': 100,
                        'weakness_score': 90,
                        'days_until_forget': 1,
                        'current_retention': 30,
                        'recommended_action': 'Critical - Review immediately',
                        'estimated_time': '45 minutes'
                    })
            
            # Sort by priority
            recommendations.sort(key=lambda x: x['priority'], reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def track_study_session(self, user_id: str, session_id: str) -> StudySessionMetrics:
        """
        Track and analyze a study session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            StudySessionMetrics for the session
        """
        try:
            # Get session data from viva history
            session_records = [
                r for r in self.viva_history[user_id]
                if r['session_id'] == session_id
            ]
            
            if not session_records:
                # Return empty metrics if session not found
                return StudySessionMetrics(
                    session_id=session_id,
                    start_time=datetime.now()
                )
            
            # Extract session information
            start_time = datetime.fromisoformat(session_records[0]['timestamp'])
            end_time = datetime.fromisoformat(session_records[-1]['timestamp'])
            
            topics = set()
            scores = []
            emotional_progression = []
            
            for record in session_records:
                topics.add(record['question'].get('topic', 'unknown'))
                scores.append(100 if record['correct'] else 0)
                
                emotional_progression.append((
                    datetime.fromisoformat(record['timestamp']),
                    record['emotional_state'].get('primary_emotion', 'neutral'),
                    record['emotional_state'].get('intensity', 0.5)
                ))
            
            # Calculate metrics
            avg_difficulty = np.mean([
                r['question'].get('difficulty', 3) 
                for r in session_records
            ]) if session_records else 0
            
            return StudySessionMetrics(
                session_id=session_id,
                start_time=start_time,
                end_time=end_time,
                flashcards_reviewed=0,  # Would need flashcard session data
                viva_questions_answered=len(session_records),
                avg_difficulty=avg_difficulty,
                topics_studied=list(topics),
                performance_scores=scores,
                emotional_progression=emotional_progression
            )
            
        except Exception as e:
            logger.error(f"Error tracking study session: {e}")
            return StudySessionMetrics(
                session_id=session_id,
                start_time=datetime.now()
            )
    
    def get_learning_insights(self, user_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive learning insights.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with learning insights and metrics
        """
        try:
            # Get all data
            weaknesses = self.analyze_weaknesses(user_id)
            recommendations = self.get_study_recommendations(user_id)
            
            # Calculate overall metrics
            all_scores = []
            for record in self.flashcard_history[user_id]:
                all_scores.append(100 - record['difficulty_rating'] * 20)
            for record in self.viva_history[user_id]:
                all_scores.append(100 if record['correct'] else 0)
            
            overall_mastery = np.mean(all_scores) if all_scores else 0
            
            # Analyze emotional patterns
            emotional_patterns = defaultdict(list)
            for record in self.emotional_history:
                if record.get('user_id') == user_id:
                    emotional_patterns[record['state']].append(record['intensity'])
            
            emotional_profile = {
                state: np.mean(intensities) 
                for state, intensities in emotional_patterns.items()
            }
            
            # Calculate study streak
            study_dates = set()
            for record in self.flashcard_history[user_id]:
                date = datetime.fromisoformat(record['timestamp']).date()
                study_dates.add(date)
            for record in self.viva_history[user_id]:
                date = datetime.fromisoformat(record['timestamp']).date()
                study_dates.add(date)
            
            # Calculate current streak
            current_streak = 0
            today = date.today()
            check_date = today
            while check_date in study_dates:
                current_streak += 1
                check_date = check_date - timedelta(days=1)
            
            return {
                'overall_mastery': round(overall_mastery, 2),
                'topics_mastered': len([t for t, _ in weaknesses.strong_topics if t[1] > 80]),
                'total_topics_studied': len(weaknesses.strong_topics) + len(weaknesses.weak_topics),
                'study_streak': current_streak,
                'emotional_profile': emotional_profile,
                'weaknesses': {
                    'critical_gaps': weaknesses.critical_gaps,
                    'weak_topics': weaknesses.weak_topics[:5]
                },
                'recommendations': recommendations,
                'improvement_pace': round(weaknesses.improvement_pace, 2),
                'estimated_time_to_mastery': self._estimate_time_to_mastery(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error generating learning insights: {e}")
            return {
                'error': str(e),
                'overall_mastery': 0,
                'recommendations': []
            }
    
    def _estimate_time_to_mastery(self, user_id: str) -> Dict[str, Any]:
        """
        Estimate time required to master current weak topics.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with time estimates
        """
        try:
            weaknesses = self.analyze_weaknesses(user_id)
            
            total_time = 0
            topic_estimates = []
            
            for topic, weakness_score in weaknesses.weak_topics[:10]:
                # Estimate study time needed (in minutes)
                # Assume 5 minutes per percentage point improvement
                needed_improvement = max(0, 80 - (100 - weakness_score))
                estimated_minutes = needed_improvement * 5
                
                topic_estimates.append({
                    'topic': topic,
                    'current_mastery': round(100 - weakness_score, 2),
                    'estimated_minutes': estimated_minutes,
                    'sessions_needed': max(1, int(estimated_minutes / 30))  # 30-min sessions
                })
                
                total_time += estimated_minutes
            
            return {
                'total_minutes': total_time,
                'total_hours': round(total_time / 60, 1),
                'sessions_needed': max(1, int(total_time / 30)),
                'topic_breakdown': topic_estimates,
                'estimated_completion': (datetime.now() + timedelta(minutes=total_time)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error estimating time to mastery: {e}")
            return {
                'total_minutes': 0,
                'error': str(e)
            }
    
    def export_analytics(self, user_id: str, format: str = 'json') -> Union[Dict, str]:
        """
        Export analytics data in various formats.
        
        Args:
            user_id: User identifier
            format: Export format ('json', 'csv', 'report')
            
        Returns:
            Exported data in requested format
        """
        try:
            insights = self.get_learning_insights(user_id)
            heatmap = self.generate_performance_heatmap(user_id)
            weaknesses = self.analyze_weaknesses(user_id)
            
            if format == 'json':
                return {
                    'user_id': user_id,
                    'export_time': datetime.now().isoformat(),
                    'insights': insights,
                    'heatmap': heatmap,
                    'weaknesses': {
                        'weak_topics': weaknesses.weak_topics,
                        'strong_topics': weaknesses.strong_topics,
                        'critical_gaps': weaknesses.critical_gaps
                    },
                    'retention_curves': {
                        topic: {
                            'forgetting_rate': curve.forgetting_rate,
                            'predicted_forget_date': curve.predicted_forget_date.isoformat() if curve.predicted_forget_date else None
                        }
                        for topic, curve in self.retention_curves.items()
                        if topic.startswith(f"{user_id}:")
                    }
                }
                
            elif format == 'report':
                # Generate human-readable report
                report_lines = [
                    f"Learning Analytics Report for User: {user_id}",
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "=" * 50,
                    f"\nOverall Mastery: {insights.get('overall_mastery', 0)}%",
                    f"Study Streak: {insights.get('study_streak', 0)} days",
                    f"Topics Studied: {insights.get('total_topics_studied', 0)}",
                    f"Topics Mastered: {insights.get('topics_mastered', 0)}",
                    "\nCritical Gaps:",
                    "-" * 20
                ]
                
                for topic in weaknesses.critical_gaps[:5]:
                    report_lines.append(f"  • {topic} (URGENT)")
                
                report_lines.extend([
                    "\nTop Weak Topics:",
                    "-" * 20
                ])
                
                for topic, score in weaknesses.weak_topics[:5]:
                    report_lines.append(f"  • {topic}: {score:.1f}% weak")
                
                report_lines.extend([
                    "\nRecommended Focus Areas:",
                    "-" * 20
                ])
                
                for rec in insights.get('recommendations', [])[:3]:
                    report_lines.append(f"  • {rec['topic']}: {rec['recommended_action']}")
                
                return "\n".join(report_lines)
            
            else:
                # Default to JSON
                return self.export_analytics(user_id, 'json')
                
        except Exception as e:
            logger.error(f"Error exporting analytics: {e}")
            return {'error': str(e)}
    
    def clear_user_data(self, user_id: str) -> bool:
        """
        Clear all analytics data for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id in self.flashcard_history:
                del self.flashcard_history[user_id]
            
            if user_id in self.viva_history:
                del self.viva_history[user_id]
            
            # Remove user-specific emotional records
            self.emotional_history = [
                r for r in self.emotional_history 
                if r.get('user_id') != user_id
            ]
            
            # Remove user-specific retention curves
            self.retention_curves = {
                k: v for k, v in self.retention_curves.items()
                if not k.startswith(f"{user_id}:")
            }
            
            self._save_data()
            logger.info(f"Cleared analytics data for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing user data: {e}")
            return False