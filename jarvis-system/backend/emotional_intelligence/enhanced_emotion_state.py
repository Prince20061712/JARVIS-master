"""
Enhanced Emotion State Tracker with Complex Emotion Understanding
"""

import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
from dataclasses import dataclass, field
from enum import Enum

class EmotionComplexity(Enum):
    """Complexity level of emotion understanding"""
    BASIC = "basic"          # Just primary emotion
    CONTEXTUAL = "contextual" # With context awareness
    NUANCED = "nuanced"       # With secondary emotions
    DEEP = "deep"            # With root causes and patterns

@dataclass
class EmotionalEpisode:
    """Represents a sustained emotional state"""
    start_time: float
    end_time: Optional[float]
    primary_emotion: str
    intensity_trace: List[Tuple[float, float]]  # (time, intensity)
    context: Dict[str, Any]
    trigger: Optional[str] = None
    resolution: Optional[str] = None
    
    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    @property
    def average_intensity(self) -> float:
        if not self.intensity_trace:
            return 0.0
        return np.mean([i for _, i in self.intensity_trace])

class EnhancedEmotionState:
    """
    Advanced emotion tracker that understands:
    - Complex emotional blends
    - Emotional episodes and patterns
    - Root causes and triggers
    - Long-term emotional trends
    """
    
    def __init__(self, user_id: str, decay_rate: float = 0.1):
        self.user_id = user_id
        self.current_state = {
            "primary_emotion": "neutral",
            "intensity": 0.0,
            "secondary_emotions": [],
            "emotional_blend": {},
            "complexity": EmotionComplexity.BASIC
        }
        
        # Temporal tracking
        self.last_updated = time.time()
        self.decay_rate = decay_rate
        
        # History
        self.emotional_episodes: List[EmotionalEpisode] = []
        self.current_episode: Optional[EmotionalEpisode] = None
        
        # Short-term memory (last 100 interactions)
        self.recent_states = deque(maxlen=100)
        
        # Long-term patterns
        self.emotional_patterns: Dict[str, Any] = {
            "baseline_emotion": "neutral",
            "emotional_variance": 0.0,
            "common_triggers": {},
            "typical_durations": {},
            "recovery_patterns": {}
        }
        
        # Root cause analysis
        self.cause_map: Dict[str, List[str]] = {}
        
        # Intervention effectiveness
        self.intervention_success: Dict[str, Any] = {}
        
    def update(self, 
               detection_result: Dict[str, Any],
               context: Optional[Dict] = None,
               trigger: Optional[str] = None) -> Dict[str, Any]:
        """
        Update emotional state with new detection
        """
        self._apply_decay()
        
        # Extract emotion info
        new_emotion = detection_result.get('primary_emotion', 'neutral')
        new_intensity = detection_result.get('intensity', 0.0)
        secondary = detection_result.get('secondary_emotions', [])
        
        # Handle emotional blend
        emotional_blend = detection_result.get('emotion_scores', {})
        
        # Check for episode boundaries
        self._check_episode_boundary(new_emotion, new_intensity, context, trigger)
        
        # Update current state with emotional blending
        if new_emotion == self.current_state['primary_emotion']:
            # Same emotion - intensity accumulates but with diminishing returns
            self.current_state['intensity'] = min(1.0, 
                self.current_state['intensity'] + new_intensity * 0.3)
        else:
            # Different emotion - blend based on intensity
            self._blend_emotions(new_emotion, new_intensity, emotional_blend)
        
        # Update secondary emotions
        self.current_state['secondary_emotions'] = list(set(
            self.current_state['secondary_emotions'] + secondary
        ))[:5]  # Keep top 5
        
        # Update complexity level
        self._update_complexity()
        
        # Timestamp
        self.last_updated = time.time()
        
        # Store in recent history
        self.recent_states.append({
            'timestamp': self.last_updated,
            'state': self.current_state.copy(),
            'context': context,
            'trigger': trigger
        })
        
        # Analyze patterns periodically
        if len(self.recent_states) % 10 == 0:
            self._analyze_patterns()
        
        return self.get_full_state()
    
    def _blend_emotions(self, new_emotion: str, new_intensity: float, 
                        new_blend: Dict[str, float]):
        """
        Intelligently blend new emotion with current state
        """
        # Calculate blend weights
        current_weight = self.current_state['intensity'] * 0.4
        new_weight = new_intensity * 0.6
        
        # Update emotional blend
        current_blend = self.current_state.get('emotional_blend', {})
        
        for emotion, score in new_blend.items():
            current_blend[emotion] = current_blend.get(emotion, 0) * current_weight + score * new_weight
        
        # Normalize
        total = sum(current_blend.values())
        if total > 0:
            for emotion in current_blend:
                current_blend[emotion] /= total
        
        # Determine primary from blend
        if current_blend:
            self.current_state['primary_emotion'] = max(current_blend, key=current_blend.get)
            self.current_state['intensity'] = current_blend[self.current_state['primary_emotion']]
        
        self.current_state['emotional_blend'] = current_blend
    
    def _check_episode_boundary(self, new_emotion: str, new_intensity: float,
                                 context: Optional[Dict], trigger: Optional[str]):
        """
        Detect if we're starting or ending an emotional episode
        """
        current_primary = self.current_state['primary_emotion']
        
        # Significant emotion change indicates new episode
        if (new_emotion != current_primary and 
            new_intensity > 0.4 and 
            self.current_state['intensity'] > 0.3):
            
            # End current episode
            if self.current_episode:
                self.current_episode.end_time = time.time()
                self.emotional_episodes.append(self.current_episode)
            
            # Start new episode
            self.current_episode = EmotionalEpisode(
                start_time=time.time(),
                end_time=None,
                primary_emotion=new_emotion,
                intensity_trace=[(time.time(), new_intensity)],
                context=context or {},
                trigger=trigger
            )
        elif self.current_episode:
            # Continue current episode
            self.current_episode.intensity_trace.append(
                (time.time(), new_intensity)
            )
    
    def _apply_decay(self):
        """
        Apply emotional decay over time
        """
        elapsed = time.time() - self.last_updated
        decay_amount = (elapsed / 60.0) * self.decay_rate
        
        if decay_amount > 0:
            # Decay intensity
            self.current_state['intensity'] = max(0, 
                self.current_state['intensity'] - decay_amount)
            
            # Decay emotional blend
            blend = self.current_state.get('emotional_blend', {})
            for emotion in blend:
                blend[emotion] = max(0, blend[emotion] - decay_amount / len(blend))
            
            # If intensity hits zero, reset to neutral
            if self.current_state['intensity'] <= 0:
                self.current_state['primary_emotion'] = 'neutral'
                self.current_state['intensity'] = 0
                self.current_state['emotional_blend'] = {}
                self.current_state['secondary_emotions'] = []
    
    def _update_complexity(self):
        """
        Update the complexity level of emotion understanding
        """
        if len(self.recent_states) < 10:
            self.current_state['complexity'] = EmotionComplexity.BASIC
        elif len(self.recent_states) < 50:
            self.current_state['complexity'] = EmotionComplexity.CONTEXTUAL
        elif len(self.recent_states) < 200:
            self.current_state['complexity'] = EmotionComplexity.NUANCED
        else:
            self.current_state['complexity'] = EmotionComplexity.DEEP
    
    def _analyze_patterns(self):
        """
        Analyze emotional patterns over time
        """
        if len(self.recent_states) < 10:
            return
        
        # Calculate emotional baseline
        emotions = [s['state']['primary_emotion'] for s in self.recent_states]
        self.emotional_patterns['baseline_emotion'] = max(set(emotions), key=emotions.count)
        
        # Calculate emotional variance
        intensities = [s['state']['intensity'] for s in self.recent_states]
        self.emotional_patterns['emotional_variance'] = np.var(intensities)
        
        # Analyze triggers
        triggers = [s['trigger'] for s in self.recent_states if s['trigger']]
        for trigger in triggers:
            self.emotional_patterns['common_triggers'][trigger] = \
                self.emotional_patterns['common_triggers'].get(trigger, 0) + 1
        
        # Analyze episode durations
        if self.emotional_episodes:
            for emotion in set(e.primary_emotion for e in self.emotional_episodes):
                episodes = [e for e in self.emotional_episodes if e.primary_emotion == emotion]
                if episodes:
                    durations = [e.duration for e in episodes]
                    self.emotional_patterns['typical_durations'][emotion] = np.mean(durations)
        
        # Analyze recovery patterns
        self._analyze_recovery_patterns()
    
    def _analyze_recovery_patterns(self):
        """
        Analyze how quickly user recovers from negative emotions
        """
        negative_episodes = [e for e in self.emotional_episodes 
                           if e.primary_emotion in ['frustration', 'sadness', 'anger', 'anxiety']]
        
        for episode in negative_episodes:
            if episode.resolution:
                recovery_time = episode.duration
                intervention = episode.resolution
                
                if intervention not in self.intervention_success:
                    self.intervention_success[intervention] = []
                
                self.intervention_success[intervention].append(recovery_time)
        
        # Calculate average recovery time per intervention
        for intervention in self.intervention_success:
            if isinstance(self.intervention_success[intervention], list):
                times = self.intervention_success[intervention]
                self.intervention_success[intervention] = np.mean(times) if times else float('inf')
    
    def get_full_state(self) -> Dict[str, Any]:
        """
        Get complete emotional state with analysis
        """
        self._apply_decay()
        
        return {
            "current": self.current_state,
            "recent_trend": self._get_recent_trend(),
            "patterns": self.emotional_patterns,
            "active_episode": {
                "duration": self.current_episode.duration if self.current_episode else 0,
                "intensity_trend": self._get_intensity_trend()
            } if self.current_episode else None,
            "intervention_effectiveness": self.intervention_success,
            "wellbeing_score": self._calculate_wellbeing()
        }
    
    def _get_recent_trend(self) -> str:
        """
        Determine recent emotional trend
        """
        if len(self.recent_states) < 5:
            return "stable"
        
        recent = list(self.recent_states)[-5:]
        intensities = [s['state']['intensity'] for s in recent]
        
        if intensities[-1] > intensities[0] * 1.2:
            return "improving"
        elif intensities[-1] < intensities[0] * 0.8:
            return "declining"
        else:
            return "stable"
    
    def _get_intensity_trend(self) -> str:
        """
        Get intensity trend for current episode
        """
        if not self.current_episode or len(self.current_episode.intensity_trace) < 3:
            return "stable"
        
        recent = self.current_episode.intensity_trace[-3:]
        if recent[-1][1] > recent[0][1]:
            return "increasing"
        elif recent[-1][1] < recent[0][1]:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_wellbeing(self) -> float:
        """
        Calculate overall wellbeing score (0-1)
        """
        if len(self.recent_states) < 10:
            return 0.5
        
        recent = list(self.recent_states)[-10:]
        
        # Factors
        positive_ratio = 0
        avg_intensity = 0
        stability = 0
        
        for state in recent:
            emotion = state['state']['primary_emotion']
            intensity = state['state']['intensity']
            
            # Check if emotion is positive
            if emotion in ['joy', 'confidence', 'curiosity', 'breakthrough', 'optimism']:
                positive_ratio += intensity
            elif emotion in ['frustration', 'sadness', 'anger', 'anxiety', 'burnout']:
                positive_ratio -= intensity
            
            avg_intensity += intensity
        
        positive_ratio = (float(positive_ratio) / len(recent) + 1.0) / 2.0  # Normalize to 0-1
        avg_intensity = float(avg_intensity) / len(recent)
        
        # Stability (lower variance is better)
        if len(self.emotional_episodes) > 0:
            stability = 1.0 - min(1.0, float(self.emotional_patterns['emotional_variance']))
        
        # Weighted score
        score = positive_ratio * 0.5 + (1.0 - avg_intensity * 0.3) + stability * 0.2
        
        return float(min(1.0, max(0.0, score)))
    
    def get_intervention_recommendation(self) -> Optional[Dict[str, Any]]:
        """
        Recommend intervention based on current state
        """
        state = self.current_state
        emotion = state['primary_emotion']
        intensity = state['intensity']
        
        # Only intervene for significant emotions
        if intensity < 0.4:
            return None
        
        recommendations = {
            'frustration': {
                'action': 'simplify_explanation',
                'message': "I notice you're feeling frustrated. Let's try a different approach.",
                'strategy': 'break_down_problem',
                'urgency': 'medium'
            },
            'anxiety': {
                'action': 'provide_reassurance',
                'message': "Take a deep breath. We'll work through this together.",
                'strategy': 'calm_and_guide',
                'urgency': 'high'
            },
            'joy': {
                'action': 'reinforce_success',
                'message': "Great progress! Would you like to try something more challenging?",
                'strategy': 'build_confidence',
                'urgency': 'low'
            },
            'sadness': {
                'action': 'provide_encouragement',
                'message': "Everyone struggles sometimes. Let's focus on what you've achieved.",
                'strategy': 'build_momentum',
                'urgency': 'medium'
            },
            'burnout': {
                'action': 'suggest_break',
                'message': "You've been working hard. How about a short break?",
                'strategy': 'rest_and_recover',
                'urgency': 'high'
            },
            'breakthrough': {
                'action': 'celebrate',
                'message': "Excellent! That's a great insight!",
                'strategy': 'reinforce_learning',
                'urgency': 'low'
            },
            'curiosity': {
                'action': 'encourage_exploration',
                'message': "Great question! Let's explore this further.",
                'strategy': 'deepen_understanding',
                'urgency': 'low'
            },
            'confusion': {
                'action': 'clarify_concept',
                'message': "This can be tricky. Let me explain it differently.",
                'strategy': 'alternative_explanation',
                'urgency': 'medium'
            }
        }
        
        if emotion in recommendations:
            rec = dict(recommendations[emotion])
            rec['confidence'] = intensity
            rec['based_on_history'] = len(self.recent_states) > 50
            
            # Check if we have effective interventions from history
            if emotion in self.intervention_success:
                best_intervention = min(self.intervention_success[emotion].items(), 
                                      key=lambda x: x[1]) if self.intervention_success[emotion] else None
                if best_intervention:
                    rec['recommended_strategy'] = best_intervention[0]
            
            return rec
        
        return None
