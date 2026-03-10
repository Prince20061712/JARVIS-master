"""
Core Flashcard System
====================

Core components for flashcard generation and spaced repetition scheduling.

Modules:
- generator: FlashcardGenerator and card models
- spaced_repetition: SM-2 algorithm and scheduling
"""

from .generator import (
    FlashcardGenerator,
    Flashcard,
    FlashcardSet,
    TextProcessor,
    DifficultyLevel,
    GenerationQuality,
    CardType,
    GenerationOptions,
)
from .spaced_repetition import (
    SpacedRepetition,
    CardProgress,
    ReviewLog,
    ReviewQuality,
    SM2Parameters,
    SchedulingInfo,
)

__all__ = [
    "FlashcardGenerator",
    "Flashcard",
    "FlashcardSet",
    "TextProcessor",
    "SpacedRepetition",
    "CardProgress",
    "ReviewLog",
    "ReviewQuality",
    "SM2Parameters",
    "SchedulingInfo",
    "DifficultyLevel",
    "GenerationQuality",
    "CardType",
    "GenerationOptions",
]
