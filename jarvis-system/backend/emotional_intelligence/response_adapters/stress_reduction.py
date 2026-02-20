from typing import List, Dict, Any
import random
from utils.logger import logger

class StressReduction:
    """
    Techniques to lower student stress levels through language and activity suggestions.
    """
    def __init__(self):
        self.calming_phrases = [
            "Let's take a quick 10-second breather before we dive back in.",
            "Engineering can be intense, but you're handling it well. Just one step at a time.",
            "If you're feeling overwhelmed, that's okay. Let's look at the simplest part first."
        ]

    def calm_response(self, response: str) -> str:
        """Prepends a calming prompt to the response."""
        return f"🌿 {random.choice(self.calming_phrases)}\n\n{response}"

    def suggest_break(self, stress_duration_minutes: int) -> Optional[str]:
        """Suggests a physical/mental break if stress persists."""
        if stress_duration_minutes > 15:
            return "⚠️ **Time for a short break.** You've been working hard for a while. Go grab some water or stretch for 5 minutes. I'll be right here when you're back."
        return None

    def mindfulness_prompt(self) -> str:
        return "Quick tip: Try the 4-7-8 breathing technique if this topic feels like a lot. It really helps clear the mind!"
