"""
API module for the Adaptive Flashcard & Viva System.
Provides REST endpoints for flashcard management and viva sessions.
"""

from .flashcard_controller import router as flashcard_router
from .viva_controller import router as viva_router

__all__ = ['flashcard_router', 'viva_router']
__version__ = '1.0.0'