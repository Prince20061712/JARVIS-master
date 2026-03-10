from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class AnalogyType(str, Enum):
    REAL_WORLD = 'real_world'
    TECHNICAL = 'technical'
    VISUAL = 'visual'

class Analogy(BaseModel):
    type: AnalogyType
    source: str
    target: str
    explanation: str
    mapping: Dict[str, str] = Field(default_factory=dict)

class AnalogyGenerator:
    def generate_analogy(self, concept: str) -> Analogy:
        return Analogy(type=AnalogyType.REAL_WORLD, source="A", target="B", explanation="A is like B")
