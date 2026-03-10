"""
Concept Explainer Module
=======================

Break down and explain concepts with multiple learning modalities.

Classes:
- AnalogyGenerator: Generate helpful analogies for concepts
- PrerequisiteCheck: Check and identify missing prerequisites
- StepByStepExplainer: Create step-by-step explanations
- Visualization: Generate visualizations for concepts
"""

from .analogy_generator import AnalogyGenerator, Analogy, AnalogyType
from .prerequisite_check import PrerequisiteCheck, PrerequisiteGap, LearningPath
from .step_by_step import StepByStepExplainer, ExplanationStep, Difficulty
from .visualization import Visualization, VisualAsset, VisualizationType

__all__ = [
    "AnalogyGenerator",
    "Analogy",
    "AnalogyType",
    "PrerequisiteCheck",
    "PrerequisiteGap",
    "LearningPath",
    "StepByStepExplainer",
    "ExplanationStep",
    "Difficulty",
    "Visualization",
    "VisualAsset",
    "VisualizationType",
]
