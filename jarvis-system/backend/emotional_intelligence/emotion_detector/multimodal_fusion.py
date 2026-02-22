"""
Multi-modal emotion fusion combining text, voice, and facial expressions.
Enhanced with deep psychological integration and holistic understanding.
"""

from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from datetime import datetime
from .text_sentiment import TextSentimentAnalyzer
from .voice_analyzer import VoiceEmotionAnalyzer
from .emotion_state import EmotionState, EmotionalDepth

class HolisticUnderstanding:
    """Represents a deep, integrated understanding of emotional state"""
    
    def __init__(self):
        self.primary_emotion: str = ""
        self.secondary_emotions: List[Tuple[str, float]] = []
        self.authenticity_score: float = 1.0  # How authentic the emotional expression is
        self.suppressed_emotions: List[str] = []  # Emotions being held back
        self.unconscious_indicators: Dict[str, float] = {}  # Body language, micro-expressions
        self.integration_level: float = 0.0  # How well integrated the emotional expression is
        self.spiritual_alignment: float = 0.0  # Alignment with deeper self
        self.wisdom_emerging: bool = False  # Whether wisdom is arising from emotion

class MultiModalFusion:
    """
    Enhanced multi-modal emotion fusion with psychiatric depth.
    Combines multiple inputs for holistic emotional understanding.
    """
    
    def __init__(self):
        self.text_analyzer = TextSentimentAnalyzer()
        self.voice_analyzer = VoiceEmotionAnalyzer()
        self.emotion_state = EmotionState()
        
        # Weights for different modalities
        self.modality_weights = {
            'text': 0.35,
            'voice': 0.35,
            'facial': 0.30
        }
        
        # Confidence thresholds
        self.high_confidence_threshold = 0.8
        self.low_confidence_threshold = 0.4
        
        # Modality reliability tracking
        self.modality_reliability = {
            'text': 1.0,
            'voice': 1.0,
            'facial': 1.0
        }
        
        # Contradiction patterns
        self.contradiction_patterns = {
            ('joy', 'sadness'): 'masked_sadness',
            ('anger', 'fear'): 'defensive_anger',
            ('calm', 'anxiety'): 'suppressed_anxiety'
        }
        
        # Deep psychological indicators
        self.micro_expression_duration = 0.04  # 40ms typical micro-expression
        self.congruence_threshold = 0.6  # Threshold for emotional congruence
        
    async def fuse_emotions(self, 
                           text: Optional[str] = None,
                           voice_features: Optional[Dict] = None,
                           facial_features: Optional[Dict] = None,
                           context: str = "") -> HolisticUnderstanding:
        """
        Fuse multiple modalities for holistic emotional understanding.
        Returns deep psychological insights.
        """
        understanding = HolisticUnderstanding()
        modality_results = {}
        confidences = {}
        
        # Analyze available modalities
        if text:
            text_result = await self.text_analyzer.analyze(text)
            modality_results['text'] = text_result
            confidences['text'] = text_result.get('confidence', 0.7)
            
        if voice_features:
            voice_result = await self.voice_analyzer.analyze(voice_features)
            modality_results['voice'] = voice_result
            confidences['voice'] = voice_result.get('confidence', 0.7)
            
        if facial_features:
            facial_result = self._analyze_facial(facial_features)
            modality_results['facial'] = facial_result
            confidences['facial'] = facial_result.get('confidence', 0.7)
        
        # Check for contradictions
        contradictions = self._detect_contradictions(modality_results)
        if contradictions:
            understanding.suppressed_emotions = contradictions
        
        # Detect micro-expressions (if facial data available)
        if facial_features:
            micro_expressions = self._detect_micro_expressions(facial_features)
            understanding.unconscious_indicators = micro_expressions
        
        # Calculate authenticity
        understanding.authenticity_score = self._calculate_authenticity(
            modality_results, contradictions
        )
        
        # Fuse emotions with weighted ensemble
        fused_emotion, secondary_emotions = self._weighted_fusion(
            modality_results, confidences
        )
        
        understanding.primary_emotion = fused_emotion['emotion']
        understanding.secondary_emotions = secondary_emotions
        
        # Calculate integration level
        understanding.integration_level = self._calculate_integration(
            modality_results, fused_emotion
        )
        
        # Check for wisdom emergence
        understanding.wisdom_emerging = self._check_wisdom_emergence(
            fused_emotion, context
        )
        
        # Calculate spiritual alignment
        understanding.spiritual_alignment = self._calculate_spiritual_alignment(
            fused_emotion, context
        )
        
        # Update modality reliability based on consistency
        self._update_reliability(modality_results)
        
        # Update emotion state with deep understanding
        state_update = self.emotion_state.update_emotion(
            emotion=understanding.primary_emotion,
            intensity=fused_emotion.get('intensity', 0.5),
            context=context
        )
        
        # Attach state insights to understanding
        understanding.emotional_state_insights = state_update
        
        return understanding
    
    def _detect_contradictions(self, modality_results: Dict) -> List[str]:
        """Detect contradictions between modalities indicating suppressed emotions"""
        contradictions = []
        
        if len(modality_results) < 2:
            return contradictions
        
        modalities = list(modality_results.keys())
        for i in range(len(modalities)):
            for j in range(i+1, len(modalities)):
                m1 = modalities[i]
                m2 = modalities[j]
                
                emotion1 = modality_results[m1].get('primary_emotion', {}).get('emotion')
                emotion2 = modality_results[m2].get('primary_emotion', {}).get('emotion')
                
                if emotion1 and emotion2:
                    # Check for contradiction patterns
                    pattern_key = tuple(sorted([emotion1, emotion2]))
                    if pattern_key in self.contradiction_patterns:
                        contradictions.append(self.contradiction_patterns[pattern_key])
                    
                    # Check for emotional opposites
                    if self._are_emotional_opposites(emotion1, emotion2):
                        contradictions.append(f"conflicting_{emotion1}_and_{emotion2}")
        
        return contradictions
    
    def _detect_micro_expressions(self, facial_features: Dict) -> Dict[str, float]:
        """Detect micro-expressions indicating unconscious emotions"""
        micro_expressions = {}
        
        # Analyze facial muscle movements over time
        if 'expression_sequence' in facial_features:
            sequence = facial_features['expression_sequence']
            
            # Look for very brief expressions (micro-expressions)
            for expression in sequence:
                if expression.get('duration', 1.0) < self.micro_expression_duration:
                    emotion = expression.get('emotion')
                    intensity = expression.get('intensity', 0.3)
                    
                    if emotion not in micro_expressions or intensity > micro_expressions[emotion]:
                        micro_expressions[emotion] = intensity
        
        return micro_expressions
    
    def _calculate_authenticity(self, modality_results: Dict, contradictions: List[str]) -> float:
        """Calculate authenticity of emotional expression"""
        if not modality_results:
            return 0.5
        
        # Base authenticity on consistency
        consistency = self._calculate_consistency(modality_results)
        
        # Reduce authenticity for contradictions
        contradiction_penalty = len(contradictions) * 0.1
        
        # Increase authenticity for congruent expression
        congruence_bonus = self._calculate_congruence(modality_results) * 0.2
        
        authenticity = consistency - contradiction_penalty + congruence_bonus
        return max(0.1, min(1.0, authenticity))
    
    def _calculate_consistency(self, modality_results: Dict) -> float:
        """Calculate consistency across modalities"""
        if len(modality_results) <= 1:
            return 1.0
        
        emotions = []
        for result in modality_results.values():
            if 'primary_emotion' in result:
                emotions.append(result['primary_emotion'].get('emotion', ''))
        
        if not emotions:
            return 0.5
        
        # Check if all emotions are the same
        if all(e == emotions[0] for e in emotions):
            return 1.0
        
        # Calculate pairwise similarity
        similarities = []
        for i in range(len(emotions)):
            for j in range(i+1, len(emotions)):
                similarity = self._emotion_similarity(emotions[i], emotions[j])
                similarities.append(similarity)
        
        return np.mean(similarities) if similarities else 0.5
    
    def _calculate_congruence(self, modality_results: Dict) -> float:
        """Calculate emotional congruence (appropriate emotion for context)"""
        # This would integrate with context awareness
        # For now, return moderate congruence
        return 0.7
    
    def _emotion_similarity(self, emotion1: str, emotion2: str) -> float:
        """Calculate similarity between emotions"""
        # Simplified similarity matrix
        similarity_map = {
            ('joy', 'happiness'): 0.9,
            ('joy', 'excitement'): 0.8,
            ('sadness', 'grief'): 0.9,
            ('sadness', 'melancholy'): 0.8,
            ('anger', 'frustration'): 0.8,
            ('anger', 'rage'): 0.9,
            ('fear', 'anxiety'): 0.8,
            ('fear', 'worry'): 0.7,
            ('calm', 'peace'): 0.9,
            ('calm', 'serene'): 0.8
        }
        
        key = tuple(sorted([emotion1, emotion2]))
        return similarity_map.get(key, 0.3)
    
    def _are_emotional_opposites(self, emotion1: str, emotion2: str) -> bool:
        """Check if emotions are psychological opposites"""
        opposites = [
            ('joy', 'sadness'),
            ('love', 'hate'),
            ('calm', 'anxiety'),
            ('hope', 'despair'),
            ('gratitude', 'resentment')
        ]
        
        pair = tuple(sorted([emotion1, emotion2]))
        return pair in opposites
    
    def _weighted_fusion(self, modality_results: Dict, confidences: Dict) -> Tuple[Dict, List]:
        """Perform weighted fusion of multiple modalities"""
        if not modality_results:
            return {'emotion': 'neutral', 'intensity': 0.5}, []
        
        # Collect all emotion predictions with weights
        all_predictions = []
        secondary_emotions = []
        
        for modality, result in modality_results.items():
            weight = self.modality_weights.get(modality, 0.33)
            reliability = self.modality_reliability.get(modality, 1.0)
            
            # Get primary emotion
            primary = result.get('primary_emotion', {})
            if primary:
                emotion = primary.get('emotion')
                intensity = primary.get('intensity', 0.5)
                confidence = confidences.get(modality, 0.7)
                
                adjusted_weight = weight * reliability * confidence
                all_predictions.append((emotion, intensity, adjusted_weight))
            
            # Get secondary emotions
            secondaries = result.get('secondary_emotions', [])
            for sec_emotion, sec_intensity in secondaries[:2]:  # Top 2 secondary
                secondary_emotions.append((sec_emotion, sec_intensity * weight))
        
        if not all_predictions:
            return {'emotion': 'neutral', 'intensity': 0.5}, []
        
        # Group by emotion and sum weights
        emotion_scores = {}
        intensity_scores = {}
        total_weight = 0
        
        for emotion, intensity, weight in all_predictions:
            emotion_scores[emotion] = emotion_scores.get(emotion, 0) + weight
            if emotion not in intensity_scores:
                intensity_scores[emotion] = []
            intensity_scores[emotion].append((intensity, weight))
            total_weight += weight
        
        # Find primary emotion
        primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        # Calculate weighted intensity for primary emotion
        primary_intensities = intensity_scores[primary_emotion[0]]
        weighted_intensity = sum(i * w for i, w in primary_intensities) / sum(w for _, w in primary_intensities)
        
        # Get secondary emotions (top 3 by score, excluding primary)
        secondary = sorted(
            [(e, s) for e, s in emotion_scores.items() if e != primary_emotion[0]],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return {
            'emotion': primary_emotion[0],
            'intensity': weighted_intensity,
            'confidence': primary_emotion[1] / total_weight if total_weight > 0 else 0.5
        }, secondary
    
    def _calculate_integration(self, modality_results: Dict, fused_emotion: Dict) -> float:
        """Calculate how well integrated the emotional expression is"""
        if not modality_results:
            return 0.5
        
        # Integration is high when modalities agree and there's depth
        consistency = self._calculate_consistency(modality_results)
        depth = fused_emotion.get('intensity', 0.5)
        
        return (consistency * 0.6 + depth * 0.4)
    
    def _check_wisdom_emergence(self, fused_emotion: Dict, context: str) -> bool:
        """Check if wisdom is emerging from emotional experience"""
        # Wisdom often emerges from:
        # 1. High intensity emotions that are processed
        # 2. Contradictory emotions leading to insight
        # 3. Emotional challenges in meaningful contexts
        
        intensity = fused_emotion.get('intensity', 0.5)
        emotion = fused_emotion.get('emotion', '')
        
        # Intense emotions in learning contexts may yield wisdom
        if intensity > 0.7 and any(word in context.lower() for word in ['learn', 'grow', 'understand', 'reflect']):
            return True
        
        # Complex emotions often precede wisdom
        complex_emotions = ['bittersweet', 'nostalgia', 'awe', 'wonder']
        if emotion in complex_emotions:
            return True
        
        return False
    
    def _calculate_spiritual_alignment(self, fused_emotion: Dict, context: str) -> float:
        """Calculate alignment with deeper self/spiritual values"""
        # This would integrate with user's spiritual profile
        # For now, return moderate alignment
        return 0.6
    
    def _update_reliability(self, modality_results: Dict):
        """Update modality reliability based on consistency"""
        if len(modality_results) < 2:
            return
        
        consistency = self._calculate_consistency(modality_results)
        
        # Increase reliability for consistent modalities
        for modality in modality_results:
            if consistency > 0.8:
                self.modality_reliability[modality] = min(1.0, self.modality_reliability[modality] + 0.01)
            elif consistency < 0.3:
                self.modality_reliability[modality] = max(0.5, self.modality_reliability[modality] - 0.01)
    
    def _analyze_facial(self, facial_features: Dict) -> Dict:
        """Analyze facial expressions"""
        # This would integrate with a facial expression recognition system
        # Simplified implementation
        return {
            'primary_emotion': {
                'emotion': facial_features.get('dominant_emotion', 'neutral'),
                'intensity': facial_features.get('intensity', 0.5)
            },
            'secondary_emotions': facial_features.get('secondary_emotions', []),
            'confidence': facial_features.get('confidence', 0.7)
        }
    
    def get_emotional_depth_analysis(self) -> Dict[str, Any]:
        """Get deep analysis of emotional patterns"""
        return self.emotion_state.get_emotional_summary()