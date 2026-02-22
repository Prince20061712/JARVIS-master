"""
Emotion detector module for JARVIS.
Provides multi-modal emotion detection from text, voice, and facial expressions.
Enhanced with monk-like wisdom and psychiatric depth.
"""

from .text_sentiment import TextSentimentAnalyzer
from .voice_analyzer import VoiceEmotionAnalyzer
from .multimodal_fusion import MultiModalFusion
from .emotion_state import EmotionState

__all__ = [
    'TextSentimentAnalyzer',
    'VoiceEmotionAnalyzer',
    'MultiModalFusion',
    'EmotionState'
]