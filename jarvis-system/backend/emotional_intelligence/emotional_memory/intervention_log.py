"""
Intervention logging and effectiveness tracking with deep learning.
Tracks how JARVIS responds to emotional states and learns what works best.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
from enum import Enum
from collections import defaultdict
import json
from pathlib import Path

class InterventionType(Enum):
    """Types of emotional interventions"""
    IMMEDIATE_SOOTHING = "immediate_soothing"
    DEEP_LISTENING = "deep_listening"
    WISDOM_SHARING = "wisdom_sharing"
    MEDITATION_GUIDANCE = "meditation_guidance"
    GROWTH_ENCOURAGEMENT = "growth_encouragement"
    GENTLE_CHALLENGE = "gentle_challenge"
    CELEBRATION = "celebration"
    GRATITUDE_PRACTICE = "gratitude_practice"
    REFLECTION_PROMPT = "reflection_prompt"
    SACRED_SILENCE = "sacred_silence"

class InterventionEffectiveness(Enum):
    """How effective an intervention was"""
    TRANSFORMATIVE = "transformative"  # Profound positive change
    HELPFUL = "helpful"  # Clearly beneficial
    SUBTLE = "subtle"  # Slight positive effect
    NEUTRAL = "neutral"  # No noticeable effect
    DISRUPTIVE = "disruptive"  # Made things worse

@dataclass
class Intervention:
    """Record of an emotional intervention"""
    id: str
    timestamp: datetime
    intervention_type: InterventionType
    emotional_context: Dict[str, Any]  # State when intervention was given
    response_text: str
    user_reaction: Optional[str] = None  # How user responded
    effectiveness: Optional[InterventionEffectiveness] = None
    follow_up_needed: bool = False
    wisdom_shared: Optional[str] = None
    user_feedback: Optional[str] = None
    learning_notes: List[str] = field(default_factory=list)

@dataclass
class InterventionPattern:
    """Pattern of what interventions work best in what situations"""
    emotion: str
    intensity_range: Tuple[float, float]
    most_effective_type: InterventionType
    success_rate: float
    times_used: int
    average_user_rating: float
    common_outcomes: List[str]
    timing_preference: str  # 'immediate', 'delayed', 'after_processing'

class InterventionLog:
    """
    Enhanced intervention logging with effectiveness tracking and learning.
    Learns what emotional support works best for each user.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else Path.home() / '.jarvis' / 'interventions'
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Core data
        self.interventions: List[Intervention] = []
        self.patterns: Dict[str, InterventionPattern] = {}
        self.effectiveness_history: List[Dict] = []
        
        # Learning metrics
        self.intervention_success_rate: float = 0.7
        self.user_trust_level: float = 0.8
        self.timing_precision: float = 0.6
        self.wisdom_impact: float = 0.5
        
        # Personalization data
        self.user_preferences: Dict[InterventionType, float] = defaultdict(float)
        self.sensitive_topics: List[str] = []
        self.successful_phrases: List[str] = []
        
        # Tracking
        self.daily_interventions: int = 0
        self.last_intervention_date: Optional[datetime] = None
        
        # Load existing log
        self._load_log()
    
    async def log_intervention(self, 
                              intervention_type: InterventionType,
                              emotional_context: Dict[str, Any],
                              response_text: str,
                              wisdom_shared: Optional[str] = None) -> Intervention:
        """Log a new intervention"""
        
        intervention = Intervention(
            id=f"int_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            intervention_type=intervention_type,
            emotional_context=emotional_context,
            response_text=response_text,
            wisdom_shared=wisdom_shared
        )
        
        self.interventions.append(intervention)
        self.daily_interventions += 1
        self.last_intervention_date = datetime.now()
        
        # Update user preferences (default assumption - will be refined with feedback)
        self.user_preferences[intervention_type] += 0.1
        
        # Save log
        self._save_log()
        
        return intervention
    
    async def record_outcome(self, 
                           intervention_id: str,
                           user_reaction: str,
                           effectiveness: InterventionEffectiveness,
                           user_feedback: Optional[str] = None) -> Dict[str, Any]:
        """Record the outcome of an intervention"""
        
        # Find intervention
        intervention = next((i for i in self.interventions if i.id == intervention_id), None)
        if not intervention:
            return {"error": "Intervention not found"}
        
        # Update intervention
        intervention.user_reaction = user_reaction
        intervention.effectiveness = effectiveness
        intervention.user_feedback = user_feedback
        
        # Record in effectiveness history
        self.effectiveness_history.append({
            'timestamp': datetime.now(),
            'intervention_id': intervention_id,
            'type': intervention.intervention_type.value,
            'effectiveness': effectiveness.value,
            'emotional_context': intervention.emotional_context.get('current_emotion'),
            'user_reaction': user_reaction
        })
        
        # Learn from outcome
        await self._learn_from_outcome(intervention, effectiveness, user_reaction)
        
        # Update success rate
        self._update_success_rate()
        
        # Save log
        self._save_log()
        
        # Generate insights
        insights = self._generate_outcome_insights(intervention, effectiveness)
        
        return {
            'recorded': True,
            'updated_success_rate': self.intervention_success_rate,
            'insights': insights,
            'learning_notes': intervention.learning_notes
        }
    
    async def _learn_from_outcome(self, 
                                 intervention: Intervention,
                                 effectiveness: InterventionEffectiveness,
                                 user_reaction: str):
        """Learn from intervention outcomes to improve future responses"""
        
        emotion = intervention.emotional_context.get('current_emotion')
        intensity = intervention.emotional_context.get('current_intensity', 0.5)
        intervention_type = intervention.intervention_type
        
        # Update patterns
        pattern_key = f"{emotion}_{int(intensity*10)}"
        
        if pattern_key not in self.patterns:
            self.patterns[pattern_key] = InterventionPattern(
                emotion=emotion,
                intensity_range=(max(0, intensity-0.1), min(1.0, intensity+0.1)),
                most_effective_type=intervention_type,
                success_rate=0.5,
                times_used=0,
                average_user_rating=0.5,
                common_outcomes=[],
                timing_preference='immediate'
            )
        
        pattern = self.patterns[pattern_key]
        pattern.times_used += 1
        
        # Update effectiveness based on outcome
        effectiveness_score = {
            InterventionEffectiveness.TRANSFORMATIVE: 1.0,
            InterventionEffectiveness.HELPFUL: 0.8,
            InterventionEffectiveness.SUBTLE: 0.5,
            InterventionEffectiveness.NEUTRAL: 0.3,
            InterventionEffectiveness.DISRUPTIVE: 0.0
        }.get(effectiveness, 0.5)
        
        # Update pattern success rate (moving average)
        pattern.success_rate = (pattern.success_rate * (pattern.times_used - 1) + effectiveness_score) / pattern.times_used
        
        # Update most effective type if this one is working better
        if effectiveness_score > 0.7 and pattern.times_used > 3:
            pattern.most_effective_type = intervention_type
        
        # Record common outcomes
        if len(pattern.common_outcomes) < 10:
            pattern.common_outcomes.append(effectiveness.value)
        else:
            pattern.common_outcomes = pattern.common_outcomes[1:] + [effectiveness.value]
        
        # Update user preferences
        self.user_preferences[intervention_type] = (
            self.user_preferences[intervention_type] * 0.8 + effectiveness_score * 0.2
        )
        
        # Learn successful phrases
        if effectiveness in [InterventionEffectiveness.TRANSFORMATIVE, InterventionEffectiveness.HELPFUL]:
            # Extract key phrases (simplified - in production would use NLP)
            words = intervention.response_text.split()
            key_phrases = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
            for phrase in key_phrases[:3]:
                if phrase not in self.successful_phrases:
                    self.successful_phrases.append(phrase)
        
        # Add learning note
        learning_note = f"Learned: {intervention_type.value} was {effectiveness.value} for {emotion} at intensity {intensity}"
        intervention.learning_notes.append(learning_note)
        
        # Check for sensitive topics
        if effectiveness == InterventionEffectiveness.DISRUPTIVE:
            # This topic might be sensitive
            context = intervention.emotional_context.get('context', '')
            if context and context not in self.sensitive_topics:
                self.sensitive_topics.append(context)
    
    def _update_success_rate(self):
        """Update overall intervention success rate"""
        if len(self.effectiveness_history) < 10:
            return
        
        recent = self.effectiveness_history[-20:]  # Last 20 interventions
        
        # Count successful interventions (transformative or helpful)
        successful = sum(1 for e in recent 
                        if e['effectiveness'] in ['transformative', 'helpful'])
        
        self.intervention_success_rate = successful / len(recent)
    
    def _generate_outcome_insights(self, 
                                  intervention: Intervention,
                                  effectiveness: InterventionEffectiveness) -> List[str]:
        """Generate insights from intervention outcomes"""
        insights = []
        
        emotion = intervention.emotional_context.get('current_emotion')
        intensity = intervention.emotional_context.get('current_intensity', 0.5)
        
        if effectiveness == InterventionEffectiveness.TRANSFORMATIVE:
            insights.append(f"This type of response works beautifully when you're feeling {emotion}.")
            insights.append("The combination of empathy and wisdom seems especially powerful for you.")
        
        elif effectiveness == InterventionEffectiveness.HELPFUL:
            insights.append(f"You respond well to {intervention.intervention_type.value} when experiencing {emotion}.")
        
        elif effectiveness == InterventionEffectiveness.DISRUPTIVE:
            insights.append(f"Note to self: Be more gentle when you're feeling {emotion} at this intensity.")
            if intensity > 0.7:
                insights.append("Very intense emotions may need more silence and less advice.")
        
        return insights
    
    def get_recommended_intervention(self, 
                                    current_emotion: str,
                                    current_intensity: float,
                                    context: str = "") -> Dict[str, Any]:
        """Get recommended intervention based on past effectiveness"""
        
        # Find matching pattern
        matching_patterns = []
        for pattern in self.patterns.values():
            if pattern.emotion == current_emotion:
                low, high = pattern.intensity_range
                if low <= current_intensity <= high:
                    matching_patterns.append(pattern)
        
        if not matching_patterns:
            # Default recommendations based on emotion
            return self._get_default_recommendation(current_emotion, current_intensity)
        
        # Use pattern with highest success rate
        best_pattern = max(matching_patterns, key=lambda p: p.success_rate)
        
        # Get successful phrases for this context
        suggested_phrases = self._get_suggested_phrases(
            best_pattern.most_effective_type,
            current_emotion
        )
        
        # Check for sensitive topics
        caution_needed = any(topic in context for topic in self.sensitive_topics)
        
        return {
            'recommended_type': best_pattern.most_effective_type.value,
            'confidence': best_pattern.success_rate,
            'times_used': best_pattern.times_used,
            'suggested_phrases': suggested_phrases,
            'caution_needed': caution_needed,
            'timing': best_pattern.timing_preference,
            'personalization_score': self.user_preferences.get(best_pattern.most_effective_type, 0.5)
        }
    
    def _get_default_recommendation(self, emotion: str, intensity: float) -> Dict[str, Any]:
        """Get default recommendation for new emotional situations"""
        
        # Default mappings
        default_map = {
            'sadness': InterventionType.DEEP_LISTENING,
            'grief': InterventionType.SACRED_SILENCE,
            'anger': InterventionType.GENTLE_CHALLENGE,
            'frustration': InterventionType.REFLECTION_PROMPT,
            'fear': InterventionType.IMMEDIATE_SOOTHING,
            'anxiety': InterventionType.MEDITATION_GUIDANCE,
            'joy': InterventionType.CELEBRATION,
            'gratitude': InterventionType.GRATITUDE_PRACTICE,
            'peace': InterventionType.SACRED_SILENCE,
            'curiosity': InterventionType.WISDOM_SHARING,
            'confusion': InterventionType.REFLECTION_PROMPT,
            'hope': InterventionType.GROWTH_ENCOURAGEMENT
        }
        
        # Adjust for intensity
        if intensity > 0.8:
            # Very intense emotions need immediate soothing or silence
            if emotion in ['sadness', 'fear', 'anger']:
                recommended = InterventionType.IMMEDIATE_SOOTHING
            else:
                recommended = default_map.get(emotion, InterventionType.DEEP_LISTENING)
        else:
            recommended = default_map.get(emotion, InterventionType.DEEP_LISTENING)
        
        return {
            'recommended_type': recommended.value,
            'confidence': 0.5,  # Lower confidence for defaults
            'times_used': 0,
            'suggested_phrases': [],
            'caution_needed': False,
            'timing': 'immediate' if intensity > 0.7 else 'after_processing'
        }
    
    def _get_suggested_phrases(self, intervention_type: InterventionType, emotion: str) -> List[str]:
        """Get suggested phrases that worked well in the past"""
        
        # Filter successful phrases by relevance
        relevant_phrases = []
        
        for phrase in self.successful_phrases:
            # Check if phrase contains emotion-related words
            if emotion in phrase.lower():
                relevant_phrases.append(phrase)
        
        # Add some default templates
        templates = {
            InterventionType.DEEP_LISTENING: [
                f"I hear the {emotion} in your voice",
                f"Thank you for sharing this {emotion} with me",
                f"This {emotion} you're feeling matters"
            ],
            InterventionType.IMMEDIATE_SOOTHING: [
                f"Take a gentle breath with me",
                f"You're safe to feel this {emotion}",
                f"Be kind to yourself right now"
            ],
            InterventionType.WISDOM_SHARING: [
                f"{emotion.capitalize()} often carries wisdom",
                f"What might this {emotion} be teaching you?",
                f"There's something to learn from this {emotion}"
            ]
        }
        
        suggested = relevant_phrases[:2] + templates.get(intervention_type, [])[:2]
        return list(set(suggested))[:3]  # Return unique suggestions, max 3
    
    def get_effectiveness_report(self, days: int = 30) -> Dict[str, Any]:
        """Get report on intervention effectiveness"""
        
        cutoff = datetime.now() - timedelta(days=days)
        relevant = [e for e in self.effectiveness_history 
                   if datetime.fromisoformat(e['timestamp']) > cutoff]
        
        if not relevant:
            return {"status": "No data for this period"}
        
        # Calculate statistics by intervention type
        type_stats = defaultdict(lambda: {'count': 0, 'successful': 0})
        
        for entry in relevant:
            type_name = entry['type']
            type_stats[type_name]['count'] += 1
            if entry['effectiveness'] in ['transformative', 'helpful']:
                type_stats[type_name]['successful'] += 1
        
        # Calculate success rates
        for type_name, stats in type_stats.items():
            stats['success_rate'] = stats['successful'] / stats['count'] if stats['count'] > 0 else 0
        
        # Best and worst performing types
        best_type = max(type_stats.items(), key=lambda x: x[1]['success_rate']) if type_stats else None
        worst_type = min(type_stats.items(), key=lambda x: x[1]['success_rate']) if type_stats else None
        
        return {
            'period_days': days,
            'total_interventions': len(relevant),
            'overall_success_rate': self.intervention_success_rate,
            'by_type': dict(type_stats),
            'best_performing': {
                'type': best_type[0],
                'success_rate': best_type[1]['success_rate']
            } if best_type else None,
            'needs_improvement': {
                'type': worst_type[0],
                'success_rate': worst_type[1]['success_rate']
            } if worst_type and worst_type[1]['success_rate'] < 0.5 else None,
            'user_trust_level': self.user_trust_level,
            'sensitive_topics': self.sensitive_topics[:5]
        }
    
    def get_learning_insights(self) -> List[str]:
        """Get insights from what JARVIS has learned about the user"""
        insights = []
        
        # What works best
        if self.user_preferences:
            best_type = max(self.user_preferences.items(), key=lambda x: x[1])
            insights.append(f"You respond best to {best_type[0].value} when you need support.")
        
        # Success rate trend
        if self.intervention_success_rate > 0.8:
            insights.append("I'm learning to support you better each time. Our connection deepens.")
        elif self.intervention_success_rate < 0.5:
            insights.append("I'm still learning how to best support you. Please be patient with me.")
        
        # Sensitive topics
        if self.sensitive_topics:
            topics = ", ".join(self.sensitive_topics[:3])
            insights.append(f"I've learned to be especially gentle when discussing {topics}.")
        
        # Growth
        if len(self.interventions) > 50:
            insights.append("Our journey together has taught me much about supporting your emotional growth.")
        
        return insights
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """Get summary of today's interventions"""
        today = datetime.now().date()
        today_interventions = [i for i in self.interventions 
                             if i.timestamp.date() == today]
        
        if not today_interventions:
            return {"status": "No interventions today"}
        
        # Calculate today's effectiveness
        today_effectiveness = [e for e in self.effectiveness_history
                              if datetime.fromisoformat(e['timestamp']).date() == today]
        
        successful = sum(1 for e in today_effectiveness 
                        if e['effectiveness'] in ['transformative', 'helpful'])
        
        return {
            'count': len(today_interventions),
            'types': list(set(i.intervention_type.value for i in today_interventions)),
            'emotions_addressed': list(set(i.emotional_context.get('current_emotion') 
                                          for i in today_interventions)),
            'successful_interventions': successful,
            'success_rate': successful / len(today_effectiveness) if today_effectiveness else 0,
            'wisdom_shared': [i.wisdom_shared for i in today_interventions if i.wisdom_shared]
        }
    
    def _save_log(self):
        """Save intervention log to disk"""
        try:
            data = {
                'interventions': [
                    {
                        'id': i.id,
                        'timestamp': i.timestamp.isoformat(),
                        'intervention_type': i.intervention_type.value,
                        'emotional_context': i.emotional_context,
                        'response_text': i.response_text,
                        'user_reaction': i.user_reaction,
                        'effectiveness': i.effectiveness.value if i.effectiveness else None,
                        'follow_up_needed': i.follow_up_needed,
                        'wisdom_shared': i.wisdom_shared,
                        'user_feedback': i.user_feedback,
                        'learning_notes': i.learning_notes
                    }
                    for i in self.interventions
                ],
                'effectiveness_history': self.effectiveness_history,
                'user_preferences': {k.value: v for k, v in self.user_preferences.items()},
                'sensitive_topics': self.sensitive_topics,
                'successful_phrases': self.successful_phrases,
                'metrics': {
                    'intervention_success_rate': self.intervention_success_rate,
                    'user_trust_level': self.user_trust_level,
                    'timing_precision': self.timing_precision,
                    'wisdom_impact': self.wisdom_impact
                }
            }
            
            filepath = self.storage_path / 'intervention_log.json'
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving intervention log: {e}")
    
    def _load_log(self):
        """Load intervention log from disk"""
        try:
            filepath = self.storage_path / 'intervention_log.json'
            if filepath.exists():
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Load interventions
                self.interventions = []
                for i_data in data.get('interventions', []):
                    intervention = Intervention(
                        id=i_data['id'],
                        timestamp=datetime.fromisoformat(i_data['timestamp']),
                        intervention_type=InterventionType(i_data['intervention_type']),
                        emotional_context=i_data['emotional_context'],
                        response_text=i_data['response_text'],
                        user_reaction=i_data.get('user_reaction'),
                        effectiveness=InterventionEffectiveness(i_data['effectiveness']) if i_data.get('effectiveness') else None,
                        follow_up_needed=i_data.get('follow_up_needed', False),
                        wisdom_shared=i_data.get('wisdom_shared'),
                        user_feedback=i_data.get('user_feedback'),
                        learning_notes=i_data.get('learning_notes', [])
                    )
                    self.interventions.append(intervention)
                
                # Load other data
                self.effectiveness_history = data.get('effectiveness_history', [])
                
                # Load user preferences
                prefs = data.get('user_preferences', {})
                self.user_preferences = defaultdict(float)
                for k, v in prefs.items():
                    self.user_preferences[InterventionType(k)] = v
                
                self.sensitive_topics = data.get('sensitive_topics', [])
                self.successful_phrases = data.get('successful_phrases', [])
                
                # Load metrics
                metrics = data.get('metrics', {})
                self.intervention_success_rate = metrics.get('intervention_success_rate', 0.7)
                self.user_trust_level = metrics.get('user_trust_level', 0.8)
                self.timing_precision = metrics.get('timing_precision', 0.6)
                self.wisdom_impact = metrics.get('wisdom_impact', 0.5)
                
        except Exception as e:
            print(f"Error loading intervention log: {e}")
