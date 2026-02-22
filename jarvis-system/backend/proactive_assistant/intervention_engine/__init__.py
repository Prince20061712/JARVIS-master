"""
Intervention Engine Module for JARVIS Proactive Assistant.
Handles feedback collection, suggestion generation, and timing optimization.
"""

from .feedback_collector import FeedbackCollector
from .suggestion_generator import SuggestionGenerator
from .timing_optimizer import TimingOptimizer

__all__ = [
    'FeedbackCollector',
    'SuggestionGenerator',
    'TimingOptimizer'
]

__version__ = '1.0.0'