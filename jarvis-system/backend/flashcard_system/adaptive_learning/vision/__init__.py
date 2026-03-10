"""
Vision module for the Adaptive Flashcard & Viva System.
Provides hand drawing recognition, diagram analysis, and OCR capabilities.
"""

from .hand_drawing import (
    HandDrawingRecognizer,
    DrawingAnalysis,
    ShapeType,
    DiagramElement,
    Diagram,
    OCRResult,
    RecognitionOptions,
    DrawingSession,
    Sketch
)

__all__ = [
    'HandDrawingRecognizer',
    'DrawingAnalysis',
    'ShapeType',
    'DiagramElement',
    'Diagram',
    'OCRResult',
    'RecognitionOptions',
    'DrawingSession',
    'Sketch'
]

__version__ = '1.0.0'