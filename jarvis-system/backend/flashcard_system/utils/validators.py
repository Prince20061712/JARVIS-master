"""Pydantic validators for data validation."""

from pydantic import BaseModel, field_validator, ValidationInfo
from typing import Optional, List
import re
import logging

logger = logging.getLogger(__name__)


class CardValidator(BaseModel):
    """Validator for flashcard data."""
    
    front: str
    back: str
    subject: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    
    @field_validator('front')
    @classmethod
    def validate_front(cls, v: str) -> str:
        """Validate front side of card."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Front side cannot be empty")
        if len(v) > 5000:
            raise ValueError("Front side too long (max 5000 chars)")
        return v.strip()
    
    @field_validator('back')
    @classmethod
    def validate_back(cls, v: str) -> str:
        """Validate back side of card."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Back side cannot be empty")
        if len(v) > 10000:
            raise ValueError("Back side too long (max 10000 chars)")
        return v.strip()
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags list."""
        if v is None:
            return None
        if len(v) > 10:
            raise ValueError("Too many tags (max 10)")
        return [tag.strip().lower() for tag in v if tag.strip()]


class ReviewValidator(BaseModel):
    """Validator for review data."""
    
    card_id: int
    quality: int  # 0-5 rating
    ease_factor: Optional[float] = None
    interval: Optional[int] = None
    
    @field_validator('quality')
    @classmethod
    def validate_quality(cls, v: int) -> int:
        """Validate quality rating."""
        if not 0 <= v <= 5:
            raise ValueError("Quality must be between 0 and 5")
        return v
    
    @field_validator('ease_factor')
    @classmethod
    def validate_ease_factor(cls, v: Optional[float]) -> Optional[float]:
        """Validate ease factor."""
        if v is not None and not (1.3 <= v <= 2.5):
            raise ValueError("Ease factor must be between 1.3 and 2.5")
        return v
    
    @field_validator('interval')
    @classmethod
    def validate_interval(cls, v: Optional[int]) -> Optional[int]:
        """Validate interval."""
        if v is not None and v < 0:
            raise ValueError("Interval cannot be negative")
        return v
