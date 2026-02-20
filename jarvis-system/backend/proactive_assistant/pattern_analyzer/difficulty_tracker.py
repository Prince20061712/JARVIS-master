import numpy as np
from typing import Dict, List, Any
from utils.logger import logger

class DifficultyTracker:
    """
    Dynamically tracks topic difficulty based on user performance using Bayesian-like updates.
    """
    def __init__(self):
        self.topic_params = {} # {topic: {'success': int, 'total': int}}
        
    def update_difficulty(self, topic: str, succeeded: bool):
        """Update success/total counts for a topic to estimate difficulty."""
        if topic not in self.topic_params:
            self.topic_params[topic] = {'success': 1, 'total': 2} # Prior: 50%
            
        self.topic_params[topic]['total'] += 1
        if succeeded:
            self.topic_params[topic]['success'] += 1
            
        logger.debug(f"Difficulty updated for {topic}: {self.get_difficulty(topic):.2f}")

    def get_difficulty(self, topic: str) -> float:
        """
        Returns estimated difficulty (1.0 - success_rate).
        High value = Difficult.
        """
        params = self.topic_params.get(topic, {'success': 1, 'total': 2})
        success_rate = params['success'] / params['total']
        return 1.0 - success_rate

    def identify_challenging(self, threshold: float = 0.6) -> List[str]:
        """Returns list of topics exceeding difficulty threshold."""
        return [t for t in self.topic_params if self.get_difficulty(t) > threshold]

    def get_difficulty_curve(self, topic: str) -> List[float]:
        """Placeholder for historical difficulty trend."""
        # In a full implementation, we'd store a history of success rates
        return [self.get_difficulty(topic)]
