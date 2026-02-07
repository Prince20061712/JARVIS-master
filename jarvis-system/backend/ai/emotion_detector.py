from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

logger = logging.getLogger("EmotionDetector")

@dataclass
class EmotionData:
    primary_emotion: str 
    confidence: float
    sentiment_score: float # -1.0 to 1.0

class EmotionDetector:
    def __init__(self):
        # In a real scenario, load a transformer model here (e.g., 'bhadresh-savani/distilbert-base-uncased-emotion')
        # For prototype speed, using TextBlob sentiment + keyword mapping
        pass

    def detect(self, text: str) -> EmotionData:
        """
        Detects emotion from text.
        """
        if not text:
            return EmotionData("neutral", 1.0, 0.0)

        sentiment = 0.0
        if TextBlob:
            blob = TextBlob(text)
            sentiment = blob.sentiment.polarity

        # Simple heuristic mapping based on sentiment and keywords
        # This is a placeholder for a real ML model
        text_lower = text.lower()
        
        if "sad" in text_lower or "unhappy" in text_lower or "depressed" in text_lower:
            return EmotionData("sad", 0.8, sentiment)
        elif "happy" in text_lower or "great" in text_lower or "joy" in text_lower:
            return EmotionData("happy", 0.8, sentiment)
        elif "angry" in text_lower or "mad" in text_lower or "hates" in text_lower:
            return EmotionData("angry", 0.8, sentiment)
        elif "fear" in text_lower or "scared" in text_lower or "afraid" in text_lower:
            return EmotionData("fear", 0.8, sentiment)
            
        # Fallback to sentiment
        if sentiment > 0.5:
            return EmotionData("happy", 0.6, sentiment)
        elif sentiment < -0.5:
            return EmotionData("sad", 0.6, sentiment)
        
        return EmotionData("neutral", 0.5, sentiment)
