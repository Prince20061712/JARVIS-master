import os
from typing import Optional, List, Dict, Any
from utils.logger import logger

# Placeholder for expensive TTS imports like Coqui TTS or pyttsx3 fallback
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

class TextToSpeech:
    """
    Handles text-to-speech synthesis using Coqui (if available) or pyttsx3 (local fallback).
    Supports emotion-based modulation and voice selection.
    """
    def __init__(self, engine_type: str = "local"):
        self.engine_type = engine_type
        self._pyttsx3_engine = None
        
    def _get_engine(self):
        if self.engine_type == "local" and pyttsx3:
            if self._pyttsx3_engine is None:
                self._pyttsx3_engine = pyttsx3.init()
            return self._pyttsx3_engine
        return None

    def synthesize(self, text: str, output_path: str, voice_id: Optional[str] = None) -> bool:
        """Synthesizes text to a WAV/MP3 file."""
        engine = self._get_engine()
        if not engine:
            logger.error("No TTS engine available.")
            return False

        try:
            if voice_id:
                engine.setProperty('voice', voice_id)
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            logger.info(f"Synthesized audio to {output_path}")
            return True
        except Exception as e:
            logger.error(f"TTS Synthesis failed: {e}")
            return False

    def get_voices(self) -> List[Dict[str, str]]:
        """Lists available system voices."""
        engine = self._get_engine()
        if not engine: return []
        
        voices = engine.getProperty('voices')
        return [{"id": v.id, "name": v.name, "languages": v.languages} for v in voices]

    def modulate_by_emotion(self, emotion: str):
        """Adjusts rate and pitch based on student's detected emotion."""
        engine = self._get_engine()
        if not engine: return
        
        if emotion == "frustrated":
            engine.setProperty('rate', 130) # Slower, calmer
        elif emotion == "confident":
            engine.setProperty('rate', 180) # Faster, energetic
        else:
            engine.setProperty('rate', 150) # Normal
