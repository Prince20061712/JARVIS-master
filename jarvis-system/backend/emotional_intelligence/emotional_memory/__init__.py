"""
Emotional memory module for JARVIS.
Tracks long-term emotional patterns, interventions, and triggers with deep psychological insight.
Provides wisdom-based memory and spiritual growth tracking.
"""

from .emotional_history import EmotionalHistory, EmotionalSeason, WisdomLevel, GrowthMilestone
from .intervention_log import InterventionLog, InterventionType, InterventionEffectiveness
from .trigger_identifier import TriggerIdentifier, TriggerCategory, TriggerDepth, EmotionalTrigger

__all__ = [
    'EmotionalHistory',
    'InterventionLog', 
    'TriggerIdentifier',
    'EmotionalSeason',
    'WisdomLevel',
    'GrowthMilestone',
    'InterventionType',
    'InterventionEffectiveness',
    'TriggerCategory',
    'TriggerDepth',
    'EmotionalTrigger'
]