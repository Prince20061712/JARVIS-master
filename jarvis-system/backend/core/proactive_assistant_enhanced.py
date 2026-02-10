#!/usr/bin/env python3
"""
Enhanced Proactive Assistant Wrapper
Re-exports AdvancedProactiveAssistant with a public save_learning_data() alias for ai_brain.py.
The brain calls save_learning_data() but the base class only has _save_learned_data() (private).
"""

from .proactive_assistant import AdvancedProactiveAssistant as _BaseProactiveAssistant


class AdvancedProactiveAssistant(_BaseProactiveAssistant):
    """Extended AdvancedProactiveAssistant with method aliases for ai_brain.py compatibility."""

    def save_learning_data(self):
        """Public alias for _save_learned_data() — called by FullFledgedAIBrain.save_state()."""
        return self._save_learned_data()


__all__ = ["AdvancedProactiveAssistant"]
