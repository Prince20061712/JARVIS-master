from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class TimingStrategy(str, Enum):
    STRICT = 'strict'
    FLEXIBLE = 'flexible'

class TimeAllocation(BaseModel):
    question_id: str
    allocated_seconds: int

class TimeManager:
    def allocate_time(self, questions: List[Any]) -> List[int]:
        return []
