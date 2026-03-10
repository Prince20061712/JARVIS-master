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
from .ocr_processor import OCRProcessor
from .diagram_detector import DiagramAnalyzer

__all__ = [
    'HandDrawingRecognizer',
    'DrawingAnalysis',
    'ShapeType',
    'DiagramElement',
    'Diagram',
    'OCRResult',
    'RecognitionOptions',
    'DrawingSession',
    'Sketch',
    'OCRProcessor',
    'DiagramAnalyzer'
]

__version__ = '3.0.0'