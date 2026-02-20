from typing import List, Dict, Any
import random
from utils.logger import logger

class EngagementMode:
    """
    Challenges and deepens the learning for curious or high-performing students.
    """
    def __init__(self):
        self.curiosity_sparks = [
            "That's a great question! Did you know this also relates to {topic}?",
            "Since you understood that so quickly, want to see how it's applied in real-world {field}?",
            "Ready for a challenge? See if you can apply this to the next level of complexity."
        ]

    def generate_challenge(self, topic: str) -> str:
        return f"🚀 **Challenge Mode!** Given what we just discussed about {topic}, how do you think it would change if the boundary conditions were doubled?"

    def spark_curiosity(self, related_topic: str) -> str:
        return f"If you liked this, you might find **{related_topic}** fascinating! It's the next logical step in your learning path."

    def suggest_next_topics(self, mastered_topics: List[str]) -> List[str]:
        # Logic to look at curriculum graph and suggest next steps
        return ["Advanced " + t for t in mastered_topics]
