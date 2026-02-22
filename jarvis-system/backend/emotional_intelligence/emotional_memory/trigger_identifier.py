"""
Trigger identification and pattern recognition with deep psychological insight.
Identifies emotional triggers and provides wisdom for working with them.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
import numpy as np
from enum import Enum
from collections import defaultdict
import re
from pathlib import Path
import json

class TriggerCategory(Enum):
    """Categories of emotional triggers"""
    EXTERNAL = "external"  # Outside events
    INTERNAL = "internal"  # Thoughts, memories
    RELATIONAL = "relational"  # Interactions with others
    ENVIRONMENTAL = "environmental"  # Physical surroundings
    TEMPORAL = "temporal"  # Time-based (anniversaries, time of day)
    DEVELOPMENTAL = "developmental"  # Growth-related challenges

class TriggerDepth(Enum):
    """How deep a trigger goes"""
    SURFACE = "surface"  # Mild, easily managed
    MODERATE = "moderate"  # Noticeable impact
    DEEP = "deep"  # Significant emotional response
    ROOT = "root"  # Core wound or pattern

@dataclass
class EmotionalTrigger:
    """An identified emotional trigger"""
    id: str
    name: str
    category: TriggerCategory
    depth: TriggerDepth
    first_detected: datetime
    last_triggered: datetime
    frequency: int
    typical_emotions: List[str]
    typical_intensity: float
    context_patterns: List[str]
    warning_signs: List[str]  # Early indicators trigger is activating
    coping_strategies: List[str]  # What has helped
    growth_opportunities: List[str]  # What this trigger teaches
    healing_progress: float  # 0-1 how much healing has occurred
    related_triggers: List[str] = field(default_factory=list)  # IDs of related triggers
    wisdom_harvested: List[str] = field(default_factory=list)

@dataclass
class TriggerEpisode:
    """A specific instance of a trigger being activated"""
    id: str
    trigger_id: str
    timestamp: datetime
    intensity: float
    emotional_response: str
    context: str
    duration: timedelta
    coping_used: Optional[str] = None
    resolution: Optional[str] = None
    insight_gained: Optional[str] = None
    healing_opportunity: bool = False

class TriggerIdentifier:
    """
    Enhanced trigger identification with deep pattern recognition.
    Helps user understand and work with their emotional triggers.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else Path.home() / '.jarvis' / 'triggers'
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Core data
        self.triggers: Dict[str, EmotionalTrigger] = {}
        self.episodes: List[TriggerEpisode] = []
        
        # Pattern recognition
        self.context_patterns: Dict[str, List[str]] = defaultdict(list)
        self.temporal_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self.emotion_trigger_map: Dict[str, List[str]] = defaultdict(list)
        
        # Learning metrics
        self.trigger_awareness: float = 0.3  # How aware user is of triggers
        self.healing_progress: float = 0.0  # Overall healing progress
        self.pattern_recognition: float = 0.4  # Ability to recognize patterns
        
        # Current state
        self.currently_triggered: Set[str] = set()
        self.active_episodes: Dict[str, TriggerEpisode] = {}
        
        # Load existing data
        self._load_data()
    
    async def identify_trigger(self, 
                              emotion: str,
                              intensity: float,
                              context: str,
                              timestamp: Optional[datetime] = None) -> Optional[EmotionalTrigger]:
        """Identify if current emotional state matches any known triggers"""
        
        if not timestamp:
            timestamp = datetime.now()
        
        # Check against known triggers
        for trigger in self.triggers.values():
            # Check context patterns
            for pattern in trigger.context_patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    # This looks like a trigger activation
                    await self.record_trigger_episode(
                        trigger.id,
                        intensity,
                        emotion,
                        context,
                        timestamp
                    )
                    return trigger
            
            # Check emotional pattern
            if emotion in trigger.typical_emotions and intensity > 0.6:
                # Possible trigger, but need context
                if self._context_similar_to_trigger(context, trigger):
                    await self.record_trigger_episode(
                        trigger.id,
                        intensity,
                        emotion,
                        context,
                        timestamp
                    )
                    return trigger
        
        # No known trigger found
        return None
    
    def _context_similar_to_trigger(self, context: str, trigger: EmotionalTrigger) -> bool:
        """Check if context is similar to known trigger patterns"""
        context_lower = context.lower()
        
        for pattern in trigger.context_patterns:
            # Simple word overlap for now
            pattern_words = set(pattern.lower().split())
            context_words = set(context_lower.split())
            
            if pattern_words and context_words:
                overlap = pattern_words.intersection(context_words)
                if len(overlap) / len(pattern_words) > 0.3:  # 30% overlap
                    return True
        
        return False
    
    async def record_trigger_episode(self,
                                    trigger_id: str,
                                    intensity: float,
                                    emotional_response: str,
                                    context: str,
                                    timestamp: datetime) -> TriggerEpisode:
        """Record an episode of a trigger being activated"""
        
        episode = TriggerEpisode(
            id=f"ep_{timestamp.timestamp()}",
            trigger_id=trigger_id,
            timestamp=timestamp,
            intensity=intensity,
            emotional_response=emotional_response,
            context=context,
            duration=timedelta(minutes=0)  # Will update when resolved
        )
        
        self.episodes.append(episode)
        self.active_episodes[episode.id] = episode
        
        # Update trigger data
        trigger = self.triggers.get(trigger_id)
        if trigger:
            trigger.last_triggered = timestamp
            trigger.frequency += 1
            
            # Update typical intensity (moving average)
            trigger.typical_intensity = (
                trigger.typical_intensity * (trigger.frequency - 1) + intensity
            ) / trigger.frequency
            
            # Add to temporal patterns
            hour = timestamp.hour
            self.temporal_patterns[f"hour_{hour}"].append(timestamp)
        
        self.currently_triggered.add(trigger_id)
        
        # Save data
        self._save_data()
        
        return episode
    
    async def resolve_trigger_episode(self,
                                     episode_id: str,
                                     resolution: str,
                                     coping_used: Optional[str] = None,
                                     insight_gained: Optional[str] = None):
        """Mark a trigger episode as resolved"""
        
        episode = self.active_episodes.get(episode_id)
        if not episode:
            # Try to find in episodes list
            episode = next((e for e in self.episodes if e.id == episode_id), None)
        
        if episode:
            episode.duration = datetime.now() - episode.timestamp
            episode.resolution = resolution
            episode.coping_used = coping_used
            episode.insight_gained = insight_gained
            
            # Check if this was a healing opportunity
            if coping_used and resolution in ['peaceful', 'understood', 'accepted']:
                episode.healing_opportunity = True
                
                # Update trigger healing progress
                trigger = self.triggers.get(episode.trigger_id)
                if trigger:
                    trigger.healing_progress = min(1.0, trigger.healing_progress + 0.05)
                    
                    if coping_used and coping_used not in trigger.coping_strategies:
                        trigger.coping_strategies.append(coping_used)
                    
                    if insight_gained and insight_gained not in trigger.wisdom_harvested:
                        trigger.wisdom_harvested.append(insight_gained)
            
            # Remove from active
            if episode_id in self.active_episodes:
                del self.active_episodes[episode_id]
            
            self.currently_triggered.discard(episode.trigger_id)
            
            # Update overall healing progress
            self._update_healing_progress()
            
            # Save data
            self._save_data()
    
    async def discover_new_trigger(self,
                                  emotion: str,
                                  intensity: float,
                                  context: str,
                                  pattern_frequency: int = 2) -> Optional[EmotionalTrigger]:
        """Discover a potential new trigger based on patterns"""
        
        # Look for patterns in recent episodes
        if len(self.episodes) < 5:
            return None
        
        # Group episodes by context similarity
        context_groups = defaultdict(list)
        for episode in self.episodes[-20:]:  # Last 20 episodes
            # Create context signature
            words = set(episode.context.lower().split())
            signature = ' '.join(sorted(words)[:5])  # Use top 5 words as signature
            context_groups[signature].append(episode)
        
        # Find patterns
        for signature, episodes in context_groups.items():
            if len(episodes) >= pattern_frequency:
                # This looks like a pattern
                common_emotions = list(set(e.emotional_response for e in episodes))
                avg_intensity = np.mean([e.intensity for e in episodes])
                
                # Check if this is already a known trigger
                is_new = True
                for trigger in self.triggers.values():
                    if any(self._context_similar_to_trigger(e.context, trigger) for e in episodes):
                        is_new = False
                        break
                
                if is_new and common_emotions:
                    # Create new trigger
                    trigger = EmotionalTrigger(
                        id=f"trig_{datetime.now().timestamp()}",
                        name=f"Trigger related to {common_emotions[0]}",
                        category=self._categorize_trigger(context),
                        depth=self._determine_depth(avg_intensity, len(episodes)),
                        first_detected=min(e.timestamp for e in episodes),
                        last_triggered=max(e.timestamp for e in episodes),
                        frequency=len(episodes),
                        typical_emotions=common_emotions[:3],
                        typical_intensity=avg_intensity,
                        context_patterns=[signature],
                        warning_signs=self._identify_warning_signs(episodes),
                        coping_strategies=[],
                        growth_opportunities=self._identify_growth_opportunities(common_emotions),
                        healing_progress=0.0
                    )
                    
                    self.triggers[trigger.id] = trigger
                    
                    # Map emotions to trigger
                    for emotion in common_emotions:
                        self.emotion_trigger_map[emotion].append(trigger.id)
                    
                    # Save data
                    self._save_data()
                    
                    return trigger
        
        return None
    
    def _categorize_trigger(self, context: str) -> TriggerCategory:
        """Categorize a trigger based on context"""
        context_lower = context.lower()
        
        # Check for relational keywords
        relational = ['they', 'them', 'she', 'he', 'friend', 'family', 'partner', 'boss', 'colleague']
        if any(word in context_lower for word in relational):
            return TriggerCategory.RELATIONAL
        
        # Check for environmental keywords
        environmental = ['room', 'place', 'home', 'office', 'space', 'weather', 'noise', 'light']
        if any(word in context_lower for word in environmental):
            return TriggerCategory.ENVIRONMENTAL
        
        # Check for internal keywords
        internal = ['think', 'remember', 'recall', 'memory', 'feel', 'thought']
        if any(word in context_lower for word in internal):
            return TriggerCategory.INTERNAL
        
        # Check for temporal keywords
        temporal = ['today', 'yesterday', 'anniversary', 'year', 'month', 'time']
        if any(word in context_lower for word in temporal):
            return TriggerCategory.TEMPORAL
        
        # Default to external
        return TriggerCategory.EXTERNAL
    
    def _determine_depth(self, intensity: float, frequency: int) -> TriggerDepth:
        """Determine trigger depth based on intensity and frequency"""
        if intensity > 0.8 and frequency > 5:
            return TriggerDepth.ROOT
        elif intensity > 0.6 and frequency > 3:
            return TriggerDepth.DEEP
        elif intensity > 0.4:
            return TriggerDepth.MODERATE
        else:
            return TriggerDepth.SURFACE
    
    def _identify_warning_signs(self, episodes: List[TriggerEpisode]) -> List[str]:
        """Identify early warning signs from episodes"""
        warning_signs = []
        
        # Look at contexts just before trigger
        for episode in episodes:
            context = episode.context.lower()
            
            # Common warning patterns
            if 'just' in context or 'suddenly' in context:
                warning_signs.append("Sudden onset - watch for abrupt emotional shifts")
            
            if 'tired' in context or 'exhausted' in context:
                warning_signs.append("Physical fatigue often precedes this trigger")
            
            if 'stress' in context or 'overwhelm' in context:
                warning_signs.append("General stress makes this trigger more likely")
        
        return list(set(warning_signs))[:3]  # Unique signs, max 3
    
    def _identify_growth_opportunities(self, emotions: List[str]) -> List[str]:
        """Identify growth opportunities from trigger emotions"""
        growth_map = {
            'anger': "This trigger offers practice in setting boundaries and self-advocacy",
            'fear': "This trigger invites you to build courage and trust",
            'sadness': "This trigger teaches about loss and the value of what you cherish",
            'anxiety': "This trigger is an opportunity to practice grounding and presence",
            'frustration': "This trigger develops patience and acceptance",
            'shame': "This trigger opens the door to self-compassion"
        }
        
        opportunities = []
        for emotion in emotions:
            if emotion in growth_map:
                opportunities.append(growth_map[emotion])
        
        return opportunities[:3]  # Max 3
    
    def _update_healing_progress(self):
        """Update overall healing progress"""
        if not self.triggers:
            return
        
        # Average healing progress across triggers
        total_progress = sum(t.healing_progress for t in self.triggers.values())
        self.healing_progress = total_progress / len(self.triggers)
        
        # Update pattern recognition (based on identified patterns)
        if len(self.triggers) > 0:
            self.pattern_recognition = min(1.0, len(self.triggers) / 20)
        
        # Update trigger awareness (based on successful identification)
        if len(self.episodes) > 0:
            identified = sum(1 for e in self.episodes if e.trigger_id in self.triggers)
            self.trigger_awareness = identified / len(self.episodes)
    
    def get_trigger_profile(self, trigger_id: str) -> Dict[str, Any]:
        """Get detailed profile of a specific trigger"""
        
        trigger = self.triggers.get(trigger_id)
        if not trigger:
            return {"error": "Trigger not found"}
        
        # Get related episodes
        episodes = [e for e in self.episodes if e.trigger_id == trigger_id]
        
        # Calculate statistics
        intensities = [e.intensity for e in episodes]
        durations = [e.duration.total_seconds() / 60 for e in episodes if e.duration]
        
        # Find best coping strategies
        coping_success = defaultdict(list)
        for e in episodes:
            if e.coping_used and e.resolution:
                success = 1 if e.resolution in ['peaceful', 'understood', 'accepted'] else 0
                coping_success[e.coping_used].append(success)
        
        best_coping = []
        for coping, outcomes in coping_success.items():
            success_rate = sum(outcomes) / len(outcomes)
            best_coping.append((coping, success_rate))
        
        best_coping.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'id': trigger.id,
            'name': trigger.name,
            'category': trigger.category.value,
            'depth': trigger.depth.value,
            'first_detected': trigger.first_detected.isoformat(),
            'last_triggered': trigger.last_triggered.isoformat(),
            'frequency': trigger.frequency,
            'typical_emotions': trigger.typical_emotions,
            'average_intensity': trigger.typical_intensity,
            'intensity_trend': self._calculate_trend(intensities),
            'average_duration': np.mean(durations) if durations else 0,
            'context_patterns': trigger.context_patterns,
            'warning_signs': trigger.warning_signs,
            'coping_strategies': [c for c, _ in best_coping[:3]],
            'growth_opportunities': trigger.growth_opportunities,
            'healing_progress': trigger.healing_progress,
            'wisdom_harvested': trigger.wisdom_harvested
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend in a list of values"""
        if len(values) < 3:
            return "insufficient_data"
        
        recent = np.mean(values[-3:])
        earlier = np.mean(values[:3])
        
        if recent < earlier * 0.8:
            return "improving"
        elif recent > earlier * 1.2:
            return "worsening"
        else:
            return "stable"
    
    def get_active_triggers(self) -> List[Dict[str, Any]]:
        """Get currently active triggers"""
        active = []
        
        for episode in self.active_episodes.values():
            trigger = self.triggers.get(episode.trigger_id)
            if trigger:
                active.append({
                    'episode_id': episode.id,
                    'trigger_name': trigger.name,
                    'emotion': episode.emotional_response,
                    'intensity': episode.intensity,
                    'duration_minutes': (datetime.now() - episode.timestamp).total_seconds() / 60,
                    'context': episode.context,
                    'suggested_coping': trigger.coping_strategies[:2]
                })
        
        return active
    
    def get_trigger_summary(self) -> Dict[str, Any]:
        """Get summary of all triggers"""
        if not self.triggers:
            return {"status": "No triggers identified yet"}
        
        # Categorize by depth
        depth_counts = defaultdict(int)
        for trigger in self.triggers.values():
            depth_counts[trigger.depth.value] += 1
        
        # Most common emotions in triggers
        all_emotions = []
        for trigger in self.triggers.values():
            all_emotions.extend(trigger.typical_emotions)
        
        emotion_counts = defaultdict(int)
        for emotion in all_emotions:
            emotion_counts[emotion] += 1
        
        top_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Most frequent triggers
        frequent_triggers = sorted(
            [(t.name, t.frequency) for t in self.triggers.values()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Healing progress
        healing_by_depth = {}
        for depth in TriggerDepth:
            depth_triggers = [t for t in self.triggers.values() if t.depth == depth]
            if depth_triggers:
                avg_healing = np.mean([t.healing_progress for t in depth_triggers])
                healing_by_depth[depth.value] = avg_healing
        
        return {
            'total_triggers': len(self.triggers),
            'by_depth': dict(depth_counts),
            'most_common_emotions': top_emotions,
            'most_frequent_triggers': frequent_triggers,
            'healing_progress_by_depth': healing_by_depth,
            'overall_healing': self.healing_progress,
            'trigger_awareness': self.trigger_awareness,
            'pattern_recognition': self.pattern_recognition,
            'currently_active': len(self.active_episodes)
        }
    
    def get_healing_suggestions(self, trigger_id: Optional[str] = None) -> List[str]:
        """Get suggestions for working with triggers"""
        
        if trigger_id:
            trigger = self.triggers.get(trigger_id)
            if not trigger:
                return []
            
            suggestions = []
            
            # Depth-based suggestions
            if trigger.depth == TriggerDepth.ROOT:
                suggestions.append("Root triggers often benefit from gentle, consistent attention over time.")
                suggestions.append("Consider working with a therapist if this feels overwhelming.")
            
            elif trigger.depth == TriggerDepth.DEEP:
                suggestions.append("These triggers respond well to gradual exposure and self-compassion.")
                suggestions.append("Journaling about this trigger can reveal its hidden messages.")
            
            # Emotion-based suggestions
            for emotion in trigger.typical_emotions:
                if emotion == 'anger':
                                        suggestions.append("Channel anger into physical activity or creative expression. Let it move through you.")
                elif emotion == 'fear':
                    suggestions.append("When fear arises, place a hand on your heart and breathe. You are safe in this moment.")
                elif emotion == 'sadness':
                    suggestions.append("Allow sadness to flow. Tears are healing waters for the soul.")
                elif emotion == 'anxiety':
                    suggestions.append("Anxiety lives in the future. Gently bring yourself back to this breath, this moment.")
            
            # Wisdom-based suggestions
            if trigger.wisdom_harvested:
                suggestions.append(f"Remember: {trigger.wisdom_harvested[-1]}")
            
            return suggestions[:5]
        
        else:
            # General healing suggestions
            return [
                "Triggers are not weaknesses - they are doorways to deeper self-understanding.",
                "Each time you face a trigger with awareness, you heal a little more.",
                "Be patient with yourself. Healing is not linear, but every step counts.",
                "Notice your triggers without judgment. They are simply old wounds asking for attention.",
                "The goal is not to eliminate triggers, but to change your relationship with them."
            ]
    
    def get_temporal_patterns(self) -> Dict[str, Any]:
        """Get time-based patterns in trigger activation"""
        if not self.temporal_patterns:
            return {"status": "Insufficient data"}
        
        # Analyze by hour
        hour_patterns = {}
        for hour_key, timestamps in self.temporal_patterns.items():
            if timestamps:
                hour = hour_key.replace('hour_', '')
                hour_patterns[hour] = len(timestamps)
        
        # Analyze by day of week
        day_patterns = defaultdict(int)
        for episode in self.episodes:
            day = episode.timestamp.strftime('%A')
            day_patterns[day] += 1
        
        # Find peak times
        peak_hour = max(hour_patterns.items(), key=lambda x: x[1]) if hour_patterns else None
        peak_day = max(day_patterns.items(), key=lambda x: x[1]) if day_patterns else None
        
        return {
            'by_hour': hour_patterns,
            'by_day': dict(day_patterns),
            'peak_hour': f"{peak_hour[0]}:00" if peak_hour else None,
            'peak_day': peak_day[0] if peak_day else None,
            'quietest_hour': min(hour_patterns.items(), key=lambda x: x[1])[0] if hour_patterns else None,
            'quietest_day': min(day_patterns.items(), key=lambda x: x[1])[0] if day_patterns else None
        }
    
    def get_trigger_relationships(self) -> List[Dict[str, Any]]:
        """Identify relationships between different triggers"""
        relationships = []
        
        # Find triggers that often occur together
        episode_clusters = defaultdict(list)
        for episode in self.episodes:
            # Group episodes that happen close in time
            time_key = episode.timestamp.strftime('%Y-%m-%d-%H')
            episode_clusters[time_key].append(episode.trigger_id)
        
        # Find co-occurring triggers
        co_occurrence = defaultdict(int)
        for trigger_ids in episode_clusters.values():
            unique_triggers = list(set(trigger_ids))
            if len(unique_triggers) > 1:
                for i in range(len(unique_triggers)):
                    for j in range(i+1, len(unique_triggers)):
                        pair = tuple(sorted([unique_triggers[i], unique_triggers[j]]))
                        co_occurrence[pair] += 1
        
        # Convert to relationship descriptions
        for (trigger_id1, trigger_id2), count in co_occurrence.items():
            if count > 2:  # Significant co-occurrence
                trigger1 = self.triggers.get(trigger_id1)
                trigger2 = self.triggers.get(trigger_id2)
                if trigger1 and trigger2:
                    relationships.append({
                        'trigger1': trigger1.name,
                        'trigger2': trigger2.name,
                        'co_occurrence_count': count,
                        'relationship_type': 'linked' if count > 5 else 'occasional',
                        'insight': f"These triggers often appear together. Healing one may help the other."
                    })
        
        return relationships
    
    def get_wisdom_from_triggers(self) -> List[str]:
        """Harvest wisdom from all trigger experiences"""
        wisdom = []
        
        # Collect all insights
        all_insights = []
        for episode in self.episodes:
            if episode.insight_gained:
                all_insights.append(episode.insight_gained)
        
        for trigger in self.triggers.values():
            if trigger.wisdom_harvested:
                all_insights.extend(trigger.wisdom_harvested)
        
        # Deduplicate and curate
        seen = set()
        for insight in all_insights:
            if insight and insight not in seen:
                wisdom.append(insight)
                seen.add(insight)
        
        return wisdom[-10:]  # Last 10 unique insights
    
    def get_trigger_readiness(self, trigger_id: str) -> Dict[str, Any]:
        """Assess readiness to work with a specific trigger"""
        trigger = self.triggers.get(trigger_id)
        if not trigger:
            return {"error": "Trigger not found"}
        
        episodes = [e for e in self.episodes if e.trigger_id == trigger_id]
        
        if not episodes:
            return {"readiness": "unknown"}
        
        # Calculate readiness factors
        recent_episodes = [e for e in episodes if e.timestamp > datetime.now() - timedelta(days=30)]
        recent_intensity = np.mean([e.intensity for e in recent_episodes]) if recent_episodes else 0
        
        healing_momentum = trigger.healing_progress
        recent_success = sum(1 for e in recent_episodes if e.healing_opportunity) / len(recent_episodes) if recent_episodes else 0
        
        # Overall readiness score (0-1)
        readiness_score = (
            healing_momentum * 0.4 +
            recent_success * 0.3 +
            (1 - recent_intensity) * 0.3
        )
        
        # Determine readiness level
        if readiness_score > 0.7:
            level = "ready_for_deep_work"
            message = "You're in a good place to work deeply with this trigger."
        elif readiness_score > 0.4:
            level = "gentle_exploration"
            message = "You can begin gently exploring this trigger with self-compassion."
        else:
            level = "rest_and_support"
            message = "This trigger needs gentle care. Focus on self-support right now."
        
        return {
            'trigger_name': trigger.name,
            'readiness_level': level,
            'readiness_score': readiness_score,
            'message': message,
            'factors': {
                'healing_progress': trigger.healing_progress,
                'recent_success_rate': recent_success,
                'recent_intensity': recent_intensity
            },
            'suggested_approach': self._get_approach_for_level(level, trigger)
        }
    
    def _get_approach_for_level(self, level: str, trigger: EmotionalTrigger) -> List[str]:
        """Get suggested approach based on readiness level"""
        
        if level == "ready_for_deep_work":
            return [
                f"Journal about what {trigger.name} teaches you",
                "Practice gentle exposure in safe contexts",
                "Share your insights with someone you trust",
                f"Create a ritual to honor your healing with this trigger"
            ]
        elif level == "gentle_exploration":
            return [
                f"Notice when {trigger.name} arises without judgment",
                "Practice grounding techniques when triggered",
                f"Write down one small insight about this trigger",
                "Be extra gentle with yourself around this trigger"
            ]
        else:
            return [
                f"Give yourself permission to rest when {trigger.name} appears",
                "Reach out for support if needed",
                "Focus on basic self-care and stability",
                "This trigger needs time - be patient with yourself"
            ]
    
    def _save_data(self):
        """Save trigger data to disk"""
        try:
            data = {
                'triggers': [
                    {
                        'id': t.id,
                        'name': t.name,
                        'category': t.category.value,
                        'depth': t.depth.value,
                        'first_detected': t.first_detected.isoformat(),
                        'last_triggered': t.last_triggered.isoformat(),
                        'frequency': t.frequency,
                        'typical_emotions': t.typical_emotions,
                        'typical_intensity': t.typical_intensity,
                        'context_patterns': t.context_patterns,
                        'warning_signs': t.warning_signs,
                        'coping_strategies': t.coping_strategies,
                        'growth_opportunities': t.growth_opportunities,
                        'healing_progress': t.healing_progress,
                        'related_triggers': t.related_triggers,
                        'wisdom_harvested': t.wisdom_harvested
                    }
                    for t in self.triggers.values()
                ],
                'episodes': [
                    {
                        'id': e.id,
                        'trigger_id': e.trigger_id,
                        'timestamp': e.timestamp.isoformat(),
                        'intensity': e.intensity,
                        'emotional_response': e.emotional_response,
                        'context': e.context,
                        'duration': e.duration.total_seconds(),
                        'coping_used': e.coping_used,
                        'resolution': e.resolution,
                        'insight_gained': e.insight_gained,
                        'healing_opportunity': e.healing_opportunity
                    }
                    for e in self.episodes
                ],
                'metrics': {
                    'trigger_awareness': self.trigger_awareness,
                    'healing_progress': self.healing_progress,
                    'pattern_recognition': self.pattern_recognition
                }
            }
            
            filepath = self.storage_path / 'triggers.json'
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving trigger data: {e}")
    
    def _load_data(self):
        """Load trigger data from disk"""
        try:
            filepath = self.storage_path / 'triggers.json'
            if filepath.exists():
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Load triggers
                self.triggers = {}
                for t_data in data.get('triggers', []):
                    trigger = EmotionalTrigger(
                        id=t_data['id'],
                        name=t_data['name'],
                        category=TriggerCategory(t_data['category']),
                        depth=TriggerDepth(t_data['depth']),
                        first_detected=datetime.fromisoformat(t_data['first_detected']),
                        last_triggered=datetime.fromisoformat(t_data['last_triggered']),
                        frequency=t_data['frequency'],
                        typical_emotions=t_data['typical_emotions'],
                        typical_intensity=t_data['typical_intensity'],
                        context_patterns=t_data['context_patterns'],
                        warning_signs=t_data['warning_signs'],
                        coping_strategies=t_data['coping_strategies'],
                        growth_opportunities=t_data['growth_opportunities'],
                        healing_progress=t_data['healing_progress'],
                        related_triggers=t_data.get('related_triggers', []),
                        wisdom_harvested=t_data.get('wisdom_harvested', [])
                    )
                    self.triggers[trigger.id] = trigger
                
                # Load episodes
                self.episodes = []
                for e_data in data.get('episodes', []):
                    episode = TriggerEpisode(
                        id=e_data['id'],
                        trigger_id=e_data['trigger_id'],
                        timestamp=datetime.fromisoformat(e_data['timestamp']),
                        intensity=e_data['intensity'],
                        emotional_response=e_data['emotional_response'],
                        context=e_data['context'],
                        duration=timedelta(seconds=e_data.get('duration', 0)),
                        coping_used=e_data.get('coping_used'),
                        resolution=e_data.get('resolution'),
                        insight_gained=e_data.get('insight_gained'),
                        healing_opportunity=e_data.get('healing_opportunity', False)
                    )
                    self.episodes.append(episode)
                
                # Load metrics
                metrics = data.get('metrics', {})
                self.trigger_awareness = metrics.get('trigger_awareness', 0.3)
                self.healing_progress = metrics.get('healing_progress', 0.0)
                self.pattern_recognition = metrics.get('pattern_recognition', 0.4)
                
        except Exception as e:
            print(f"Error loading trigger data: {e}")