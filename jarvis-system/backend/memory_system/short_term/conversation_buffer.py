import collections
from datetime import datetime
from typing import List, Dict, Any
from utils.logger import logger

class ConversationBuffer:
    """
    Short-term memory to keep track of recent messages for context.
    Size-limited queue dropping the oldest messages.
    """
    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self.buffer = collections.deque(maxlen=max_size)

    def add_message(self, role: str, content: str, emotion: str = "neutral", msg_type: str = "text"):
        """Adds a message to the buffer."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "emotion": emotion,
            "type": msg_type
        }
        self.buffer.append(message)
        logger.debug(f"Added message to buffer. Buffer size: {len(self.buffer)}")

    def get_recent(self, count: int = 10) -> List[Dict[str, Any]]:
        """Retrieves the most recent N messages."""
        return list(self.buffer)[-count:]

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieves all messages currently in the buffer."""
        return list(self.buffer)

    def clear_old(self):
        """Clears the buffer manually if a complete context reset is needed."""
        self.buffer.clear()
        logger.info("Conversation buffer cleared.")

    def format_for_llm(self, count: int = 10) -> List[Dict[str, str]]:
        """Formats the most recent messages for direct insertion into an LLM prompt array."""
        messages = self.get_recent(count)
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]

    def serialize(self) -> List[Dict[str, Any]]:
        return list(self.buffer)

    def load_from_serialized(self, data: List[Dict[str, Any]]):
        self.buffer.clear()
        for item in data[-self.max_size:]:
            self.buffer.append(item)
