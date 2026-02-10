from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import logging
from ..core.emotional_intelligence import EmotionalIntelligence, EmotionalState

logger = logging.getLogger("EmotionDetector")

@dataclass
class EmotionData:
    primary_emotion: str 
    confidence: float
    sentiment_score: float # -1.0 to 1.0
    details: Dict[str, Any] = field(default_factory=dict)

class EmotionDetector:
    def __init__(self):
        self.engine = EmotionalIntelligence()

    def detect(self, text: str) -> EmotionData:
        """
        Detects emotion using the advanced EmotionalIntelligence engine.
        """
        if not text:
            return EmotionData("neutral", 1.0, 0.0)

        # Use the advanced human-like detection
        analysis = self.engine.detect_emotion_humanlike(text)
        
        primary_emotion = analysis.get("primary_emotion", "neutral")
        if hasattr(primary_emotion, "value"):
            primary_emotion = primary_emotion.value
            
        confidence = analysis.get("confidence", 0.0)
        
        # Extract sentiment from the linguistic analysis if available
        sentiment = 0.0
        if "linguistic_analysis" in analysis and "sentiment" in analysis["linguistic_analysis"]:
            sentiment = analysis["linguistic_analysis"]["sentiment"].get("polarity", 0.0)

        return EmotionData(primary_emotion, confidence, sentiment, details=analysis)
