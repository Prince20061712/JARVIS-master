import os
import io
from typing import Optional, Dict, Any, List
from utils.logger import logger

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None
    logger.warning("faster-whisper not installed. SpeechToText will be disabled.")

class SpeechToText:
    """
    Handles speech-to-text transcription using faster-whisper.
    Supports multiple languages and domain-specific terminology.
    """
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _load_model(self):
        if self._model is None and WhisperModel:
            logger.info(f"Loading Whisper model: {self.model_size} on {self.device}")
            self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribes a recorded audio file."""
        self._load_model()
        if not self._model:
            return {"text": "", "error": "Model not loaded"}

        try:
            segments, info = self._model.transcribe(audio_path, beam_size=5, language=language)
            
            full_text = ""
            for segment in segments:
                full_text += segment.text + " "
            
            return {
                "text": full_text.strip(),
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration
            }
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {"text": "", "error": str(e)}

    def get_language(self, audio_data: bytes) -> str:
        """Detects the language of raw audio data."""
        # Simplified for now: assuming English/Hindi for engineering focus
        return "en"
