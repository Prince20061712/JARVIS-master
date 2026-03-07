"""
Flashcards module for the Adaptive Flashcard System.
Provides flashcard generation, management, and spaced repetition algorithms.
"""

from .generator import (
    FlashcardGenerator,
    Flashcard,
    FlashcardSet,
    GenerationOptions,
    GenerationQuality,
    DifficultyLevel
)
from .spaced_repetition import (
    SpacedRepetition,
    ReviewLog,
    CardProgress,
    SM2Parameters,
    ReviewQuality,
    SchedulingInfo
)

__all__ = [
    'FlashcardGenerator',
    'Flashcard',
    'FlashcardSet',
    'GenerationOptions',
    'GenerationQuality',
    'DifficultyLevel',
    'SpacedRepetition',
    'ReviewLog',
    'CardProgress',
    'SM2Parameters',
    'ReviewQuality',
    'SchedulingInfo'
]

__version__ = '1.0.0'