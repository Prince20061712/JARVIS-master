from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Feedback(BaseModel):
    comment: str
    constructive: bool = True

class EvaluationResult(BaseModel):
    score: float
    max_score: float
    is_correct: bool
    feedback: List[Feedback] = Field(default_factory=list)

class AnswerEvaluator:
    def evaluate(self, question: Any, answer: str) -> EvaluationResult:
        return EvaluationResult(score=0.0, max_score=1.0, is_correct=False)
