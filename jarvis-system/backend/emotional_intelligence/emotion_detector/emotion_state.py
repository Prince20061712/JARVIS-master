import time
from typing import Dict, Any, List
from utils.logger import logger

class EmotionState:
    """
    Tracks the persistent emotional state of the student over a session.
    Implements emotion decay (intensity decreases over time without new input).
    """
    def __init__(self, decay_rate: float = 0.1):
        self.current_emotion = "neutral"
        self.intensity = 0.0
        self.last_updated = time.time()
        self.decay_rate = decay_rate # Intensity lost per minute
        self.history: List[Dict[str, Any]] = []

    def update_state(self, new_emotion: str, new_intensity: float, context: str = ""):
        """Updates state and logs to history."""
        self._apply_decay()
        
        # If the same emotion persists, intensity might accumulate/reinforce
        if new_emotion == self.current_emotion:
            self.intensity = min(1.0, self.intensity + (new_intensity * 0.5))
        else:
            # Different emotion overrides, but starting intensity is averaged if old intensity was high
            self.intensity = (self.intensity * 0.3) + (new_intensity * 0.7)
            self.current_emotion = new_emotion
            
        self.last_updated = time.time()
        
        self.history.append({
            "emotion": self.current_emotion,
            "intensity": self.intensity,
            "timestamp": self.last_updated,
            "context": context
        })
        logger.debug(f"Emotion state updated: {self.current_emotion} ({self.intensity:.2f})")

    def _apply_decay(self):
        """Reduces intensity based on time passed since last update."""
        elapsed_minutes = (time.time() - self.last_updated) / 60.0
        reduction = elapsed_minutes * self.decay_rate
        self.intensity = max(0.0, self.intensity - reduction)
        if self.intensity == 0.0:
            self.current_emotion = "neutral"

    def get_state(self) -> Dict[str, Any]:
        self._apply_decay()
        return {
            "current_emotion": self.current_emotion,
            "intensity": round(self.intensity, 2),
            "is_stable": self.intensity < 0.3
        }

    def detect_changes(self) -> bool:
        """Checks if the recent history shows a significant shift in emotion."""
        if len(self.history) < 2: return False
        prev = self.history[-2]["emotion"]
        curr = self.history[-1]["emotion"]
        return prev != curr
