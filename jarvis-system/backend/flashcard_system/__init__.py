"""
Flashcard & Academic Intelligence System v3.0
==============================================

A robust, production-ready system integrating:
- Card generation (from text/documents)
- Spaced repetition scheduling (SM-2 algorithm)
- Learning analytics and progress tracking
- Adaptive viva exam sessions
- Material scanning and processing
- Smart response formatting
- Concept explanation & visualization
- Exam simulation & evaluation
- Handwriting recognition (OCR) & diagram detection
- Real-time WebSocket communication
- Configuration management
- Storage & caching layer
- Utility functions and validators

Architecture (v3.0):
- core: Card generation and spaced repetition
- api: REST API endpoints
- academic: Concept explanation, exam simulation, response formatting
  - response_formatter: Code, diagrams, derivations, marks
  - concept_explainer: Analogies, prerequisites, step-by-step, visualization
  - exam_simulator: Question generation, answer evaluation, time management
- vision: Handwriting recognition, OCR, diagram detection
- viva: Exam session management
- websocket: Real-time communication infrastructure
- analytics: Learning patterns and statistics
- config: Application configuration management
- storage: Data persistence layer (repository, caching)
- utils: Helper functions, validators, constants
"""

# Version
__version__ = "3.0.0"

# ===== Core Components =====
from flashcard_system.core.generator import FlashcardGenerator, Flashcard, FlashcardSet
from flashcard_system.core.spaced_repetition import SpacedRepetition, CardProgress

# ===== Configuration =====
from flashcard_system.config import Settings, setup_logging

# ===== Storage & Persistence =====
from flashcard_system.storage import Repository, CacheManager

# ===== Utilities =====
from flashcard_system.utils import (
    CardValidator,
    ReviewValidator,
    generate_id,
    format_datetime,
    calculate_interval,
    SM2_CONSTANTS,
    STUDY_CONSTANTS,
    API_CONSTANTS,
    CARD_STATUSES,
    REVIEW_TYPES,
)

# ===== Academic Intelligence =====
from flashcard_system.academic import (
    CodeFormatter,
    DiagramGenerator,
    DerivationBuilder,
    MarksAllocator,
    NumericalSolver,
    AnalogyGenerator,
    PrerequisiteCheck,
    StepByStepExplainer,
    Visualization,
    AnswerEvaluator,
    QuestionGenerator,
    TimeManager,
)

# ===== Vision & OCR =====
from flashcard_system.vision import (
    HandDrawingRecognizer,
    OCRProcessor,
    DiagramAnalyzer,
)

# ===== Viva Sessions =====
from flashcard_system.viva import VivaSession

# ===== WebSocket Communication =====
from flashcard_system.websocket import (
    WSEvent,
    EventType,
    ConnectionManager,
)

# ===== Analytics =====
from flashcard_system.analytics import LearningPatterns


__all__ = [
    # Version
    "__version__",
    
    # Core
    "FlashcardGenerator",
    "Flashcard",
    "FlashcardSet",
    "SpacedRepetition",
    "CardProgress",
    
    # Configuration
    "Settings",
    "setup_logging",
    
    # Storage
    "Repository",
    "CacheManager",
    
    # Utilities
    "CardValidator",
    "ReviewValidator",
    "generate_id",
    "format_datetime",
    "calculate_interval",
    "SM2_CONSTANTS",
    "STUDY_CONSTANTS",
    "API_CONSTANTS",
    "CARD_STATUSES",
    "REVIEW_TYPES",
    
    # Academic Intelligence
    "CodeFormatter",
    "DiagramGenerator",
    "DerivationBuilder",
    "MarksAllocator",
    "NumericalSolver",
    "AnalogyGenerator",
    "PrerequisiteCheck",
    "StepByStepExplainer",
    "Visualization",
    "AnswerEvaluator",
    "QuestionGenerator",
    "TimeManager",
    
    # Vision
    "HandDrawingRecognizer",
    "OCRProcessor",
    "DiagramAnalyzer",
    
    # Viva
    "VivaSession",
    
    # WebSocket
    "WSEvent",
    "EventType",
    "ConnectionManager",
    
    # Analytics
    "LearningPatterns",
]

