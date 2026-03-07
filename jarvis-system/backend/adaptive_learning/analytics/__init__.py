"""
Analytics module for the Adaptive Flashcard & Viva System.
Provides learning pattern analysis, retention curve calculations, and performance metrics.
"""

from .learning_patterns import (
    LearningPatterns,
    RetentionCurve,
    PerformanceMetrics,
    WeaknessAnalysis,
    StudySessionMetrics
)
from .api_routes import router as analytics_router

__all__ = [
    'LearningPatterns',
    'RetentionCurve',
    'PerformanceMetrics',
    'WeaknessAnalysis',
    'StudySessionMetrics',
    'analytics_router'
]

__version__ = '1.0.0'