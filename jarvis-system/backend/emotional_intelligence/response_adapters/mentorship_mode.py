import random
from typing import List, Dict, Any
from utils.logger import logger

class MentorshipMode:
    """
    Adapts AI responses for struggling students with empathy, simplifications,
    and encouragement.
    """
    def __init__(self):
        self.encouragements = [
            "You're making great progress! Let's break this down even further.",
            "It's completely normal to find this concept tricky. You'll get there!",
            "Take a deep breath. We'll solve this step-by-step together.",
            "Don't worry about being stuck. Every engineering expert was once where you are."
        ]
        
    def adapt_response(self, raw_academic_response: str, query: str = "") -> str:
        """Wraps academic content with encouraging mentorship framing."""
        opening = random.choice(self.encouragements)
        
        # Breakdown long theoretical blocks into bullet points if they aren't already
        paragraphs = raw_academic_response.split('\n\n')
        simplified_paragraphs = []
        for p in paragraphs:
            if len(p) > 300: # If too long, maybe it's too dense
                simplified_paragraphs.append(f"💡 *Key Point:* {p[:250]}... (Breaking it down further)")
            else:
                simplified_paragraphs.append(p)
                
        body = "\n\n".join(simplified_paragraphs)
        
        adapted = f"💙 **Mentorship Mode Active**\n\n"
        adapted += f"{opening}\n\n"
        adapted += f"{body}\n\n"
        adapted += "*Shall we try a small practice problem to check your understanding?*"
        
        return adapted

    def check_understanding(self) -> str:
        """Generates a soft 'concept check' question."""
        return "Before we move on, could you explain the main idea in your own words?"
