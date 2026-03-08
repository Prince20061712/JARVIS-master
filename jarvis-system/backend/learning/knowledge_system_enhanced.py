#!/usr/bin/env python3
"""
Enhanced Knowledge System Wrapper
Re-exports EnhancedKnowledgeSystem for ai_brain.py
"""

try:
    from .knowledge_system import EnhancedKnowledgeSystem
except ImportError:
    from knowledge_system import EnhancedKnowledgeSystem

__all__ = ["EnhancedKnowledgeSystem"]
