"""
Flashcard API
=============

REST API endpoints for flashcard management.

Modules:
- flashcard_controller: Main API router with CRUD and review endpoints
"""

from .flashcard_controller import router

__all__ = ["router"]
