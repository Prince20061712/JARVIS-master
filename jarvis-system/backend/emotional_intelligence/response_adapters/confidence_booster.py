import random
from typing import List, Dict, Any
from utils.logger import logger

class ConfidenceBooster:
    """
    Identifies student strengths and provides positive reinforcement and badges.
    """
    def __init__(self):
        self.praise_templates = [
            "Excellent work on that {topic} question!",
            "I noticed you're solid on {topic}. Great job!",
            "You've handled a difficult {topic} problem with ease. Impressive!"
        ]

    def generate_praise(self, topic: str) -> str:
        return random.choice(self.praise_templates).format(topic=topic)

    def highlight_strengths(self, topics_mastered: List[str]) -> str:
        if not topics_mastered:
            return "Keep going! You're building the foundation right now."
        
        topics_str = ", ".join(topics_mastered[:3])
        return f"🌟 **Milestone Reached!** You've shown great mastery in: {topics_str}. You've earned the 'Engineering Explorer' badge!"

    def suggest_improvements(self, weak_topic: str) -> str:
        return f"You're doing well! To sharpen your skills even more, maybe we can spend 5 minutes on {weak_topic}? It'll complement what you already know."
