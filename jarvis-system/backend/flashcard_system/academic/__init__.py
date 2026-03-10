"""
Academic Intelligence System
=============================

Integrated academic tools for concept explanation, response formatting, and exam simulation.

Submodules:
- response_formatter: Format and evaluate academic responses
- concept_explainer: Break down and explain concepts
- exam_simulator: Create and manage simulated exams
"""

from .response_formatter import (
    CodeFormatter,
    DiagramGenerator,
    DerivationBuilder,
    MarksAllocator,
    NumericalSolver,
)
from .concept_explainer import (
    AnalogyGenerator,
    PrerequisiteCheck,
    StepByStepExplainer,
    Visualization,
)
from .exam_simulator import (
    AnswerEvaluator,
    QuestionGenerator,
    TimeManager,
)

__all__ = [
    # Response Formatter
    "CodeFormatter",
    "DiagramGenerator",
    "DerivationBuilder",
    "MarksAllocator",
    "NumericalSolver",
    # Concept Explainer
    "AnalogyGenerator",
    "PrerequisiteCheck",
    "StepByStepExplainer",
    "Visualization",
    # Exam Simulator
    "AnswerEvaluator",
    "QuestionGenerator",
    "TimeManager",
]
