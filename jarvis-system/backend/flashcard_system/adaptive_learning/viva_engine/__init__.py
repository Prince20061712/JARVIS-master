"""
Viva Engine module for the Adaptive Flashcard & Viva System.
Provides adaptive oral examination capabilities with emotional intelligence.
"""

from .viva_session import (
    VivaSession,
    VivaMode,
    VivaState,
    Question,
    Answer,
    Feedback,
    SessionConfig,
    QuestionRecord
)
from .adaptive_questioner import (
    AdaptiveQuestioner,
    QuestionDifficulty,
    QuestionType,
    QuestionBank,
    QuestionTemplate,
    EmotionalState,
    AdaptationStrategy
)

__all__ = [
    'VivaSession',
    'VivaMode',
    'VivaState',
    'Question',
    'Answer',
    'Feedback',
    'SessionConfig',
    'QuestionRecord',
    'AdaptiveQuestioner',
    'QuestionDifficulty',
    'QuestionType',
    'QuestionBank',
    'QuestionTemplate',
    'EmotionalState',
    'AdaptationStrategy'
]

__version__ = '1.0.0'