#!/usr/bin/env python3
"""
Enhanced Decision Engine Wrapper
Re-exports DecisionEngine as EnhancedDecisionEngine for ai_brain.py
"""

from .decision_engine import DecisionEngine as EnhancedDecisionEngine

__all__ = ["EnhancedDecisionEngine"]
