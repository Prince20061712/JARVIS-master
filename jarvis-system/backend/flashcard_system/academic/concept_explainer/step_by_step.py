from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Difficulty(str, Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'

class ExplanationStep(BaseModel):
    number: int
    content: str
    hints: List[str] = Field(default_factory=list)

class StepByStepExplainer:
    def explain(self, concept: str, depth: int = 5) -> List[ExplanationStep]:
        return []
