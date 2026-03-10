"""
Response Formatter Module
========================

Format academic responses with proper structure, derivations, and evaluation.

Classes:
- CodeFormatter: Format code snippets with syntax highlighting
- DiagramGenerator: Generate ASCII/visual diagrams for explanations
- DerivationBuilder: Build step-by-step mathematical derivations
- MarksAllocator: Allocate marks based on answer quality
- NumericalSolver: Solve numerical problems step-by-step
"""

from .code_formatter import CodeFormatter, CodeBlock, CodeAnalysis
from .diagram_generator import DiagramGenerator, Diagram, DiagramType
from .derivation_builder import DerivationBuilder, DerivationStep
from .marks_allocator import MarksAllocator, MarksCriteria, AnswerQuality
from .numerical_solver import NumericalSolver, Solution, SolutionStep

__all__ = [
    "CodeFormatter",
    "CodeBlock",
    "CodeAnalysis",
    "DiagramGenerator",
    "Diagram",
    "DiagramType",
    "DerivationBuilder",
    "DerivationStep",
    "MarksAllocator",
    "MarksCriteria",
    "AnswerQuality",
    "NumericalSolver",
    "Solution",
    "SolutionStep",
]
