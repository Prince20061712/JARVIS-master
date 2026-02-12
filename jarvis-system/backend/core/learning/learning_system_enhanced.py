#!/usr/bin/env python3
"""
Enhanced Learning System Wrapper
Re-exports EnhancedLearningSystem with a save_learning() alias for ai_brain.py
The brain calls save_learning() but the base class has save_learning_data().
"""

from .learning_system import EnhancedLearningSystem as _BaseLearningSystem


class EnhancedLearningSystem(_BaseLearningSystem):
    """Extended EnhancedLearningSystem with method aliases for ai_brain.py compatibility."""

    def save_learning(self):
        """Alias for save_learning_data() — called by FullFledgedAIBrain.save_state()."""
        return self.save_learning_data()


__all__ = ["EnhancedLearningSystem"]
