"""
Emotion state management with deep psychological insights and monk-like wisdom.
Tracks emotional patterns, provides spiritual guidance, and maintains wellbeing metrics.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import numpy as np
from enum import Enum

class EmotionalDepth(Enum):
    """Levels of emotional understanding"""
    SURFACE = "surface"  # Immediate emotional reaction
    CORE = "core"  # Underlying emotional state
    SPIRITUAL = "spiritual"  # Soul-level emotional wellbeing
    TRANSCENDENT = "transcendent"  # Beyond emotion - wisdom state

@dataclass
class EmotionalEpisode:
    """Represents a significant emotional experience"""
    emotion: str
    intensity: float  # 0-1
    context: str
    timestamp: datetime
    duration: timedelta = timedelta(seconds=0)
    resolution: Optional[str] = None
    lesson_learned: Optional[str] = None
    depth: EmotionalDepth = EmotionalDepth.SURFACE
    
    def is_resolved(self) -> bool:
        return self.resolution is not None

@dataclass
class WisdomInsight:
    """A spiritual or psychological insight gained from emotional patterns"""
    insight: str
    emotion_source: str
    timestamp: datetime
    category: str  # 'growth', 'warning', 'opportunity', 'acceptance'
    practical_advice: str
    meditative_guidance: Optional[str] = None

class EmotionState:
    """
    Enhanced emotion state tracker with monk-like wisdom and psychiatric depth.
    Tracks emotional patterns, provides insights, and guides personal growth.
    """
    
    def __init__(self):
        self.current_emotion: Optional[str] = None
        self.current_intensity: float = 0.0
        self.emotional_history: List[EmotionalEpisode] = []
        self.wisdom_insights: List[WisdomInsight] = []
        self.wellbeing_score: float = 0.85  # 0-1 baseline
        self.baseline_emotion: str = "peaceful"
        self.consecutive_negative: int = 0
        self.positive_to_negative_ratio: float = 1.0
        self.emotional_triggers: Dict[str, int] = {}
        self.growth_opportunities: List[str] = []
        
        # Deep psychological metrics
        self.emotional_intelligence_quotient: float = 0.7
        self.resilience_score: float = 0.8
        self.spiritual_awareness: float = 0.6
        self.self_compassion_level: float = 0.75
        
        # Monk-like wisdom parameters
        self.detachment_level: float = 0.5  # Ability to observe emotions without being consumed
        self.mindfulness_score: float = 0.6  # Present moment awareness
        self.compassion_level: float = 0.8  # Self-compassion and compassion for others
        
        # Time-based tracking
        self.last_update = datetime.now()
        self.daily_mood_pattern: List[float] = []
        self.weekly_trend: List[float] = []
        
    def update_emotion(self, emotion: str, intensity: float, context: str = "") -> Dict[str, Any]:
        """
        Update current emotion with deep psychological tracking.
        Returns insights and recommendations for emotional growth.
        """
        previous_emotion = self.current_emotion
        previous_intensity = self.current_intensity
        
        # Create emotional episode if significant change
        if emotion != previous_emotion or abs(intensity - previous_intensity) > 0.2:
            if self.current_emotion:
                # End previous episode
                if self.emotional_history:
                    last_episode = self.emotional_history[-1]
                    last_episode.duration = datetime.now() - last_episode.timestamp
            
            # Start new episode
            episode = EmotionalEpisode(
                emotion=emotion,
                intensity=intensity,
                context=context,
                timestamp=datetime.now()
            )
            self.emotional_history.append(episode)
            
            # Keep only last 100 episodes for memory efficiency
            if len(self.emotional_history) > 100:
                self.emotional_history = self.emotional_history[-100:]
        
        self.current_emotion = emotion
        self.current_intensity = intensity
        self.last_update = datetime.now()
        
        # Update metrics
        self._update_emotional_metrics(emotion, intensity)
        
        # Track triggers
        if context and intensity > 0.6:
            self.emotional_triggers[context] = self.emotional_triggers.get(context, 0) + 1
        
        # Generate insights
        insights = self._generate_wisdom_insights(emotion, intensity, context)
        
        # Calculate wellbeing impact
        wellbeing_impact = self._calculate_wellbeing_impact(emotion, intensity)
        self.wellbeing_score = max(0.1, min(1.0, self.wellbeing_score + wellbeing_impact))
        
        # Check for growth opportunities
        growth_opportunities = self._identify_growth_opportunities()
        
        return {
            "previous_state": previous_emotion,
            "current_state": emotion,
            "intensity": intensity,
            "wellbeing_score": self.wellbeing_score,
            "insights": insights,
            "growth_opportunities": growth_opportunities,
            "needs_intervention": self._needs_intervention(),
            "intervention_type": self._get_intervention_type() if self._needs_intervention() else None,
            "spiritual_guidance": self._get_spiritual_guidance(emotion)
        }
    
    def _update_emotional_metrics(self, emotion: str, intensity: float):
        """Update deep psychological metrics"""
        # Update consecutive negative count
        negative_emotions = ["sadness", "anger", "fear", "anxiety", "frustration", "despair"]
        if emotion in negative_emotions:
            self.consecutive_negative += 1
        else:
            self.consecutive_negative = 0
        
        # Update positive/negative ratio
        positive_emotions = ["joy", "peace", "gratitude", "contentment", "love", "hope"]
        if emotion in positive_emotions:
            self.positive_to_negative_ratio = self.positive_to_negative_ratio * 0.9 + 0.1
        elif emotion in negative_emotions:
            self.positive_to_negative_ratio = self.positive_to_negative_ratio * 0.95 - 0.05
        
        self.positive_to_negative_ratio = max(0.1, min(2.0, self.positive_to_negative_ratio))
        
        # Update resilience (ability to bounce back)
        if self.consecutive_negative > 3:
            self.resilience_score = max(0.3, self.resilience_score - 0.05)
        elif emotion in positive_emotions:
            self.resilience_score = min(1.0, self.resilience_score + 0.02)
        
        # Update spiritual awareness (recognizing transient nature of emotions)
        if len(self.emotional_history) > 10:
            emotional_variety = len(set(e.emotion for e in self.emotional_history[-10:]))
            self.spiritual_awareness = min(1.0, emotional_variety / 10 * 0.8)
        
        # Update detachment level (observing without attachment)
        if self.consecutive_negative > 0:
            # Practice in adversity
            self.detachment_level = min(1.0, self.detachment_level + 0.01)
        
        # Update mindfulness (present moment awareness)
        time_since_update = (datetime.now() - self.last_update).seconds
        if time_since_update < 60:  # Frequent updates indicate mindfulness
            self.mindfulness_score = min(1.0, self.mindfulness_score + 0.01)
    
    def _generate_wisdom_insights(self, emotion: str, intensity: float, context: str) -> List[str]:
        """Generate deep insights based on emotional patterns"""
        insights = []
        
        # Pattern recognition
        if len(self.emotional_history) >= 5:
            recent_emotions = [e.emotion for e in self.emotional_history[-5:]]
            
            # Check for patterns
            if recent_emotions.count(emotion) >= 3:
                insights.append(f"I notice {emotion} has been visiting you frequently. This pattern might hold a message for your growth.")
            
            # Emotional roller coaster
            if len(set(recent_emotions)) >= 4:
                insights.append("Your emotions are dancing like autumn leaves today. Remember, you are the sky, not the weather.")
        
        # Intensity insights
        if intensity > 0.8:
            insights.append(f"This wave of {emotion} is strong. Like the ocean, its power can be overwhelming, but remember you can learn to surf these waves.")
        elif intensity < 0.3 and emotion not in ["peace", "contentment"]:
            insights.append(f"A gentle whisper of {emotion}. Sometimes our deepest feelings start as subtle nudges.")
        
        # Context-based wisdom
        if context and self.emotional_triggers.get(context, 0) > 3:
            insights.append(f"{context} seems to be a recurring theme in your emotional journey. Perhaps this is your soul's way of pointing toward an area needing attention.")
        
        return insights
    
    def _identify_growth_opportunities(self) -> List[str]:
        """Identify areas for emotional and spiritual growth"""
        opportunities = []
        
        # Check emotional range
        if len(self.emotional_history) > 20:
            unique_emotions = set(e.emotion for e in self.emotional_history[-20:])
            if len(unique_emotions) < 5:
                opportunities.append("Your emotional palette seems limited. Exploring a wider range of feelings can deepen your self-understanding.")
        
        # Check resilience
        if self.resilience_score < 0.5:
            opportunities.append("Building emotional resilience could serve you well. Each challenging emotion is an opportunity to strengthen your inner core.")
        
        # Check detachment
        if self.detachment_level < 0.4:
            opportunities.append("You might benefit from observing your emotions without being consumed by them. Meditation could help develop this skill.")
        
        # Check compassion
        if self.self_compassion_level < 0.6:
            opportunities.append("Be gentle with yourself during emotional storms. Self-compassion is not weakness; it's the foundation of strength.")
        
        return opportunities
    
    def _needs_intervention(self) -> bool:
        """Determine if emotional intervention is needed"""
        return (
            self.wellbeing_score < 0.4 or
            self.consecutive_negative > 5 or
            self.positive_to_negative_ratio < 0.3 or
            (self.current_intensity > 0.8 and self.current_emotion in ["anger", "despair", "anxiety"])
        )
    
    def _get_intervention_type(self) -> str:
        """Get appropriate intervention type based on emotional state"""
        if self.current_intensity > 0.8:
            if self.current_emotion == "anxiety":
                return "immediate_stress_reduction"
            elif self.current_emotion == "anger":
                return "calming_practice"
            elif self.current_emotion == "despair":
                return "compassionate_support"
        
        if self.consecutive_negative > 3:
            return "emotional_resilience_training"
        
        if self.wellbeing_score < 0.3:
            return "deep_spiritual_support"
        
        return "gentle_guidance"
    
    def _get_spiritual_guidance(self, emotion: str) -> str:
        """Provide spiritual guidance based on current emotion"""
        guidance_map = {
            "anger": "Anger is like holding a hot coal with the intention of throwing it. Release it, and you free yourself.",
            "sadness": "Sadness is the rain that waters the garden of your soul. Let it nourish, not drown you.",
            "fear": "Fear is a doorway to courage. On the other side of your fear lives your strength.",
            "anxiety": "Anxiety is tomorrow's storm in today's mind. Return to this breath, this moment, this peace.",
            "joy": "Joy is your true nature. Let it flow through you like sunlight through a window.",
            "frustration": "Frustration arises when reality doesn't match your expectations. Surrender to what is.",
            "loneliness": "Loneliness is the soul calling you home to yourself. In this space, you can meet your own depth.",
            "gratitude": "Gratitude transforms what we have into enough. Stay in this sacred space.",
            "hope": "Hope is the bridge between despair and possibility. Walk it with patience.",
            "peace": "Peace is not the absence of chaos, but the presence of calm within it."
        }
        return guidance_map.get(emotion, "All emotions are visitors. Let them come and go.")
    
    def _calculate_wellbeing_impact(self, emotion: str, intensity: float) -> float:
        """Calculate impact on wellbeing score"""
        impact_map = {
            "joy": 0.05,
            "peace": 0.04,
            "gratitude": 0.06,
            "contentment": 0.03,
            "hope": 0.04,
            "love": 0.07,
            "sadness": -0.03,
            "anger": -0.04,
            "fear": -0.05,
            "anxiety": -0.06,
            "frustration": -0.03,
            "despair": -0.08
        }
        
        base_impact = impact_map.get(emotion, 0)
        return base_impact * intensity
    
    def get_emotional_summary(self) -> Dict[str, Any]:
        """Get a comprehensive emotional summary with spiritual insights"""
        return {
            "current_emotion": self.current_emotion,
            "current_intensity": self.current_intensity,
            "wellbeing_score": self.wellbeing_score,
            "emotional_intelligence": self.emotional_intelligence_quotient,
            "resilience": self.resilience_score,
            "spiritual_awareness": self.spiritual_awareness,
            "detachment": self.detachment_level,
            "mindfulness": self.mindfulness_score,
            "compassion": self.compassion_level,
            "positive_to_negative_ratio": self.positive_to_negative_ratio,
            "common_triggers": self._get_top_triggers(5),
            "recent_patterns": self._analyze_recent_patterns(),
            "wisdom_insights": [i.insight for i in self.wisdom_insights[-3:]],
            "growth_path": self._suggest_growth_path()
        }
    
    def _get_top_triggers(self, n: int) -> List[str]:
        """Get top emotional triggers"""
        sorted_triggers = sorted(self.emotional_triggers.items(), key=lambda x: x[1], reverse=True)
        return [f"{trigger} ({count} times)" for trigger, count in sorted_triggers[:n]]
    
    def _analyze_recent_patterns(self) -> List[str]:
        """Analyze recent emotional patterns"""
        if len(self.emotional_history) < 5:
            return ["Building emotional history..."]
        
        recent = self.emotional_history[-5:]
        patterns = []
        
        # Check for improvement/deterioration
        intensities = [e.intensity for e in recent]
        if len(intensities) > 1:
            if intensities[-1] < intensities[0]:
                patterns.append("Your emotional intensity is decreasing, showing resilience.")
            elif intensities[-1] > intensities[0]:
                patterns.append("Emotional intensity is increasing. Consider what might be accumulating.")
        
        # Check emotional variety
        emotions = [e.emotion for e in recent]
        if len(set(emotions)) == 1:
            patterns.append(f"You've been in a sustained state of {emotions[0]}. This depth of feeling can lead to profound insights.")
        
        return patterns
    
    def _suggest_growth_path(self) -> str:
        """Suggest a spiritual/emotional growth path"""
        if self.spiritual_awareness < 0.4:
            return "Begin with mindfulness meditation - observe your emotions like clouds passing in the sky."
        elif self.detachment_level < 0.5:
            return "Practice loving-kindness meditation to develop compassion for yourself during emotional storms."
        elif self.emotional_intelligence_quotient < 0.6:
            return "Journal your emotions daily, noting their triggers and messages. This builds emotional vocabulary."
        else:
            return "You're ready for deeper practice. Consider how you can serve others from your growing emotional wisdom."
    
    def add_wisdom_insight(self, insight: str, emotion_source: str, category: str, practical_advice: str):
        """Add a wisdom insight to the collection"""
        wisdom = WisdomInsight(
            insight=insight,
            emotion_source=emotion_source,
            timestamp=datetime.now(),
            category=category,
            practical_advice=practical_advice
        )
        self.wisdom_insights.append(wisdom)
        
        # Keep only last 50 insights
        if len(self.wisdom_insights) > 50:
            self.wisdom_insights = self.wisdom_insights[-50:]