import torch
from typing import Dict, Any, List
from utils.logger import logger

try:
    from transformers import pipeline
except ImportError:
    pipeline = None
    logger.warning("Transformers not installed. TextSentimentAnalyzer will use fallback.")

class TextSentimentAnalyzer:
    """
    Analyzes user query sentiment using Transformer models (DistilBERT/RoBERTa).
    Detects frustration, confusion, and confidence levels.
    """
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        self.device = 0 if torch.cuda.is_available() else -1
        self._classifier = None
        self.model_name = model_name

    def _load_model(self):
        if self._classifier is None and pipeline:
            try:
                logger.info(f"Loading sentiment model: {self.model_name}")
                self._classifier = pipeline("sentiment-analysis", model=self.model_name, device=self.device)
            except Exception as e:
                logger.error(f"Failed to load transformer model: {e}")

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Returns deep sentiment metrics from user input."""
        self._load_model()
        
        if self._classifier:
            results = self._classifier(text)
            top_result = results[0]
            label = top_result['label'].lower()
            score = top_result['score']
            
            # Additional heuristic check for "engineering frustration"
            frustration_keywords = ["hard", "stuck", "don't understand", "failing", "impossible", "too much"]
            is_frustrated = any(kw in text.lower() for kw in frustration_keywords)
            
            # Map labels to our system's logic
            detected_emotion = "neutral"
            if label == "negative":
                detected_emotion = "frustrated" if is_frustrated else "confused"
            elif label == "positive":
                detected_emotion = "confident"
                
            return {
                "emotion": detected_emotion,
                "intensity": score,
                "needs_mentorship": detected_emotion in ["frustrated", "confused"] and score > 0.6
            }
        else:
            # Fallback to simple keyword-based analysis from previous implementation
            return self._fallback_analysis(text)

    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        if any(w in text_lower for w in ["stuck", "hard", "don't know"]):
            return {"emotion": "frustrated", "intensity": 0.5, "needs_mentorship": True}
        return {"emotion": "neutral", "intensity": 1.0, "needs_mentorship": False}

    def detect_sarcasm(self, text: str) -> bool:
        """Placeholder for sarcasm detection logic."""
        return False
