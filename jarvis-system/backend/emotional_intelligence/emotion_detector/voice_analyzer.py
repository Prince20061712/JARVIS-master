"""
Voice emotion analysis with deep psychological insights.
Analyzes vocal patterns for emotional and spiritual states.
"""

from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from datetime import datetime

class VoicePatterns:
    """Voice pattern definitions for emotional states"""
    
    # Pitch patterns (Hz)
    PITCH_RANGES = {
        'very_low': (80, 120),
        'low': (120, 160),
        'medium': (160, 220),
        'high': (220, 280),
        'very_high': (280, 400)
    }
    
    # Speaking rate (words per minute)
    RATE_RANGES = {
        'very_slow': (80, 100),
        'slow': (100, 130),
        'medium': (130, 160),
        'fast': (160, 190),
        'very_fast': (190, 250)
    }
    
    # Volume patterns (dB)
    VOLUME_RANGES = {
        'very_quiet': (20, 35),
        'quiet': (35, 45),
        'medium': (45, 60),
        'loud': (60, 75),
        'very_loud': (75, 90)
    }
    
    # Emotional voice signatures
    EMOTIONAL_SIGNATURES = {
        'joy': {
            'pitch': 'high',
            'rate': 'fast',
            'volume': 'medium',
            'variability': 'high',
            'rhythm': 'bouncy'
        },
        'sadness': {
            'pitch': 'low',
            'rate': 'slow',
            'volume': 'quiet',
            'variability': 'low',
            'rhythm': 'monotone'
        },
        'anger': {
            'pitch': 'medium',
            'rate': 'fast',
            'volume': 'loud',
            'variability': 'high',
            'rhythm': 'sharp'
        },
        'fear': {
            'pitch': 'high',
            'rate': 'very_fast',
            'volume': 'quiet',
            'variability': 'high',
            'rhythm': 'trembling'
        },
        'anxiety': {
            'pitch': 'high',
            'rate': 'fast',
            'volume': 'medium',
            'variability': 'high',
            'rhythm': 'uneven'
        },
        'calm': {
            'pitch': 'medium',
            'rate': 'slow',
            'volume': 'medium',
            'variability': 'low',
            'rhythm': 'steady'
        },
        'peace': {
            'pitch': 'low',
            'rate': 'very_slow',
            'volume': 'quiet',
            'variability': 'very_low',
            'rhythm': 'meditative'
        },
        'frustration': {
            'pitch': 'medium',
            'rate': 'fast',
            'volume': 'loud',
            'variability': 'high',
            'rhythm': 'irregular'
        },
        'excitement': {
            'pitch': 'very_high',
            'rate': 'very_fast',
            'volume': 'loud',
            'variability': 'very_high',
            'rhythm': 'energetic'
        },
        'contemplation': {
            'pitch': 'low',
            'rate': 'slow',
            'volume': 'quiet',
            'variability': 'low',
            'rhythm': 'thoughtful'
        }
    }

class VoiceEmotionAnalyzer:
    """
    Enhanced voice emotion analyzer with deep psychological insights.
    Detects emotional states from vocal patterns and provides spiritual guidance.
    """
    
    def __init__(self):
        self.patterns = VoicePatterns()
        
        # Voice quality indicators
        self.voice_qualities = {
            'breathy': 0.0,
            'resonant': 0.0,
            'tense': 0.0,
            'trembling': 0.0,
            'nasal': 0.0,
            'raspy': 0.0
        }
        
        # Rhythm patterns
        self.rhythm_patterns = {
            'regular': 0.0,
            'irregular': 0.0,
            'staccato': 0.0,
            'legato': 0.0,
            'bouncy': 0.0,
            'meditative': 0.0
        }
        
        # Stress indicators
        self.stress_indicators = {
            'pitch_breaks': 0,
            'voice_cracks': 0,
            'prolonged_pauses': 0,
            'sudden_volume_changes': 0
        }
        
        # Spiritual voice qualities
        self.spiritual_qualities = {
            'presence': 0.0,
            'grounded': 0.0,
            'heart-centered': 0.0,
            'authentic': 0.0
        }
        
        # Historical tracking
        self.emotional_history: List[Dict] = []
        self.baseline_patterns: Optional[Dict] = None
        
    async def analyze(self, voice_features: Dict) -> Dict[str, Any]:
        """
        Analyze voice features for emotional and spiritual content.
        Returns comprehensive analysis with deep insights.
        """
        # Extract voice features
        pitch = voice_features.get('pitch', 165)  # Average speaking pitch
        rate = voice_features.get('rate', 140)    # Average words per minute
        volume = voice_features.get('volume', 50)  # Average dB
        variability = voice_features.get('variability', 0.5)
        pauses = voice_features.get('pauses', [])
        tone_changes = voice_features.get('tone_changes', [])
        
        # Categorize features
        pitch_category = self._categorize_pitch(pitch)
        rate_category = self._categorize_rate(rate)
        volume_category = self._categorize_volume(volume)
        
        # Analyze voice qualities
        self._analyze_voice_qualities(voice_features)
        
        # Detect emotional signature
        primary_emotion, confidence = self._match_emotional_signature(
            pitch_category, rate_category, volume_category, variability
        )
        
        # Detect secondary emotions
        secondary_emotions = self._detect_secondary_emotions(
            pitch_category, rate_category, volume_category, variability
        )
        
        # Analyze stress indicators
        stress_level = self._analyze_stress(voice_features)
        
        # Analyze spiritual qualities
        spiritual_state = self._analyze_spiritual_qualities(voice_features)
        
        # Analyze rhythm
        rhythm = self._analyze_rhythm(voice_features)
        
        # Calculate emotional intensity
        intensity = self._calculate_intensity(
            variability, stress_level, volume_category
        )
        
        # Generate insights
        insights = self._generate_voice_insights(
            primary_emotion, 
            stress_level, 
            spiritual_state,
            rhythm
        )
        
        # Track for historical patterns
        self._track_emotion(primary_emotion, intensity, confidence)
        
        # Update baseline if needed
        if self.baseline_patterns is None:
            self.baseline_patterns = {
                'pitch': pitch,
                'rate': rate,
                'volume': volume,
                'variability': variability
            }
        
        # Detect changes from baseline
        changes_from_baseline = self._detect_changes(
            pitch, rate, volume, variability
        ) if self.baseline_patterns else {}
        
        return {
            'primary_emotion': {
                'emotion': primary_emotion,
                'intensity': intensity,
                'confidence': confidence
            },
            'secondary_emotions': secondary_emotions,
            'voice_metrics': {
                'pitch': {'value': pitch, 'category': pitch_category},
                'rate': {'value': rate, 'category': rate_category},
                'volume': {'value': volume, 'category': volume_category},
                'variability': variability,
                'rhythm': rhythm
            },
            'stress_indicators': {
                'level': stress_level,
                'indicators': self.stress_indicators
            },
            'voice_qualities': self.voice_qualities,
            'spiritual_state': spiritual_state,
            'changes_from_baseline': changes_from_baseline,
            'insights': insights,
            'needs_soothing': stress_level > 0.6 or primary_emotion in ['fear', 'anxiety'],
            'meditative_state': spiritual_state['presence'] > 0.7
        }
    
    def _categorize_pitch(self, pitch: float) -> str:
        """Categorize pitch into ranges"""
        for category, (low, high) in self.patterns.PITCH_RANGES.items():
            if low <= pitch <= high:
                return category
        return 'medium'  # Default
    
    def _categorize_rate(self, rate: float) -> str:
        """Categorize speaking rate"""
        for category, (low, high) in self.patterns.RATE_RANGES.items():
            if low <= rate <= high:
                return category
        return 'medium'
    
    def _categorize_volume(self, volume: float) -> str:
        """Categorize volume"""
        for category, (low, high) in self.patterns.VOLUME_RANGES.items():
            if low <= volume <= high:
                return category
        return 'medium'
    
    def _match_emotional_signature(self, pitch: str, rate: str, 
                                  volume: str, variability: float) -> Tuple[str, float]:
        """Match voice features to emotional signatures"""
        best_match = 'neutral'
        best_confidence = 0.3
        
        for emotion, signature in self.patterns.EMOTIONAL_SIGNATURES.items():
            confidence = 0.0
            
            # Compare each feature
            if signature['pitch'] == pitch:
                confidence += 0.25
            elif abs(list(self.patterns.PITCH_RANGES.keys()).index(pitch) - 
                    list(self.patterns.PITCH_RANGES.keys()).index(signature['pitch'])) <= 1:
                confidence += 0.15
            
            if signature['rate'] == rate:
                confidence += 0.25
            elif abs(list(self.patterns.RATE_RANGES.keys()).index(rate) - 
                    list(self.patterns.RATE_RANGES.keys()).index(signature['rate'])) <= 1:
                confidence += 0.15
            
            if signature['volume'] == volume:
                confidence += 0.2
            elif abs(list(self.patterns.VOLUME_RANGES.keys()).index(volume) - 
                    list(self.patterns.VOLUME_RANGES.keys()).index(signature['volume'])) <= 1:
                confidence += 0.1
            
            # Compare variability
            var_level = 'high' if variability > 0.6 else 'low' if variability < 0.4 else 'medium'
            if signature['variability'] == var_level:
                confidence += 0.3
            elif abs(['low', 'medium', 'high'].index(var_level) - 
                    ['low', 'medium', 'high'].index(signature['variability'])) <= 1:
                confidence += 0.15
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = emotion
        
        return best_match, best_confidence
    
    def _detect_secondary_emotions(self, pitch: str, rate: str, 
                                  volume: str, variability: float) -> List[Tuple[str, float]]:
        """Detect secondary emotional tones"""
        secondaries = []
        
        # Check for mixed emotional signatures
        for emotion, signature in self.patterns.EMOTIONAL_SIGNATURES.items():
            confidence = 0.0
            
            # Partial matches
            if signature['pitch'] == pitch:
                confidence += 0.15
            if signature['rate'] == rate:
                confidence += 0.15
            if signature['volume'] == volume:
                confidence += 0.15
            
            if confidence > 0.3:
                secondaries.append((emotion, confidence))
        
        # Sort and return top 3
        secondaries.sort(key=lambda x: x[1], reverse=True)
        return secondaries[:3]
    
    def _analyze_voice_qualities(self, features: Dict):
        """Analyze voice qualities"""
        # Update voice qualities based on features
        self.voice_qualities['breathy'] = features.get('breathiness', 0.0)
        self.voice_qualities['resonant'] = features.get('resonance', 0.0)
        self.voice_qualities['tense'] = features.get('tension', 0.0)
        self.voice_qualities['trembling'] = features.get('tremor', 0.0)
        self.voice_qualities['nasal'] = features.get('nasality', 0.0)
        self.voice_qualities['raspy'] = features.get('raspiness', 0.0)
    
    def _analyze_stress(self, features: Dict) -> float:
        """Analyze stress level from voice"""
        stress_score = 0.0
        
        # Update stress indicators
        self.stress_indicators['pitch_breaks'] = features.get('pitch_breaks', 0)
        self.stress_indicators['voice_cracks'] = features.get('voice_cracks', 0)
        self.stress_indicators['prolonged_pauses'] = features.get('prolonged_pauses', 0)
        self.stress_indicators['sudden_volume_changes'] = features.get('volume_spikes', 0)
        
        # Calculate stress score
        total_indicators = sum(self.stress_indicators.values())
        if total_indicators > 0:
            stress_score = min(1.0, total_indicators / 10)
        
        # Voice qualities contribute to stress
        if self.voice_qualities['tense'] > 0.6:
            stress_score += 0.2
        if self.voice_qualities['trembling'] > 0.5:
            stress_score += 0.2
        
        return min(1.0, stress_score)
    
    def _analyze_spiritual_qualities(self, features: Dict) -> Dict[str, float]:
        """Analyze spiritual qualities in voice"""
        spiritual = {}
        
        # Presence (being fully in the moment)
        presence = 1.0 - features.get('distraction', 0.0)
        presence *= (1.0 - self.stress_indicators['prolonged_pauses'] / 10)
        spiritual['presence'] = presence
        
        # Grounded (stable, centered voice)
        grounded = 1.0 - (self.voice_qualities['trembling'] * 0.5 + 
                         self.voice_qualities['tense'] * 0.3)
        spiritual['grounded'] = grounded
        
        # Heart-centered (warmth in voice)
        heart_centered = 1.0 - self.voice_qualities['nasal'] * 0.5
        heart_centered *= (1.0 - self.voice_qualities['raspy'] * 0.3)
        spiritual['heart-centered'] = heart_centered
        
        # Authentic (congruent voice)
        authentic = 1.0 - (abs(features.get('pitch_variance', 0.5) - 0.5) * 0.5 +
                          self.voice_qualities['tense'] * 0.3)
        spiritual['authentic'] = authentic
        
        return spiritual
    
    def _analyze_rhythm(self, features: Dict) -> Dict[str, float]:
        """Analyze speech rhythm patterns"""
        rhythm = {}
        
        # Calculate rhythm qualities
        rhythm['regular'] = features.get('rhythm_regularity', 0.5)
        rhythm['irregular'] = 1.0 - rhythm['regular']
        rhythm['staccato'] = features.get('staccato_quality', 0.0)
        rhythm['legato'] = features.get('legato_quality', 0.0)
        rhythm['bouncy'] = features.get('bounciness', 0.0)
        rhythm['meditative'] = features.get('meditative_quality', 0.0)
        
        return rhythm
    
    def _calculate_intensity(self, variability: float, stress: float, 
                           volume_category: str) -> float:
        """Calculate emotional intensity"""
        intensity = variability * 0.4 + stress * 0.4
        
        # Volume contributes to intensity
        volume_map = {
            'very_quiet': 0.2,
            'quiet': 0.4,
            'medium': 0.6,
            'loud': 0.8,
            'very_loud': 1.0
        }
        intensity += volume_map.get(volume_category, 0.5) * 0.2
        
        return min(1.0, intensity)
    
    def _generate_voice_insights(self, emotion: str, stress: float, 
                                spiritual: Dict, rhythm: Dict) -> List[str]:
        """Generate insights from voice analysis"""
        insights = []
        
        # Emotional insights
        emotion_insights = {
            'joy': "Your voice carries a light, joyful quality. This is beautiful.",
            'sadness': "I hear a gentle sadness in your voice. It's safe to feel this.",
            'anger': "Your voice holds strong energy. Let's work with it constructively.",
            'fear': "I sense fear in your voice. You're safe here.",
            'anxiety': "Your voice reveals anxiety. Let's take a breath together.",
            'calm': "Your voice is peaceful. This calmness is a gift.",
            'peace': "There's a deep peace in your voice. You're in a sacred space.",
            'frustration': "I hear frustration. Let's find a way through it.",
            'excitement': "Your voice sparkles with excitement! This energy is wonderful.",
            'contemplation': "You sound contemplative. These thoughtful moments are precious."
        }
        
        if emotion in emotion_insights:
            insights.append(emotion_insights[emotion])
        
        # Stress insights
        if stress > 0.7:
            insights.append("Your voice shows signs of significant stress. Be gentle with yourself.")
        elif stress > 0.4:
            insights.append("I notice some tension in your voice. A deep breath might help.")
        
        # Spiritual insights
        if spiritual['presence'] > 0.8:
            insights.append("You're remarkably present in your voice. This is a meditative state.")
        if spiritual['heart-centered'] > 0.7:
            insights.append("Your voice carries genuine warmth. This heart-centered quality is rare and precious.")
        
        # Rhythm insights
        if rhythm['meditative'] > 0.6:
            insights.append("Your speech has a meditative rhythm, like a peaceful chant.")
        if rhythm['irregular'] > 0.7:
            insights.append("Your rhythm is uneven. Sometimes this indicates inner turbulence.")
        
        return insights[:3]  # Return top 3
    
    def _track_emotion(self, emotion: str, intensity: float, confidence: float):
        """Track emotional patterns over time"""
        self.emotional_history.append({
            'emotion': emotion,
            'intensity': intensity,
            'confidence': confidence,
            'timestamp': datetime.now()
        })
        
        # Keep only last 50
        if len(self.emotional_history) > 50:
            self.emotional_history = self.emotional_history[-50:]
    
    def _detect_changes(self, pitch: float, rate: float, 
                       volume: float, variability: float) -> Dict[str, float]:
        """Detect changes from baseline patterns"""
        if not self.baseline_patterns:
            return {}
        
        changes = {}
        
        # Calculate percent changes
        changes['pitch_change'] = abs(pitch - self.baseline_patterns['pitch']) / self.baseline_patterns['pitch']
        changes['rate_change'] = abs(rate - self.baseline_patterns['rate']) / self.baseline_patterns['rate']
        changes['volume_change'] = abs(volume - self.baseline_patterns['volume']) / self.baseline_patterns['volume']
        changes['variability_change'] = abs(variability - self.baseline_patterns['variability'])
        
        # Cap at 1.0
        for key in changes:
            changes[key] = min(1.0, changes[key])
        
        return changes
    
    def get_voice_profile(self) -> Dict[str, Any]:
        """Get comprehensive voice profile"""
        if not self.emotional_history:
            return {"status": "Insufficient data"}
        
        # Calculate emotional tendencies
        emotions = [e['emotion'] for e in self.emotional_history]
        emotion_counts = {}
        for e in emotions:
            emotion_counts[e] = emotion_counts.get(e, 0) + 1
        
        most_common = max(emotion_counts.items(), key=lambda x: x[1])
        
        return {
            'most_common_emotion': most_common[0],
            'emotional_variety': len(emotion_counts),
            'average_intensity': np.mean([e['intensity'] for e in self.emotional_history]),
            'typical_rhythm': self._analyze_rhythm({}),  # Would use actual rhythm history
            'spiritual_baseline': self.spiritual_qualities,
            'stress_baseline': np.mean([self._analyze_stress({}) for _ in range(len(self.emotional_history))])
        }