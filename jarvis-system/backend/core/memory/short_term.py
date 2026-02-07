from typing import List, Dict
from sqlalchemy import desc
from core.memory.db import get_db
from core.memory.models import Conversation

class ShortTermMemory:
    def __init__(self):
        pass

    def get_recent_messages(self, limit: int = 10) -> List[Dict]:
        """
        Retrieves the last N messages for immediate context.
        """
        db = next(get_db())
        try:
            records = db.query(Conversation).order_by(desc(Conversation.timestamp)).limit(limit).all()
            # Reverse to chronological order
            history = []
            for r in reversed(records):
                history.append({
                    "role": r.role,
                    "content": r.content
                })
            return history
        finally:
            db.close()

    def get_context_string(self, limit: int = 10) -> str:
        messages = self.get_recent_messages(limit)
        return "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in messages])
