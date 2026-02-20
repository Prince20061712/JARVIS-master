from typing import Dict, Any, Optional
from utils.logger import logger

class MultimodalFusion:
    """
    Fuses emotional signals from voice, text, and contextual data.
    Uses a weighted attention-like mechanism to get a unified emotional state.
    """
    def __init__(self):
        # Initial weights for different modalities
        self.weights = {
            "text": 0.6,
            "voice": 0.3,
            "context": 0.1
        }

    def fuse_modalities(self, text_sentiment: Dict, voice_stress: Optional[Dict] = None, context_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Combines multiple signals into a single 'detected_emotion'.
        If a modality is missing, weights are redistributed.
        """
        active_weights = self.weights.copy()
        
        # Adjust weights if voice is missing
        if voice_stress is None:
            active_weights["text"] += active_weights["voice"]
            active_weights["voice"] = 0.0
            
        # Extract base values
        text_intensity = text_sentiment.get("intensity", 0.0)
        voice_intensity = voice_stress.get("stress_level", 0.0) if voice_stress else 0.0
        
        # Weighted intensity
        combined_intensity = (text_intensity * active_weights["text"]) + (voice_intensity * active_weights["voice"])
        
        # Logic to decide the dominant emotion
        # If voice stress is very high, it might override text "neutrality"
        dominant_emotion = text_sentiment.get("emotion", "neutral")
        if voice_intensity > 0.7:
            dominant_emotion = "stressed" if dominant_emotion != "frustrated" else "frustrated"

        confidence = combined_intensity # Simplified confidence metric
        
        return {
            "fused_emotion": dominant_emotion,
            "intensity": combined_intensity,
            "confidence": confidence,
            "needs_intervention": combined_intensity > 0.6 or dominant_emotion in ["frustrated", "stressed"]
        }

    def calibrate_weights(self, preference: str):
        """Allows user to prioritize voice or text signals."""
        if preference == "voice_heavy":
            self.weights = {"text": 0.3, "voice": 0.6, "context": 0.1}
        elif preference == "balanced":
            self.weights = {"text": 0.45, "voice": 0.45, "context": 0.1}
        logger.info(f"Fusion weights calibrated to {preference}")
