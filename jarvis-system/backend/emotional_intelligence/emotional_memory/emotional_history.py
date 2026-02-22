"""
Emotional history tracking with deep psychological and spiritual memory.
Maintains a wisdom-based record of emotional journeys and growth patterns.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
from enum import Enum
from collections import defaultdict
import json
from pathlib import Path

class EmotionalSeason(Enum):
    """Metaphorical seasons representing emotional periods"""
    SPRING = "spring"  # New beginnings, hope, growth
    SUMMER = "summer"  # Fullness, joy, expression
    AUTUMN = "autumn"  # Letting go, reflection, harvest
    WINTER = "winter"  # Stillness, rest, inner work
    MONSOON = "monsoon"  # Intense emotional release
    INDIAN_SUMMER = "indian_summer"  # Unexpected warmth in difficult times

class WisdomLevel(Enum):
    """Levels of wisdom achieved from emotional experiences"""
    SEED = "seed"  # Beginning to understand
    SPROUT = "sprout"  # Initial insights
    FLOWER = "flower"  # Growing wisdom
    FRUIT = "fruit"  # Mature wisdom
    TREE = "tree"  # Deep wisdom that can nurture others

@dataclass
class EmotionalEvent:
    """A significant emotional event with context and learnings"""
    id: str
    timestamp: datetime
    emotion: str
    intensity: float
    context: str
    trigger: Optional[str] = None
    duration: timedelta = timedelta(minutes=0)
    resolution: Optional[str] = None
    insights_gained: List[str] = field(default_factory=list)
    wisdom_harvested: Optional[str] = None
    season: EmotionalSeason = EmotionalSeason.SPRING
    impact_score: float = 0.5  # How much this event impacted wellbeing
    related_events: List[str] = field(default_factory=list)  # IDs of related events
    
@dataclass 
class EmotionalPattern:
    """Recurring emotional patterns with deep insights"""
    name: str
    emotions: List[str]
    frequency: int
    first_detected: datetime
    last_detected: datetime
    common_triggers: List[str]
    typical_duration: timedelta
    wisdom_learned: List[str] = field(default_factory=list)
    growth_stage: WisdomLevel = WisdomLevel.SEED
    spiritual_message: Optional[str] = None
    meditation_practice: Optional[str] = None

@dataclass
class GrowthMilestone:
    """Significant growth moments in emotional journey"""
    date: datetime
    milestone_type: str  # 'breakthrough', 'acceptance', 'realization', 'healing'
    description: str
    emotion_involved: str
    wisdom_gained: str
    celebration_suggestion: str  # How to honor this milestone

class EmotionalHistory:
    """
    Enhanced emotional history tracker with wisdom-based memory.
    Maintains a sacred record of emotional journeys and provides deep insights.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else Path.home() / '.jarvis' / 'emotional_memory'
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Core data structures
        self.events: List[EmotionalEvent] = []
        self.patterns: Dict[str, EmotionalPattern] = {}
        self.milestones: List[GrowthMilestone] = []
        
        # Wisdom tracking
        self.wisdom_journal: List[Dict] = []
        self.seasons_history: List[Tuple[datetime, EmotionalSeason]] = []
        
        # Statistical tracking
        self.emotional_baseline: Dict[str, float] = {}
        self.seasonal_patterns: Dict[EmotionalSeason, List[EmotionalEvent]] = defaultdict(list)
        
        # Growth metrics
        self.emotional_iq: float = 0.5
        self.wisdom_quotient: float = 0.3
        self.healing_index: float = 0.5
        self.spiritual_alignment: float = 0.4
        
        # Load existing history
        self._load_history()
        
    async def record_event(self, 
                          emotion: str, 
                          intensity: float, 
                          context: str,
                          trigger: Optional[str] = None,
                          duration: timedelta = timedelta(minutes=0),
                          insights: List[str] = None) -> EmotionalEvent:
        """Record an emotional event with wisdom tracking"""
        
        # Create event
        event = EmotionalEvent(
            id=f"evt_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            emotion=emotion,
            intensity=intensity,
            context=context,
            trigger=trigger,
            duration=duration,
            insights_gained=insights or [],
            season=self._determine_season(emotion, intensity),
            impact_score=self._calculate_impact(emotion, intensity, duration)
        )
        
        # Check for related events (similar context/trigger)
        related = self._find_related_events(event)
        event.related_events = related
        
        # Add to history
        self.events.append(event)
        
        # Update seasonal patterns
        self.seasonal_patterns[event.season].append(event)
        
        # Detect patterns
        await self._detect_patterns()
        
        # Check for milestones
        milestone = await self._check_for_milestone(event)
        if milestone:
            self.milestones.append(milestone)
        
        # Harvest wisdom
        wisdom = self._harvest_wisdom(event)
        if wisdom:
            event.wisdom_harvested = wisdom
            self.wisdom_journal.append({
                'date': datetime.now(),
                'wisdom': wisdom,
                'event_id': event.id,
                'emotion': emotion
            })
        
        # Update growth metrics
        self._update_growth_metrics()
        
        # Save history
        self._save_history()
        
        return event
    
    def _determine_season(self, emotion: str, intensity: float) -> EmotionalSeason:
        """Determine the emotional season based on emotion and intensity"""
        
        # High intensity negative emotions often indicate monsoon (release)
        if emotion in ['anger', 'frustration', 'grief'] and intensity > 0.7:
            return EmotionalSeason.MONSOON
        
        # Low intensity negative emotions often indicate winter (rest)
        if emotion in ['sadness', 'melancholy'] and intensity < 0.4:
            return EmotionalSeason.WINTER
        
        # Positive emotions with growth context indicate spring
        if emotion in ['hope', 'curiosity', 'excitement']:
            return EmotionalSeason.SPRING
        
        # Joy and contentment with high intensity indicate summer
        if emotion in ['joy', 'love', 'gratitude'] and intensity > 0.6:
            return EmotionalSeason.SUMMER
        
        # Reflection emotions indicate autumn
        if emotion in ['contemplation', 'nostalgia', 'bittersweet']:
            return EmotionalSeason.AUTUMN
        
        # Unexpected positive during difficulty indicates Indian summer
        if emotion in ['peace', 'calm'] and self._is_difficult_period():
            return EmotionalSeason.INDIAN_SUMMER
        
        # Default based on intensity
        if intensity > 0.7:
            return EmotionalSeason.SUMMER
        elif intensity < 0.3:
            return EmotionalSeason.WINTER
        else:
            return EmotionalSeason.SPRING
    
    def _is_difficult_period(self) -> bool:
        """Check if current period is emotionally difficult"""
        if len(self.events) < 10:
            return False
        
        recent = self.events[-10:]
        negative_count = sum(1 for e in recent if e.emotion in 
                           ['sadness', 'anger', 'fear', 'anxiety', 'frustration'])
        return negative_count >= 7
    
    def _calculate_impact(self, emotion: str, intensity: float, duration: timedelta) -> float:
        """Calculate the emotional impact score"""
        impact = intensity * 0.5
        
        # Longer duration = higher impact
        duration_hours = duration.total_seconds() / 3600
        impact += min(0.3, duration_hours / 24 * 0.3)
        
        # Certain emotions have higher baseline impact
        high_impact_emotions = ['grief', 'trauma', 'ecstasy', 'awe']
        if emotion in high_impact_emotions:
            impact += 0.2
        
        return min(1.0, impact)
    
    def _find_related_events(self, event: EmotionalEvent) -> List[str]:
        """Find events related to this one by context or trigger"""
        related = []
        
        for past_event in self.events[-50:]:  # Look at last 50 events
            # Same trigger
            if event.trigger and past_event.trigger == event.trigger:
                related.append(past_event.id)
            
            # Similar context
            elif event.context and past_event.context and \
                 self._context_similarity(event.context, past_event.context) > 0.7:
                related.append(past_event.id)
            
            # Same emotion cluster
            elif self._same_emotion_cluster(event.emotion, past_event.emotion):
                related.append(past_event.id)
        
        return related[:5]  # Limit to 5 related events
    
    def _context_similarity(self, context1: str, context2: str) -> float:
        """Calculate similarity between two contexts"""
        # Simple word overlap similarity
        words1 = set(context1.lower().split())
        words2 = set(context2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _same_emotion_cluster(self, emotion1: str, emotion2: str) -> bool:
        """Check if emotions belong to same cluster"""
        clusters = {
            'sadness': ['sadness', 'grief', 'melancholy', 'despair'],
            'anger': ['anger', 'frustration', 'irritation', 'rage'],
            'fear': ['fear', 'anxiety', 'worry', 'dread'],
            'joy': ['joy', 'happiness', 'ecstasy', 'delight'],
            'peace': ['peace', 'calm', 'serenity', 'contentment'],
            'love': ['love', 'affection', 'compassion', 'tenderness']
        }
        
        for cluster in clusters.values():
            if emotion1 in cluster and emotion2 in cluster:
                return True
        
        return False
    
    async def _detect_patterns(self):
        """Detect recurring emotional patterns"""
        if len(self.events) < 10:
            return
        
        # Look at last 30 days of events
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_events = [e for e in self.events if e.timestamp > thirty_days_ago]
        
        if len(recent_events) < 5:
            return
        
        # Group by emotion
        emotion_groups = defaultdict(list)
        for event in recent_events:
            emotion_groups[event.emotion].append(event)
        
        # Check for patterns (emotions that occur multiple times)
        for emotion, events in emotion_groups.items():
            if len(events) >= 3:  # Pattern threshold
                # Calculate average duration
                avg_duration = sum((e.duration for e in events), timedelta()) / len(events)
                
                # Find common triggers
                triggers = [e.trigger for e in events if e.trigger]
                common_triggers = list(set(triggers))[:3]
                
                # Update or create pattern
                pattern_name = f"{emotion}_pattern"
                if pattern_name in self.patterns:
                    pattern = self.patterns[pattern_name]
                    pattern.frequency += 1
                    pattern.last_detected = datetime.now()
                    pattern.typical_duration = avg_duration
                    
                    # Update common triggers
                    for trigger in common_triggers:
                        if trigger not in pattern.common_triggers:
                            pattern.common_triggers.append(trigger)
                    
                    # Evolve wisdom stage
                    if pattern.frequency > 10:
                        pattern.growth_stage = WisdomLevel.TREE
                    elif pattern.frequency > 5:
                        pattern.growth_stage = WisdomLevel.FRUIT
                    elif pattern.frequency > 3:
                        pattern.growth_stage = WisdomLevel.FLOWER
                else:
                    # Create new pattern
                    self.patterns[pattern_name] = EmotionalPattern(
                        name=pattern_name,
                        emotions=[emotion],
                        frequency=1,
                        first_detected=events[0].timestamp,
                        last_detected=datetime.now(),
                        common_triggers=common_triggers,
                        typical_duration=avg_duration,
                        growth_stage=WisdomLevel.SEED
                    )
    
    async def _check_for_milestone(self, event: EmotionalEvent) -> Optional[GrowthMilestone]:
        """Check if this event represents a growth milestone"""
        
        # First time experiencing an emotion
        if not any(e.emotion == event.emotion for e in self.events[:-1]):
            return GrowthMilestone(
                date=event.timestamp,
                milestone_type='first_experience',
                description=f"First time experiencing {event.emotion}",
                emotion_involved=event.emotion,
                wisdom_gained=f"You've encountered {event.emotion} for the first time. Each new emotion is a doorway to deeper self-understanding.",
                celebration_suggestion="Take a moment to acknowledge this emotional expansion. Perhaps journal about what this new feeling teaches you."
            )
        
        # Breakthrough in pattern (different resolution than usual)
        if event.emotion in ['sadness', 'anger', 'fear']:
            similar_events = [e for e in self.events if e.emotion == event.emotion][-5:]
            if len(similar_events) >= 3:
                usual_resolution = max(set(e.resolution for e in similar_events if e.resolution), 
                                      key=lambda x: sum(1 for e in similar_events if e.resolution == x))
                if event.resolution and event.resolution != usual_resolution and \
                   self._is_healthier_resolution(event.resolution, usual_resolution):
                    return GrowthMilestone(
                        date=event.timestamp,
                        milestone_type='breakthrough',
                        description=f"New way of processing {event.emotion} discovered",
                        emotion_involved=event.emotion,
                        wisdom_gained=f"You've found a new, healthier way to work with {event.emotion}. This is real growth.",
                        celebration_suggestion="This deserves acknowledgment. Perhaps a small ritual to honor your emotional evolution."
                    )
        
        # Healing milestone (emotion intensity decreasing over time for same trigger)
        if event.trigger:
            trigger_events = [e for e in self.events if e.trigger == event.trigger]
            if len(trigger_events) >= 3:
                intensities = [e.intensity for e in trigger_events[-3:]]
                if intensities[0] > intensities[1] > intensities[2]:
                    return GrowthMilestone(
                        date=event.timestamp,
                        milestone_type='healing',
                        description=f"Healing progress on trigger: {event.trigger}",
                        emotion_involved=event.emotion,
                        wisdom_gained=f"What once strongly affected you now has less power. This is the fruit of emotional work.",
                        celebration_suggestion="This is significant healing. Consider what practice helped most and honor it."
                    )
        
        return None
    
    def _is_healthier_resolution(self, resolution1: str, resolution2: str) -> bool:
        """Determine if a resolution is healthier than another"""
        healthy_resolutions = ['acceptance', 'understanding', 'compassion', 'growth', 'peace']
        unhealthy_resolutions = ['suppression', 'denial', 'blame', 'withdrawal', 'acting_out']
        
        score1 = 1 if resolution1 in healthy_resolutions else -1 if resolution1 in unhealthy_resolutions else 0
        score2 = 1 if resolution2 in healthy_resolutions else -1 if resolution2 in unhealthy_resolutions else 0
        
        return score1 > score2
    
    def _harvest_wisdom(self, event: EmotionalEvent) -> Optional[str]:
        """Harvest wisdom from emotional events"""
        
        # Only harvest from significant events
        if event.impact_score < 0.6:
            return None
        
        # Wisdom based on emotion and context
        wisdom_map = {
            'sadness': "Sadness teaches us what we truly value. What have you lost that matters?",
            'anger': "Anger shows us our boundaries. What needs protection in your life?",
            'fear': "Fear points to where growth wants to happen. What courage is being called for?",
            'joy': "Joy reveals our true nature. How can you invite more of this?",
            'gratitude': "Gratitude transforms what we have into enough. What abundance do you already hold?",
            'frustration': "Frustration arises when reality doesn't match expectations. What expectations need releasing?",
            'peace': "Peace is always available beneath the surface of emotions. Can you rest here?",
            'love': "Love is your essence. Every other emotion is just love wearing different clothes."
        }
        
        base_wisdom = wisdom_map.get(event.emotion)
        
        # Enhance wisdom with context
        if base_wisdom and event.context:
            enhanced = f"{base_wisdom} In the context of {event.context}, perhaps there's a specific message for you."
            return enhanced
        
        return base_wisdom
    
    def _update_growth_metrics(self):
        """Update emotional growth metrics"""
        if len(self.events) < 10:
            return
        
        # Emotional IQ: ability to identify and understand emotions
        emotional_variety = len(set(e.emotion for e in self.events[-20:]))
        self.emotional_iq = min(1.0, emotional_variety / 15)
        
        # Wisdom quotient: insights harvested vs events
        wisdom_count = sum(1 for e in self.events if e.wisdom_harvested)
        self.wisdom_quotient = min(1.0, wisdom_count / max(1, len(self.events)) * 2)
        
        # Healing index: reduction in negative emotion intensity over time
        if len(self.events) >= 20:
            recent_neg = [e.intensity for e in self.events[-10:] 
                         if e.emotion in ['sadness', 'anger', 'fear', 'anxiety']]
            older_neg = [e.intensity for e in self.events[-20:-10] 
                        if e.emotion in ['sadness', 'anger', 'fear', 'anxiety']]
            
            if recent_neg and older_neg:
                recent_avg = np.mean(recent_neg)
                older_avg = np.mean(older_neg)
                if older_avg > 0:
                    self.healing_index = min(1.0, max(0, 1 - (recent_avg / older_avg)))
        
        # Spiritual alignment: presence of transcendent emotions
        transcendent = ['peace', 'awe', 'gratitude', 'love']
        transcendent_count = sum(1 for e in self.events[-20:] if e.emotion in transcendent)
        self.spiritual_alignment = min(1.0, transcendent_count / 10)
    
    def get_emotional_timeline(self, days: int = 30) -> Dict[str, Any]:
        """Get emotional timeline for visualization"""
        cutoff = datetime.now() - timedelta(days=days)
        relevant_events = [e for e in self.events if e.timestamp > cutoff]
        
        if not relevant_events:
            return {"status": "No data for this period"}
        
        timeline = {
            'dates': [e.timestamp.isoformat() for e in relevant_events],
            'emotions': [e.emotion for e in relevant_events],
            'intensities': [e.intensity for e in relevant_events],
            'seasons': [e.season.value for e in relevant_events],
            'impacts': [e.impact_score for e in relevant_events]
        }
        
        return timeline
    
    def get_wisdom_summary(self) -> Dict[str, Any]:
        """Get summary of wisdom gained"""
        return {
            'total_wisdom_harvested': len(self.wisdom_journal),
            'recent_wisdom': self.wisdom_journal[-5:] if self.wisdom_journal else [],
            'wisdom_quotient': self.wisdom_quotient,
            'growth_stages': {p.name: p.growth_stage.value for p in self.patterns.values()},
            'milestones': [
                {
                    'date': m.date.isoformat(),
                    'type': m.milestone_type,
                    'description': m.description,
                    'wisdom': m.wisdom_gained
                }
                for m in self.milestones[-5:]  # Last 5 milestones
            ]
        }
    
    def get_seasonal_insights(self) -> Dict[str, Any]:
        """Get insights based on emotional seasons"""
        current_season = self._determine_season(
            self.events[-1].emotion if self.events else 'neutral',
            self.events[-1].intensity if self.events else 0.5
        )
        
        season_guidance = {
            EmotionalSeason.SPRING: {
                'message': "You're in a season of new beginnings. What wants to grow?",
                'practice': "Plant seeds of intention. Water them with attention.",
                'activities': ["Start something new", "Learn", "Explore", "Dream"]
            },
            EmotionalSeason.SUMMER: {
                'message': "You're in a season of fullness and expression. Share your light.",
                'practice': "Celebrate and express gratitude for what's blooming.",
                'activities': ["Create", "Share", "Celebrate", "Connect"]
            },
            EmotionalSeason.AUTUMN: {
                'message': "You're in a season of letting go. What are you ready to release?",
                'practice': "Harvest lessons learned. Let go of what no longer serves.",
                'activities': ["Reflect", "Journal", "Release", "Simplify"]
            },
            EmotionalSeason.WINTER: {
                'message': "You're in a season of rest and inner work. The quiet holds wisdom.",
                'practice': "Rest deeply. Listen to the silence.",
                'activities': ["Rest", "Meditate", "Go inward", "Dream"]
            },
            EmotionalSeason.MONSOON: {
                'message': "You're in a season of intense release. Let it rain, let it flow.",
                'practice': "Allow emotions to move through you without resistance.",
                'activities': ["Cry if needed", "Move your body", "Write", "Purge"]
            },
            EmotionalSeason.INDIAN_SUMMER: {
                'message': "Unexpected warmth in difficulty. This too shall pass, but first, feel this gift.",
                'practice': "Savor this unexpected peace. It's a sign of your resilience.",
                'activities': ["Rest in the peace", "Trust the process", "Gather strength"]
            }
        }
        
        guidance = season_guidance.get(current_season, season_guidance[EmotionalSeason.SPRING])
        
        # Add seasonal patterns from history
        season_events = self.seasonal_patterns.get(current_season, [])
        
        return {
            'current_season': current_season.value,
            'season_message': guidance['message'],
            'suggested_practice': guidance['practice'],
            'suggested_activities': guidance['activities'],
            'seasonal_frequency': len(season_events),
            'typical_emotions': list(set(e.emotion for e in season_events[-10:]))[:5]
        }
    
    def get_growth_report(self) -> Dict[str, Any]:
        """Get comprehensive growth report"""
        return {
            'metrics': {
                'emotional_iq': self.emotional_iq,
                'wisdom_quotient': self.wisdom_quotient,
                'healing_index': self.healing_index,
                'spiritual_alignment': self.spiritual_alignment
            },
            'patterns_detected': len(self.patterns),
            'total_events': len(self.events),
            'milestones_achieved': len(self.milestones),
            'current_season': self.get_seasonal_insights(),
            'wisdom': self.get_wisdom_summary(),
            'recommendations': self._generate_growth_recommendations()
        }
    
    def _generate_growth_recommendations(self) -> List[str]:
        """Generate personalized growth recommendations"""
        recommendations = []
        
        if self.emotional_iq < 0.4:
            recommendations.append("Build emotional vocabulary by naming feelings throughout the day.")
        
        if self.wisdom_quotient < 0.3:
            recommendations.append("Journal about emotional experiences to harvest more wisdom.")
        
        if self.healing_index < 0.3:
            recommendations.append("Work with a specific trigger pattern through gentle exposure and self-compassion.")
        
        if self.spiritual_alignment < 0.3:
            recommendations.append("Practice gratitude and awe - notice beauty and wonder daily.")
        
        if not recommendations:
            recommendations.append("You're growing beautifully. Consider how you might share your wisdom with others.")
        
        return recommendations
    
    def get_trigger_patterns(self, trigger: str) -> Dict[str, Any]:
        """Get detailed analysis of a specific trigger"""
        trigger_events = [e for e in self.events if e.trigger == trigger]
        
        if not trigger_events:
            return {"status": "No data for this trigger"}
        
        emotions = [e.emotion for e in trigger_events]
        intensities = [e.intensity for e in trigger_events]
        
        return {
            'trigger': trigger,
            'frequency': len(trigger_events),
            'first_seen': min(e.timestamp for e in trigger_events),
            'last_seen': max(e.timestamp for e in trigger_events),
            'common_emotions': list(set(emotions)),
            'average_intensity': np.mean(intensities),
            'intensity_trend': 'decreasing' if len(intensities) >= 3 and intensities[-1] < intensities[0] else 'stable',
            'wisdom_harvested': [e.wisdom_harvested for e in trigger_events if e.wisdom_harvested]
        }
    
    def _save_history(self):
        """Save emotional history to disk"""
        try:
            data = {
                'events': [
                    {
                        'id': e.id,
                        'timestamp': e.timestamp.isoformat(),
                        'emotion': e.emotion,
                        'intensity': e.intensity,
                        'context': e.context,
                        'trigger': e.trigger,
                        'duration': e.duration.total_seconds(),
                        'resolution': e.resolution,
                        'insights_gained': e.insights_gained,
                        'wisdom_harvested': e.wisdom_harvested,
                        'season': e.season.value,
                        'impact_score': e.impact_score,
                        'related_events': e.related_events
                    }
                    for e in self.events
                ],
                'milestones': [
                    {
                        'date': m.date.isoformat(),
                        'type': m.milestone_type,
                        'description': m.description,
                        'emotion_involved': m.emotion_involved,
                        'wisdom_gained': m.wisdom_gained,
                        'celebration_suggestion': m.celebration_suggestion
                    }
                    for m in self.milestones
                ],
                'wisdom_journal': self.wisdom_journal,
                'metrics': {
                    'emotional_iq': self.emotional_iq,
                    'wisdom_quotient': self.wisdom_quotient,
                    'healing_index': self.healing_index,
                    'spiritual_alignment': self.spiritual_alignment
                }
            }
            
            filepath = self.storage_path / 'emotional_history.json'
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving emotional history: {e}")
    
    def _load_history(self):
        """Load emotional history from disk"""
        try:
            filepath = self.storage_path / 'emotional_history.json'
            if filepath.exists():
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Load events
                self.events = []
                for e_data in data.get('events', []):
                    event = EmotionalEvent(
                        id=e_data['id'],
                        timestamp=datetime.fromisoformat(e_data['timestamp']),
                        emotion=e_data['emotion'],
                        intensity=e_data['intensity'],
                        context=e_data['context'],
                        trigger=e_data.get('trigger'),
                        duration=timedelta(seconds=e_data.get('duration', 0)),
                        resolution=e_data.get('resolution'),
                        insights_gained=e_data.get('insights_gained', []),
                        wisdom_harvested=e_data.get('wisdom_harvested'),
                        season=EmotionalSeason(e_data.get('season', 'spring')),
                        impact_score=e_data.get('impact_score', 0.5),
                        related_events=e_data.get('related_events', [])
                    )
                    self.events.append(event)
                
                # Load milestones
                self.milestones = []
                for m_data in data.get('milestones', []):
                    milestone = GrowthMilestone(
                        date=datetime.fromisoformat(m_data['date']),
                        milestone_type=m_data['type'],
                        description=m_data['description'],
                        emotion_involved=m_data['emotion_involved'],
                        wisdom_gained=m_data['wisdom_gained'],
                        celebration_suggestion=m_data['celebration_suggestion']
                    )
                    self.milestones.append(milestone)
                
                # Load wisdom journal
                self.wisdom_journal = data.get('wisdom_journal', [])
                
                # Load metrics
                metrics = data.get('metrics', {})
                self.emotional_iq = metrics.get('emotional_iq', 0.5)
                self.wisdom_quotient = metrics.get('wisdom_quotient', 0.3)
                self.healing_index = metrics.get('healing_index', 0.5)
                self.spiritual_alignment = metrics.get('spiritual_alignment', 0.4)
                
        except Exception as e:
            print(f"Error loading emotional history: {e}")