"""
Emotional Intelligence Module for JARVIS
Provides comprehensive emotion understanding and adaptation
"""

from typing import Dict, Any, Optional
from .emotion_taxonomy import EmotionDetector, EmotionTaxonomy
from .enhanced_emotion_state import EnhancedEmotionState
from .emotional_response_adapter import EmotionalResponseAdapter

class EmotionalIntelligence:
    """
    Main integration point for emotional intelligence features
    """
    
    def __init__(self, user_id: str):
        self.detector = EmotionDetector()
        self.state_tracker = EnhancedEmotionState(user_id)
        self.response_adapter = EmotionalResponseAdapter()
        
    async def process_interaction(self,
                                 text: Optional[str] = None,
                                 voice_features: Optional[Dict] = None,
                                 facial_features: Optional[Dict] = None,
                                 context: Optional[Dict] = None,
                                 trigger: Optional[str] = None) -> Dict[str, Any]:
        """
        Process an interaction through the emotional intelligence pipeline
        """
        # Detect emotion from available modalities
        detection = await self.detector.detect_emotion(
            text=text,
            voice_features=voice_features,
            facial_features=facial_features,
            context=context
        )
        
        # Update emotional state
        full_state = self.state_tracker.update(detection, context, trigger)
        
        # Check if intervention is needed
        intervention = self.state_tracker.get_intervention_recommendation()
        
        # Generate proactive message if appropriate
        proactive = self.response_adapter.generate_proactive_message(full_state)
        
        return {
            "detection": detection,
            "state": full_state,
            "intervention": intervention,
            "proactive_message": proactive,
            "wellbeing_score": full_state.get('wellbeing_score', 0.5)
        }
    
    def adapt_response(self, base_response: str, context: Dict[str, Any]) -> str:
        """
        Adapt a response based on current emotional state
        """
        state = self.state_tracker.get_full_state()
        return self.response_adapter.adapt_response(
            base_response, 
            state['current'], 
            context
        )
    
    def get_emotional_summary(self) -> Dict[str, Any]:
        """
        Get summary of emotional state and patterns
        """
        state = self.state_tracker.get_full_state()
        
        return {
            "current_mood": state['current']['primary_emotion'],
            "wellbeing": state['wellbeing_score'],
            "trend": state['recent_trend'],
            "active_episode_duration": state['active_episode']['duration'] if state['active_episode'] else 0,
            "common_patterns": {
                k: v for k, v in state['patterns'].items() 
                if k in ['baseline_emotion', 'emotional_variance']
            }
        }
