"""
Exam Simulator Module
====================

Simulate exams with question generation, answer evaluation, and time management.

Classes:
- AnswerEvaluator: Evaluate student answers with detailed feedback
- QuestionGenerator: Generate exam questions intelligently
- TimeManager: Manage exam time and question allocation
"""

from .answer_evaluator import AnswerEvaluator, EvaluationResult, Feedback
from .question_generator import QuestionGenerator, Question, QuestionDifficulty
from .time_manager import TimeManager, TimeAllocation, TimingStrategy

__all__ = [
    "AnswerEvaluator",
    "EvaluationResult",
    "Feedback",
    "QuestionGenerator",
    "Question",
    "QuestionDifficulty",
    "TimeManager",
    "TimeAllocation",
    "TimingStrategy",
]
