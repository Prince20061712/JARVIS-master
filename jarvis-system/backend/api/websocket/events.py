from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel
import json

class EventType(str, Enum):
    NEW_QUERY = "new_query"
    EMOTION_UPDATE = "emotion_update"
    PROACTIVE_SUGGESTION = "suggestion"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    LIPSYNC_START = "lipsync_start"

class WSEvent(BaseModel):
    type: EventType
    data: Dict[str, Any]
    timestamp: Optional[float] = None

    def to_json(self) -> str:
        return json.dumps(self.dict())

    @classmethod
    def from_json(cls, json_str: str) -> "WSEvent":
        data = json.loads(json_str)
        return cls(**data)
