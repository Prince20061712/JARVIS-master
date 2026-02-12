#!/usr/bin/env python3
"""
Enhanced Context Awareness Wrapper
Re-exports HumanLikeContextAwareness as EnhancedContextAwareness for ai_brain.py
"""

from .context_awareness import HumanLikeContextAwareness as EnhancedContextAwareness

__all__ = ["EnhancedContextAwareness"]
