import time
from typing import Dict, Any, Optional

class ContextWindow:
    """
    Manages the current operational state of the active study session.
    Tracks what the user is currently focusing on.
    """
    def __init__(self, expiry_minutes: int = 30):
        self.expiry_seconds = expiry_minutes * 60
        self.current_topic: Optional[str] = None
        self.active_subject: Optional[str] = None
        self.user_goal: Optional[str] = None
        self.last_updated: float = time.time()
        self.attention_flags: Dict[str, Any] = {}

    def update_context(self, subject: str = None, topic: str = None, goal: str = None, attention_flag: dict = None):
        """Updates the active session context."""
        if subject: self.active_subject = subject
        if topic: self.current_topic = topic
        if goal: self.user_goal = goal
        if attention_flag:
            self.attention_flags.update(attention_flag)
            
        self.last_updated = time.time()

    def is_expired(self) -> bool:
        """Checks if the context is still relevant based on time elapsed."""
        return (time.time() - self.last_updated) > self.expiry_seconds

    def get_context(self) -> Dict[str, Any]:
        """Returns the active context, purging it if it has mathematically expired."""
        if self.is_expired():
            self._reset_context()

        return {
            "active_subject": self.active_subject,
            "current_topic": self.current_topic,
            "user_goal": self.user_goal,
            "attention_flags": self.attention_flags,
            "is_active": self.active_subject is not None
        }

    def merge_contexts(self, other_context: 'ContextWindow'):
        """Merges another context into this one (e.g. restoring previous session context)."""
        self.update_context(
            subject=other_context.active_subject,
            topic=other_context.current_topic,
            goal=other_context.user_goal,
            attention_flag=other_context.attention_flags
        )

    def _reset_context(self):
        """Clears out the active topic/focus due to expiry."""
        self.current_topic = None
        self.active_subject = None
        self.user_goal = None
        self.attention_flags.clear()
        self.last_updated = time.time()
