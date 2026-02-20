import pytest
from emotional_intelligence.emotion_detector.text_sentiment import TextSentimentAnalyzer
from emotional_intelligence.emotion_detector.multimodal_fusion import MultimodalFusion
from emotional_intelligence.emotion_detector.emotion_state import EmotionState

def test_text_sentiment_analysis():
    analyzer = TextSentimentAnalyzer()
    res = analyzer.analyze("I am really confused about these circuits.")
    assert res['emotion'] in ["frustrated", "confused", "neutral"]
    assert res['intensity'] > 0.0

def test_multimodal_fusion():
    fusion = MultimodalFusion()
    text_sig = {"emotion": "frustrated", "intensity": 0.8}
    voice_sig = {"stress_level": 0.7}
    
    fused = fusion.fuse_modalities(text_sig, voice_sig)
    assert fused['fused_emotion'] == "frustrated"
    assert fused['intensity'] > 0.7
    assert fused['needs_intervention'] is True

def test_emotion_state_tracking():
    state = EmotionState(decay_rate=0.5)
    state.update_state("stressed", 0.9)
    assert state.current_emotion == "stressed"
    
    # Simulate time pass (not really possible without mocking time, but check update logic)
    state.update_state("stressed", 0.9)
    assert state.intensity > 0.8
    
    state.update_state("neutral", 0.1)
    assert state.current_emotion == "neutral" or state.intensity < 0.5
