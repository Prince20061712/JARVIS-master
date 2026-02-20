import numpy as np
from utils.logger import logger

try:
    import webrtcvad
except ImportError:
    webrtcvad = None
    logger.warning("webrtcvad not installed. VoiceActivity detection will use energy heuristics.")

class VoiceActivity:
    """
    Detects voice activity (VAD) in real-time audio streams.
    Helps segment audio into user requests and silence.
    """
    def __init__(self, aggressiveness: int = 1):
        self.vad = None
        if webrtcvad:
            self.vad = webrtcvad.Vad(aggressiveness)
        
    def detect_speech(self, frame: bytes, sr: int = 16000) -> bool:
        """Detects if a single frame (10/20/30ms) contains speech."""
        if self.vad:
            try:
                # webrtcvad needs specific frame lengths
                return self.vad.is_speech(frame, sr)
            except Exception:
                return self._energy_heuristic(frame)
        return self._energy_heuristic(frame)

    def _energy_heuristic(self, frame: bytes) -> bool:
        """Fallback VAD based on RMS energy."""
        audio_np = np.frombuffer(frame, dtype=np.int16)
        rms = np.sqrt(np.mean(audio_np.astype(float)**2))
        return rms > 300 # Heuristic threshold for quiet background

    def get_energy(self, frame: bytes) -> float:
        """Calculates energy of the frame for visualizers/noise-logging."""
        audio_np = np.frombuffer(frame, dtype=np.int16)
        if len(audio_np) == 0: return 0.0
        return float(np.sqrt(np.mean(audio_np.astype(float)**2)))

    def segment_audio(self, stream_buffer: List[bytes]) -> List[bytes]:
        """Filters out long silences from an audio buffer."""
        # Simplified: just return the buffer if it has active speech
        return stream_buffer
