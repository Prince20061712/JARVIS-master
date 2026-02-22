"""
Performance Predictor Module - Enhanced version
Predicts user performance and provides actionable insights for improvement.
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
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class PerformanceMetric(Enum):
    """Enum for performance metrics."""
    PRODUCTIVITY = "productivity"
    FOCUS = "focus"
    ACCURACY = "accuracy"
    SPEED = "speed"
    QUALITY = "quality"
    CONSISTENCY = "consistency"

class PredictionType(Enum):
    """Types of predictions."""
    SHORT_TERM = "short_term"  # Next few hours
    MEDIUM_TERM = "medium_term"  # Next few days
    LONG_TERM = "long_term"  # Next few weeks

@dataclass
class PerformanceMetrics:
    """Data class for performance metrics."""
    timestamp: datetime
    productivity_score: float  # 0-1
    focus_score: float  # 0-1
    accuracy_score: float  # 0-1
    speed_score: float  # 0-1
    quality_score: float  # 0-1
    consistency_score: float  # 0-1
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PredictionResult:
    """Data class for prediction results."""
    metric: PerformanceMetric
    predicted_value: float
    confidence_interval: Tuple[float, float]
    prediction_time: datetime
    features_importance: Dict[str, float]
    recommendations: List[str] = field(default_factory=list)

@dataclass
class PerformanceFactor:
    """Data class for factors affecting performance."""
    name: str
    impact: float  # -1 to 1 (negative to positive)
    confidence: float
    category: str  # 'environmental', 'personal', 'task', 'temporal'
    actionable: bool

class PerformancePredictor:
    """
    Enhanced performance predictor that uses machine learning to forecast
    performance and identify key factors affecting productivity.
    """
    
    def __init__(self, storage_path: str = "data/patterns/performance"):
        """
        Initialize the performance predictor.
        
        Args:
            storage_path: Path to store performance data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Performance data storage
        self.performance_history: List[PerformanceMetrics] = []
        self.prediction_history: List[PredictionResult] = []
        
        # ML Models
        self.models: Dict[PerformanceMetric, Any] = {}
        self.scalers: Dict[PerformanceMetric, StandardScaler] = {}
        self.feature_importance: Dict[PerformanceMetric, Dict[str, float]] = defaultdict(dict)
        
        # Model parameters
        self.model_version = "1.0.0"
        self.retrain_threshold = 100  # Retrain after 100 new samples
        self.samples_since_train = 0
        
        # Performance factors
        self.performance_factors: Dict[PerformanceMetric, List[PerformanceFactor]] = defaultdict(list)
        self.baseline_performance: Dict[PerformanceMetric, float] = defaultdict(float)
        
        # Feature engineering
        self.feature_columns = [
            'hour', 'day_of_week', 'day_of_month', 'month',
            'is_weekend', 'is_morning', 'is_afternoon', 'is_evening',
            'session_duration', 'break_frequency', 'task_switches',
            'energy_level', 'stress_level', 'sleep_hours',
            'caffeine_intake', 'exercise_minutes', 'screen_time'
        ]
        
        # Load existing data
        self._load_data()
        
        # Initialize or load models
        self._initialize_models()
        
        logger.info("PerformancePredictor initialized successfully")
    
    def _load_data(self):
        """Load performance data from storage."""
        history_file = self.storage_path / "performance_history.json"
        models_file = self.storage_path / "models.pkl"
        factors_file = self.storage_path / "performance_factors.json"
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        metrics = PerformanceMetrics(
                            timestamp=datetime.fromisoformat(item['timestamp']),
                            productivity_score=item['productivity_score'],
                            focus_score=item['focus_score'],
                            accuracy_score=item['accuracy_score'],
                            speed_score=item['speed_score'],
                            quality_score=item['quality_score'],
                            consistency_score=item['consistency_score'],
                            context=item.get('context', {}),
                            metadata=item.get('metadata', {})
                        )
                        self.performance_history.append(metrics)
                logger.info(f"Loaded {len(self.performance_history)} performance records")
            except Exception as e:
                logger.error(f"Error loading performance history: {e}")
        
        if factors_file.exists():
            try:
                with open(factors_file, 'r') as f:
                    data = json.load(f)
                    for metric_str, factors in data.items():
                        metric = PerformanceMetric(metric_str)
                        for factor_data in factors:
                            factor = PerformanceFactor(
                                name=factor_data['name'],
                                impact=factor_data['impact'],
                                confidence=factor_data['confidence'],
                                category=factor_data['category'],
                                actionable=factor_data['actionable']
                            )
                            self.performance_factors[metric].append(factor)
                logger.info("Loaded performance factors")
            except Exception as e:
                logger.error(f"Error loading performance factors: {e}")
    
    def _initialize_models(self):
        """Initialize or load ML models."""
        models_file = self.storage_path / "models.pkl"
        
        if models_file.exists():
            try:
                data = joblib.load(models_file)
                self.models = data.get('models', {})
                self.scalers = data.get('scalers', {})
                self.feature_importance = data.get('feature_importance', {})
                self.model_version = data.get('version', '1.0.0')
                logger.info("Loaded existing ML models")
            except Exception as e:
                logger.error(f"Error loading models: {e}")
                self._create_default_models()
        else:
            self._create_default_models()
    
    def _create_default_models(self):
        """Create default ML models for each metric."""
        for metric in PerformanceMetric:
            self.models[metric] = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            self.scalers[metric] = StandardScaler()
        
        logger.info("Created default ML models")
    
    async def record_performance(self,
                               metrics: PerformanceMetrics) -> None:
        """
        Record a performance measurement.
        
        Args:
            metrics: Performance metrics to record
        """
        self.performance_history.append(metrics)
        self.samples_since_train += 1
        
        # Trim history
        self._trim_history()
        
        # Retrain models if threshold reached
        if self.samples_since_train >= self.retrain_threshold:
            await self.retrain_models()
        
        # Save data
        await self._save_data()
        
        logger.info(f"Recorded performance metrics at {metrics.timestamp}")
    
    async def predict_performance(self,
                                target_time: datetime,
                                context: Dict[str, Any],
                                metrics: Optional[List[PerformanceMetric]] = None) -> Dict[str, PredictionResult]:
        """
        Predict performance for a specific time.
        
        Args:
            target_time: Time to predict for
            context: Context information
            metrics: Specific metrics to predict (all if None)
            
        Returns:
            Dictionary mapping metrics to predictions
        """
        predictions = {}
        
        # Prepare features
        features = self._extract_features(target_time, context)
        
        # Predict each requested metric
        metrics_to_predict = metrics or list(PerformanceMetric)
        
        for metric in metrics_to_predict:
            if metric not in self.models:
                continue
            
            try:
                # Scale features
                features_scaled = self.scalers[metric].fit_transform([features])[0]
                
                # Make prediction
                predicted_value = self.models[metric].predict([features_scaled])[0]
                
                # Calculate confidence interval using ensemble variance
                confidence_interval = self._calculate_confidence_interval(
                    metric, features_scaled, predicted_value
                )
                
                # Get feature importance for this prediction
                importance = self._get_local_feature_importance(
                    metric, features_scaled, predicted_value
                )
                
                # Generate recommendations
                recommendations = self._generate_performance_recommendations(
                    metric, predicted_value, context
                )
                
                predictions[metric] = PredictionResult(
                    metric=metric,
                    predicted_value=float(predicted_value),
                    confidence_interval=confidence_interval,
                    prediction_time=target_time,
                    features_importance=importance,
                    recommendations=recommendations
                )
                
            except Exception as e:
                logger.error(f"Error predicting {metric.value}: {e}")
        
        # Store predictions
        self.prediction_history.extend(predictions.values())
        
        return predictions
    
    def _extract_features(self, time: datetime, context: Dict[str, Any]) -> np.ndarray:
        """Extract features from time and context."""
        features = []
        
        # Temporal features
        features.extend([
            time.hour / 24.0,  # Hour of day (normalized)
            time.weekday() / 6.0,  # Day of week
            time.day / 31.0,  # Day of month
            time.month / 12.0,  # Month
            1 if time.weekday() >= 5 else 0,  # Is weekend
            1 if 5 <= time.hour < 12 else 0,  # Is morning
            1 if 12 <= time.hour < 17 else 0,  # Is afternoon
            1 if 17 <= time.hour < 22 else 0,  # Is evening
        ])
        
        # Context features (with defaults)
        features.extend([
            context.get('session_duration', 0) / 3600,  # Hours
            context.get('break_frequency', 0.5),
            context.get('task_switches', 5) / 20,  # Normalized
            context.get('energy_level', 0.5),
            context.get('stress_level', 0.3),
            context.get('sleep_hours', 7) / 12,  # Normalized
            context.get('caffeine_intake', 0) / 500,  # mg, normalized
            context.get('exercise_minutes', 0) / 120,  # Normalized
            context.get('screen_time', 480) / 720,  # Minutes, normalized
        ])
        
        return np.array(features)
    
    def _calculate_confidence_interval(self,
                                     metric: PerformanceMetric,
                                     features: np.ndarray,
                                     prediction: float) -> Tuple[float, float]:
        """Calculate confidence interval for prediction."""
        # Use historical prediction errors to estimate confidence
        if len(self.prediction_history) < 10:
            return (max(0, prediction - 0.2), min(1, prediction + 0.2))
        
        # Get recent prediction errors for this metric
        recent_errors = []
        for result in self.prediction_history[-50:]:
            if result.metric == metric:
                # Find actual value around prediction time
                actual = self._find_actual_performance(metric, result.prediction_time)
                if actual is not None:
                    error = abs(actual - result.predicted_value)
                    recent_errors.append(error)
        
        if not recent_errors:
            return (max(0, prediction - 0.15), min(1, prediction + 0.15))
        
        # Calculate confidence interval based on error distribution
        std_error = np.std(recent_errors)
        margin = 1.96 * std_error  # 95% confidence interval
        
        return (
            max(0, prediction - margin),
            min(1, prediction + margin)
        )
    
    def _find_actual_performance(self,
                               metric: PerformanceMetric,
                               time: datetime) -> Optional[float]:
        """Find actual performance value near given time."""
        # Look for performance record within 30 minutes
        for record in self.performance_history[-100:]:
            time_diff = abs((record.timestamp - time).total_seconds())
            if time_diff < 1800:  # Within 30 minutes
                if metric == PerformanceMetric.PRODUCTIVITY:
                    return record.productivity_score
                elif metric == PerformanceMetric.FOCUS:
                    return record.focus_score
                elif metric == PerformanceMetric.ACCURACY:
                    return record.accuracy_score
                elif metric == PerformanceMetric.SPEED:
                    return record.speed_score
                elif metric == PerformanceMetric.QUALITY:
                    return record.quality_score
                elif metric == PerformanceMetric.CONSISTENCY:
                    return record.consistency_score
        return None
    
    def _get_local_feature_importance(self,
                                    metric: PerformanceMetric,
                                    features: np.ndarray,
                                    prediction: float) -> Dict[str, float]:
        """Get feature importance for a specific prediction."""
        if metric not in self.models:
            return {}
        
        # Use permutation importance for local explanation
        base_prediction = prediction
        importance = {}
        
        for i, feature_name in enumerate(self.feature_columns):
            if i >= len(features):
                break
            
            # Perturb feature and measure impact
            perturbed_features = features.copy()
            perturbed_features[i] = np.random.normal(features[i], 0.1)
            
            try:
                new_prediction = self.models[metric].predict([perturbed_features])[0]
                impact = abs(new_prediction - base_prediction)
                importance[feature_name] = float(impact)
            except:
                continue
        
        # Normalize
        total = sum(importance.values())
        if total > 0:
            importance = {k: v/total for k, v in importance.items()}
        
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def _generate_performance_recommendations(self,
                                            metric: PerformanceMetric,
                                            predicted_value: float,
                                            context: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on performance prediction."""
        recommendations = []
        
        # Compare with baseline
        baseline = self.baseline_performance[metric]
        
        if predicted_value < baseline - 0.15:
            recommendations.append(
                f"Predicted {metric.value} is below your baseline. "
                f"Consider taking a break or changing your environment."
            )
        elif predicted_value > baseline + 0.15:
            recommendations.append(
                f"Excellent predicted {metric.value}! "
                f"This is a great time for challenging tasks."
            )
        
        # Metric-specific recommendations
        if metric == PerformanceMetric.FOCUS and predicted_value < 0.6:
            recommendations.extend([
                "Try the Pomodoro technique (25 min work, 5 min break)",
                "Minimize distractions by silencing notifications",
                "Consider using focus music or white noise"
            ])
        
        elif metric == PerformanceMetric.ENERGY and predicted_value < 0.5:
            recommendations.extend([
                "Take a short walk to boost energy",
                "Stay hydrated - drink a glass of water",
                "Consider a healthy snack for sustained energy"
            ])
        
        elif metric == PerformanceMetric.PRODUCTIVITY and predicted_value > 0.8:
            recommendations.extend([
                "Tackle your most important tasks now",
                "Batch similar tasks together for efficiency",
                "Save routine tasks for lower-energy periods"
            ])
        
        # Context-based recommendations
        if context.get('stress_level', 0.5) > 0.7:
            recommendations.append(
                "High stress detected. Consider a mindfulness break "
                "or breathing exercise before starting."
            )
        
        if context.get('sleep_hours', 7) < 6:
            recommendations.append(
                "Limited sleep may affect performance. "
                "Consider lighter tasks today."
            )
        
        return recommendations[:5]  # Return top 5 recommendations
    
    async def analyze_performance_factors(self,
                                        days: int = 30) -> Dict[PerformanceMetric, List[PerformanceFactor]]:
        """
        Analyze factors affecting performance.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary mapping metrics to influential factors
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_performance = [
            p for p in self.performance_history
            if p.timestamp > cutoff_date
        ]
        
        if len(recent_performance) < 10:
            return {}
        
        # Prepare data for analysis
        X = []
        y_dict = defaultdict(list)
        
        for record in recent_performance:
            features = self._extract_features(record.timestamp, record.context)
            X.append(features)
            
            y_dict[PerformanceMetric.PRODUCTIVITY].append(record.productivity_score)
            y_dict[PerformanceMetric.FOCUS].append(record.focus_score)
            y_dict[PerformanceMetric.ACCURACY].append(record.accuracy_score)
            y_dict[PerformanceMetric.SPEED].append(record.speed_score)
            y_dict[PerformanceMetric.QUALITY].append(record.quality_score)
            y_dict[PerformanceMetric.CONSISTENCY].append(record.consistency_score)
        
        X = np.array(X)
        
        # Analyze for each metric
        for metric, y in y_dict.items():
            if len(set(y)) < 5:  # Need some variance
                continue
            
            # Train a simple model for factor analysis
            model = RandomForestRegressor(n_estimators=50, random_state=42)
            model.fit(X, y)
            
            # Get feature importance
            importance = model.feature_importances_
            
            # Identify top factors
            top_indices = np.argsort(importance)[-10:][::-1]
            
            factors = []
            for idx in top_indices:
                if idx < len(self.feature_columns):
                    factor_name = self.feature_columns[idx]
                    impact = importance[idx]
                    
                    # Determine if factor is actionable
                    actionable = factor_name not in ['hour', 'day_of_week', 'month', 'is_weekend']
                    
                    # Categorize factor
                    if factor_name in ['hour', 'day_of_week', 'month', 'is_weekend']:
                        category = 'temporal'
                    elif factor_name in ['energy_level', 'stress_level', 'sleep_hours']:
                        category = 'personal'
                    elif factor_name in ['session_duration', 'break_frequency', 'task_switches']:
                        category = 'task'
                    else:
                        category = 'environmental'
                    
                    factor = PerformanceFactor(
                        name=factor_name.replace('_', ' ').title(),
                        impact=float(impact),
                        confidence=float(model.score(X, y)),
                        category=category,
                        actionable=actionable
                    )
                    factors.append(factor)
            
            self.performance_factors[metric] = factors
        
        return self.performance_factors
    
    async def predict_optimal_schedule(self,
                                     available_hours: List[Tuple[datetime, datetime]],
                                     tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict optimal schedule for tasks based on performance predictions.
        
        Args:
            available_hours: List of available time windows
            tasks: List of tasks with metadata
            
        Returns:
            Dictionary with optimized schedule
        """
        schedule = []
        
        for start_time, end_time in available_hours:
            window_duration = (end_time - start_time).total_seconds() / 3600
            
            # Predict performance throughout the window
            predictions = []
            current_time = start_time
            
            while current_time < end_time:
                # Predict for this time slot
                context = {
                    'session_duration': window_duration,
                    'energy_level': 0.5,  # Default
                    'stress_level': 0.3
                }
                
                pred = await self.predict_performance(
                    current_time,
                    context,
                    [PerformanceMetric.PRODUCTIVITY, PerformanceMetric.FOCUS]
                )
                
                predictions.append({
                    'time': current_time,
                    'productivity': pred.get(PerformanceMetric.PRODUCTIVITY),
                    'focus': pred.get(PerformanceMetric.FOCUS)
                })
                
                current_time += timedelta(minutes=30)  # 30-minute slots
            
            # Find best slots for each task
            for task in tasks:
                task_duration = task.get('duration', 1.0)  # Hours
                task_difficulty = task.get('difficulty', 3)  # 1-5
                task_type = task.get('type', 'general')
                
                # Find best time slot for this task
                best_score = -1
                best_slot = None
                
                for i in range(len(predictions) - int(task_duration * 2)):  # 30-min slots
                    slot_predictions = predictions[i:i + int(task_duration * 2)]
                    
                    # Calculate weighted score based on task requirements
                    if task_difficulty > 3.5:  # Hard task
                        # Need high focus and productivity
                        score = np.mean([
                            (p['productivity'].predicted_value if p['productivity'] else 0.5) *
                            (p['focus'].predicted_value if p['focus'] else 0.5)
                            for p in slot_predictions
                        ])
                    elif task_type == 'creative':
                        # Need good focus, productivity less important
                        score = np.mean([
                            (p['focus'].predicted_value if p['focus'] else 0.5)
                            for p in slot_predictions
                        ])
                    else:  # Routine task
                        # Any time is fine, but avoid peak productivity
                        avg_productivity = np.mean([
                            p['productivity'].predicted_value if p['productivity'] else 0.5
                            for p in slot_predictions
                        ])
                        score = 1 - avg_productivity  # Prefer low productivity times
                    
                    if score > best_score:
                        best_score = score
                        best_slot = slot_predictions[0]['time']
                
                if best_slot:
                    schedule.append({
                        'task': task.get('name', 'Unnamed'),
                        'start_time': best_slot.isoformat(),
                        'duration': task_duration,
                        'expected_performance': best_score,
                        'task_type': task_type,
                        'difficulty': task_difficulty
                    })
        
        # Sort schedule by time
        schedule.sort(key=lambda x: x['start_time'])
        
        return {
            'schedule': schedule,
            'total_tasks': len(schedule),
            'total_hours': sum(t['duration'] for t in schedule),
            'average_performance': np.mean([t['expected_performance'] for t in schedule]) if schedule else 0
        }
    
    async def get_performance_trends(self,
                                   metric: PerformanceMetric,
                                   days: int = 30) -> Dict[str, Any]:
        """Get performance trends over time."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter records
        relevant_records = [
            r for r in self.performance_history
            if r.timestamp > cutoff_date
        ]
        
        if len(relevant_records) < 5:
            return {'message': 'Insufficient data for trend analysis'}
        
        # Extract values
        timestamps = [r.timestamp for r in relevant_records]
        values = []
        
        for record in relevant_records:
            if metric == PerformanceMetric.PRODUCTIVITY:
                values.append(record.productivity_score)
            elif metric == PerformanceMetric.FOCUS:
                values.append(record.focus_score)
            elif metric == PerformanceMetric.ACCURACY:
                values.append(record.accuracy_score)
            elif metric == PerformanceMetric.SPEED:
                values.append(record.speed_score)
            elif metric == PerformanceMetric.QUALITY:
                values.append(record.quality_score)
            elif metric == PerformanceMetric.CONSISTENCY:
                values.append(record.consistency_score)
        
        # Calculate trend
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        # Calculate moving averages
        window = min(7, len(values) // 3)
        if window > 1:
            weights = np.ones(window) / window
            moving_avg = np.convolve(values, weights, mode='valid')
        else:
            moving_avg = values
        
        # Detect cycles
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(values, distance=5)
        valleys, _ = find_peaks([-v for v in values], distance=5)
        
        return {
            'metric': metric.value,
            'current_value': values[-1] if values else 0,
            'average_value': np.mean(values),
            'trend': 'improving' if slope > 0.01 else 'declining' if slope < -0.01 else 'stable',
            'slope': slope,
            'volatility': np.std(values),
            'moving_average': moving_avg.tolist() if len(moving_avg) > 0 else [],
            'peak_times': [timestamps[i].isoformat() for i in peaks[:5]],
            'valley_times': [timestamps[i].isoformat() for i in valleys[:5]],
            'consistency': 1 - (np.std(values) / max(np.mean(values), 0.01)),
            'prediction_accuracy': self._calculate_prediction_accuracy(metric)
        }
    
    def _calculate_prediction_accuracy(self, metric: PerformanceMetric) -> float:
        """Calculate prediction accuracy for a metric."""
        if len(self.prediction_history) < 10:
            return 0.0
        
        errors = []
        for prediction in self.prediction_history[-50:]:
            if prediction.metric == metric:
                actual = self._find_actual_performance(metric, prediction.prediction_time)
                if actual is not None:
                    error = abs(actual - prediction.predicted_value)
                    errors.append(error)
        
        if not errors:
            return 0.0
        
        mae = np.mean(errors)
        return max(0, 1 - mae)  # Convert to accuracy score
    
    async def retrain_models(self):
        """Retrain ML models with latest data."""
        if len(self.performance_history) < 50:
            logger.info("Insufficient data for retraining")
            return
        
        logger.info("Retraining performance prediction models")
        
        # Prepare data
        X = []
        y_dict = defaultdict(list)
        
        for record in self.performance_history[-1000:]:  # Use last 1000 records
            features = self._extract_features(record.timestamp, record.context)
            X.append(features)
            
            y_dict[PerformanceMetric.PRODUCTIVITY].append(record.productivity_score)
            y_dict[PerformanceMetric.FOCUS].append(record.focus_score)
            y_dict[PerformanceMetric.ACCURACY].append(record.accuracy_score)
            y_dict[PerformanceMetric.SPEED].append(record.speed_score)
            y_dict[PerformanceMetric.QUALITY].append(record.quality_score)
            y_dict[PerformanceMetric.CONSISTENCY].append(record.consistency_score)
        
        X = np.array(X)
        
        # Train model for each metric
        for metric, y in y_dict.items():
            if len(set(y)) < 10:  # Need variance
                continue
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            self.scalers[metric].fit(X_train)
            X_train_scaled = self.scalers[metric].transform(X_train)
            X_test_scaled = self.scalers[metric].transform(X_test)
            
            # Train model
            self.models[metric].fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.models[metric].predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Store feature importance
            if hasattr(self.models[metric], 'feature_importances_'):
                importance = self.models[metric].feature_importances_
                for i, col in enumerate(self.feature_columns):
                    if i < len(importance):
                        self.feature_importance[metric][col] = float(importance[i])
            
            logger.info(f"Model for {metric.value}: MAE={mae:.3f}, R2={r2:.3f}")
        
        self.samples_since_train = 0
        self.model_version = f"1.0.{len(self.performance_history) // 100}"
        
        # Save models
        await self._save_models()
    
    async def get_performance_insights(self) -> Dict[str, Any]:
        """Get comprehensive performance insights."""
        if len(self.performance_history) < 10:
            return {'message': 'Insufficient data for insights'}
        
        # Calculate baseline performance
        for metric in PerformanceMetric:
            values = []
            for record in self.performance_history[-100:]:  # Last 100 records
                if metric == PerformanceMetric.PRODUCTIVITY:
                    values.append(record.productivity_score)
                elif metric == PerformanceMetric.FOCUS:
                    values.append(record.focus_score)
                elif metric == PerformanceMetric.ACCURACY:
                    values.append(record.accuracy_score)
                elif metric == PerformanceMetric.SPEED:
                    values.append(record.speed_score)
                elif metric == PerformanceMetric.QUALITY:
                    values.append(record.quality_score)
                elif metric == PerformanceMetric.CONSISTENCY:
                    values.append(record.consistency_score)
            
            if values:
                self.baseline_performance[metric] = np.mean(values)
        
        # Analyze factors if not done recently
        if not self.performance_factors:
            await self.analyze_performance_factors()
        
        # Get top actionable factors
        actionable_factors = []
        for metric, factors in self.performance_factors.items():
            for factor in factors:
                if factor.actionable and factor.impact > 0.1:
                    actionable_factors.append({
                        'metric': metric.value,
                        'factor': factor.name,
                        'impact': factor.impact,
                        'category': factor.category
                    })
        
        # Sort by impact
        actionable_factors.sort(key=lambda x: x['impact'], reverse=True)
        
        # Predict next 24 hours
        tomorrow = datetime.now() + timedelta(days=1)
        next_day_predictions = await self.predict_performance(
            tomorrow,
            {'energy_level': 0.6, 'stress_level': 0.3}
        )
        
        return {
            'baseline_performance': {
                metric.value: score
                for metric, score in self.baseline_performance.items()
            },
            'top_actionable_factors': actionable_factors[:10],
            'next_day_predictions': {
                metric.value: {
                    'predicted': result.predicted_value,
                    'confidence': result.confidence_interval
                }
                for metric, result in next_day_predictions.items()
            },
            'model_accuracy': {
                metric.value: self._calculate_prediction_accuracy(metric)
                for metric in PerformanceMetric
            },
            'model_version': self.model_version,
            'total_predictions': len(self.prediction_history),
            'total_records': len(self.performance_history)
        }
    
    def _trim_history(self, max_entries: int = 10000):
        """Trim performance history to prevent unlimited growth."""
        if len(self.performance_history) > max_entries:
            self.performance_history = self.performance_history[-max_entries:]
        
        if len(self.prediction_history) > max_entries:
            self.prediction_history = self.prediction_history[-max_entries:]
    
    async def _save_data(self):
        """Save performance data to storage."""
        try:
            # Save performance history
            history_file = self.storage_path / "performance_history.json"
            with open(history_file, 'w') as f:
                json.dump([
                    {
                        'timestamp': p.timestamp.isoformat(),
                        'productivity_score': p.productivity_score,
                        'focus_score': p.focus_score,
                        'accuracy_score': p.accuracy_score,
                        'speed_score': p.speed_score,
                        'quality_score': p.quality_score,
                        'consistency_score': p.consistency_score,
                        'context': p.context,
                        'metadata': p.metadata
                    }
                    for p in self.performance_history[-1000:]  # Save last 1000
                ], f, indent=2, default=str)
            
            # Save performance factors
            factors_file = self.storage_path / "performance_factors.json"
            with open(factors_file, 'w') as f:
                json.dump({
                    metric.value: [
                        {
                            'name': factor.name,
                            'impact': factor.impact,
                            'confidence': factor.confidence,
                            'category': factor.category,
                            'actionable': factor.actionable
                        }
                        for factor in factors
                    ]
                    for metric, factors in self.performance_factors.items()
                }, f, indent=2)
            
            logger.debug("Performance data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving performance data: {e}")
    
    async def _save_models(self):
        """Save ML models to storage."""
        try:
            models_file = self.storage_path / "models.pkl"
            joblib.dump({
                'models': self.models,
                'scalers': self.scalers,
                'feature_importance': self.feature_importance,
                'version': self.model_version
            }, models_file)
            logger.debug("Models saved successfully")
        except Exception as e:
            logger.error(f"Error saving models: {e}")