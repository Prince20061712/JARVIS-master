from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class QuestionDifficulty(str, Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'

class Question(BaseModel):
    id: str
    content: str
    type: str
    difficulty: QuestionDifficulty
    expected_answer: Optional[str] = None

class QuestionGenerator:
    def generate_questions(self, subject: str, count: int = 10, difficulty: str = "HARD") -> List[Question]:
        return []
