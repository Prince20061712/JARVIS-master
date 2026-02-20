import os
import numpy as np
from typing import Dict, Any, Optional
from utils.logger import logger

try:
    import librosa
except ImportError:
    librosa = None
    logger.warning("Librosa not installed. VoiceAnalyzer will have limited functionality.")

class VoiceAnalyzer:
    """
    Analyzes audio features (pitch, energy, tone) to detect real-time user stress.
    Processes streaming audio input or files.
    """
    def __init__(self):
        self.baseline_pitch = None
        self.baseline_energy = None

    def extract_features(self, audio_data: np.ndarray, sr: int = 22050) -> Dict[str, float]:
        """Extracts low-level acoustic features."""
        if not librosa:
            return {}
            
        # Pitch estimation
        pitches, magnitudes = librosa.core.piptrack(y=audio_data, sr=sr)
        pitch = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0
        
        # Energy / RMS
        rms = librosa.feature.rms(y=audio_data)[0]
        energy = np.mean(rms)
        
        # Spectral centroids (brightness of voice)
        centroid = np.mean(librosa.feature.spectral_centroid(y=audio_data, sr=sr))
        
        return {
            "pitch": float(pitch),
            "energy": float(energy),
            "brightness": float(centroid),
            "timestamp": float(librosa.get_duration(y=audio_data, sr=sr))
        }

    def detect_stress(self, features: Dict[str, float]) -> float:
        """
        Heuristic-based stress detection based on deviations from baseline.
        Returns a score from 0.0 to 1.0.
        """
        if self.baseline_pitch is None:
            # Calibrate on the first run
            self.baseline_pitch = features.get("pitch", 0)
            self.baseline_energy = features.get("energy", 0)
            return 0.0

        pitch_diff = (features.get("pitch", 0) - self.baseline_pitch) / (self.baseline_pitch + 1)
        energy_diff = (features.get("energy", 0) - self.baseline_energy) / (self.baseline_energy + 1)
        
        # Stress often correlates with higher pitch and higher energy
        stress_score = (max(0, pitch_diff) * 0.6) + (max(0, energy_diff) * 0.4)
        return min(1.0, stress_score)

    def analyze_audio(self, file_path: str) -> Dict[str, Any]:
        """Analyzes a recorded voice file for emotional cues."""
        if not librosa or not os.path.exists(file_path):
            return {"error": "Librosa not found or file missing."}
            
        y, sr = librosa.load(file_path)
        features = self.extract_features(y, sr)
        stress = self.detect_stress(features)
        
        return {
            "features": features,
            "stress_level": stress,
            "is_stressed": stress > 0.4
        }
