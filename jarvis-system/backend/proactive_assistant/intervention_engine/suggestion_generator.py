"""
Suggestion Generator Module - Enhanced version
Generates intelligent, context-aware suggestions for proactive interventions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
import random
import numpy as np
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class SuggestionPriority(Enum):
    """Priority levels for suggestions."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class SuggestionCategory(Enum):
    """Categories of suggestions."""
    PRODUCTIVITY = "productivity"
    WELLNESS = "wellness"
    LEARNING = "learning"
    REMINDER = "reminder"
    INSIGHT = "insight"
    BREAK = "break"
    TASK = "task"
    OPTIMIZATION = "optimization"

@dataclass
class Suggestion:
    """Data class for suggestions."""
    id: str
    title: str
    description: str
    category: SuggestionCategory
    priority: SuggestionPriority
    context_required: Dict[str, Any]
    action: Optional[Callable] = None
    action_params: Dict[str, Any] = field(default_factory=dict)
    expiry: Optional[datetime] = None
    cooldown_minutes: int = 30
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate a unique suggestion ID."""
        unique_string = f"{self.title}_{datetime.now().isoformat()}_{random.random()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]

class SuggestionGenerator:
    """
    Enhanced suggestion generator that creates contextual and personalized suggestions.
    Uses machine learning concepts to improve suggestion relevance over time.
    """
    
    def __init__(self, feedback_collector=None, templates_path: str = "data/suggestion_templates.json"):
        """
        Initialize the suggestion generator.
        
        Args:
            feedback_collector: Optional feedback collector instance for learning
            templates_path: Path to suggestion templates
        """
        self.feedback_collector = feedback_collector
        self.templates_path = Path(templates_path)
        
        # Suggestion storage
        self.active_suggestions: Dict[str, Suggestion] = {}
        self.suggestion_history: List[Dict] = []
        self.suggestion_templates: Dict[str, List[Dict]] = defaultdict(list)
        
        # Context tracking
        self.last_suggestion_time: Dict[str, datetime] = {}
        self.context_cache: Dict[str, Any] = {}
        self.user_preferences: Dict[str, Any] = {}
        
        # Learning parameters
        self.relevance_scores: Dict[str, float] = defaultdict(float)
        self.category_preferences: Dict[str, float] = defaultdict(lambda: 0.5)
        
        # Load templates
        self._load_templates()
        
        logger.info("SuggestionGenerator initialized successfully")
    
    def _load_templates(self):
        """Load suggestion templates from file."""
        if self.templates_path.exists():
            try:
                with open(self.templates_path, 'r') as f:
                    templates = json.load(f)
                    
                for category, category_templates in templates.items():
                    self.suggestion_templates[category] = category_templates
                    
                logger.info(f"Loaded templates for {len(self.suggestion_templates)} categories")
            except Exception as e:
                logger.error(f"Error loading templates: {e}")
                self._create_default_templates()
        else:
            self._create_default_templates()
    
    def _create_default_templates(self):
        """Create default suggestion templates."""
        self.suggestion_templates = {
            'productivity': [
                {
                    'title': "Focus Mode Activated",
                    'description': "You've been working for {duration} minutes. Would you like to enter focus mode?",
                    'context_required': {'activity': 'working', 'min_duration': 45}
                },
                {
                    'title': "Task Prioritization",
                    'description': "You have {task_count} pending tasks. Shall I help you prioritize them?",
                    'context_required': {'has_tasks': True}
                }
            ],
            'wellness': [
                {
                    'title': "Hydration Reminder",
                    'description': "You haven't had water in {hours_since_last_drink} hours. Time for a hydration break!",
                    'context_required': {'activity': 'working', 'duration': 60}
                },
                {
                    'title': "Eye Strain Prevention",
                    'description': "Time to follow the 20-20-20 rule! Look at something 20 feet away for 20 seconds.",
                    'context_required': {'screen_time': 120}
                }
            ],
            'learning': [
                {
                    'title': "Active Recall Session",
                    'description': "Based on your learning pattern, now is a good time for an active recall session.",
                    'context_required': {'activity': 'learning', 'duration': 30}
                },
                {
                    'title': "Concept Review",
                    'description': "You studied {topic} {days_ago} days ago. Time for a quick review?",
                    'context_required': {'has_learned_topics': True}
                }
            ],
            'break': [
                {
                    'title': "Break Time!",
                    'description': "You've been focused for {focus_duration} minutes. Take a {break_duration}-minute break?",
                    'context_required': {'continuous_work': 90}
                },
                {
                    'title': "Movement Break",
                    'description': "Time to stretch! Try these {exercise_count} simple desk exercises.",
                    'context_required': {'sedentary_time': 60}
                }
            ],
            'insight': [
                {
                    'title': "Productivity Pattern Detected",
                    'description': "You're most productive between {peak_hours}. Consider scheduling important tasks then.",
                    'context_required': {'has_productivity_data': True}
                }
            ]
        }
        
        # Save templates
        self.templates_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.templates_path, 'w') as f:
            json.dump(dict(self.suggestion_templates), f, indent=2)
    
    async def generate_suggestions(self, 
                                  context: Dict[str, Any],
                                  max_suggestions: int = 3,
                                  include_categories: Optional[List[SuggestionCategory]] = None) -> List[Suggestion]:
        """
        Generate contextually relevant suggestions.
        
        Args:
            context: Current user context
            max_suggestions: Maximum number of suggestions to generate
            include_categories: Optional filter for specific categories
            
        Returns:
            List of generated suggestions
        """
        try:
            # Update context cache
            self._update_context_cache(context)
            
            # Get candidate suggestions from all categories or filtered
            candidates = []
            
            categories = include_categories if include_categories else list(SuggestionCategory)
            
            for category in categories:
                category_suggestions = await self._generate_for_category(category, context)
                candidates.extend(category_suggestions)
            
            # Score and filter suggestions
            scored_suggestions = await self._score_suggestions(candidates, context)
            
            # Apply cooldowns
            filtered_suggestions = self._apply_cooldowns(scored_suggestions)
            
            # Select top suggestions
            selected = filtered_suggestions[:max_suggestions]
            
            # Store active suggestions
            for suggestion in selected:
                self.active_suggestions[suggestion.id] = suggestion
                self.last_suggestion_time[suggestion.id] = datetime.now()
                
                # Log generation
                self.suggestion_history.append({
                    'id': suggestion.id,
                    'title': suggestion.title,
                    'category': suggestion.category.value,
                    'priority': suggestion.priority.value,
                    'context': context.copy(),
                    'timestamp': datetime.now().isoformat()
                })
            
            logger.info(f"Generated {len(selected)} suggestions")
            
            return selected
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []
    
    async def _generate_for_category(self, 
                                    category: SuggestionCategory,
                                    context: Dict[str, Any]) -> List[Suggestion]:
        """Generate suggestions for a specific category."""
        suggestions = []
        templates = self.suggestion_templates.get(category.value, [])
        
        for template in templates:
            # Check if template matches context
            if self._matches_context(template['context_required'], context):
                # Personalize the suggestion
                suggestion = await self._create_suggestion_from_template(template, category, context)
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _matches_context(self, required: Dict[str, Any], actual: Dict[str, Any]) -> bool:
        """Check if context matches requirements."""
        for key, value in required.items():
            if key not in actual:
                return False
            
            if isinstance(value, dict):
                # Handle operators like min, max, etc.
                for op, op_value in value.items():
                    if op == 'min' and actual[key] < op_value:
                        return False
                    elif op == 'max' and actual[key] > op_value:
                        return False
                    elif op == 'equals' and actual[key] != op_value:
                        return False
            elif isinstance(value, (int, float, str, bool)):
                if actual[key] != value:
                    return False
        
        return True
    
    async def _create_suggestion_from_template(self, 
                                              template: Dict,
                                              category: SuggestionCategory,
                                              context: Dict[str, Any]) -> Optional[Suggestion]:
        """Create a personalized suggestion from template."""
        try:
            # Format title and description with context
            title = template['title']
            description = template['description']
            
            # Replace placeholders with context values
            for key, value in context.items():
                placeholder = f"{{{key}}}"
                if placeholder in title:
                    title = title.replace(placeholder, str(value))
                if placeholder in description:
                    description = description.replace(placeholder, str(value))
            
            # Calculate priority based on context and user preferences
            priority = self._calculate_priority(category, context)
            
            # Calculate expiry time
            expiry = None
            if priority == SuggestionPriority.CRITICAL:
                expiry = datetime.now() + timedelta(minutes=5)
            elif priority == SuggestionPriority.HIGH:
                expiry = datetime.now() + timedelta(minutes=15)
            elif priority == SuggestionPriority.MEDIUM:
                expiry = datetime.now() + timedelta(minutes=30)
            
            # Generate tags
            tags = self._generate_tags(category, context)
            
            return Suggestion(
                id="",  # Will be auto-generated
                title=title,
                description=description,
                category=category,
                priority=priority,
                context_required=template['context_required'],
                expiry=expiry,
                tags=tags,
                metadata={
                    'template_used': template.get('title'),
                    'generation_time': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating suggestion from template: {e}")
            return None
    
    def _calculate_priority(self, category: SuggestionCategory, context: Dict[str, Any]) -> SuggestionPriority:
        """Calculate suggestion priority based on context and preferences."""
        base_priority = SuggestionPriority.MEDIUM
        
        # Adjust based on category
        category_priority_map = {
            SuggestionCategory.WELLNESS: SuggestionPriority.HIGH,
            SuggestionCategory.BREAK: SuggestionPriority.MEDIUM,
            SuggestionCategory.PRODUCTIVITY: SuggestionPriority.MEDIUM,
            SuggestionCategory.LEARNING: SuggestionPriority.LOW,
            SuggestionCategory.REMINDER: SuggestionPriority.MEDIUM,
            SuggestionCategory.INSIGHT: SuggestionPriority.LOW,
            SuggestionCategory.TASK: SuggestionPriority.MEDIUM,
            SuggestionCategory.OPTIMIZATION: SuggestionPriority.LOW
        }
        
        base_priority = category_priority_map.get(category, SuggestionPriority.MEDIUM)
        
        # Adjust based on context factors
        priority_value = base_priority.value
        
        # Time-based adjustment
        if 'time_of_day' in context:
            if context['time_of_day'] in ['morning', 'evening']:
                priority_value += 0.5
        
        # Activity-based adjustment
        if 'activity' in context and context['activity'] == 'working':
            if category == SuggestionCategory.BREAK:
                priority_value += 1  # Breaks more important during work
        
        # User preference adjustment
        category_pref = self.category_preferences.get(category.value, 0.5)
        if category_pref > 0.7:
            priority_value += 0.5
        elif category_pref < 0.3:
            priority_value -= 0.5
        
        # Clamp to valid range
        priority_value = max(1, min(4, priority_value))
        
        return SuggestionPriority(int(priority_value))
    
    def _generate_tags(self, category: SuggestionCategory, context: Dict[str, Any]) -> List[str]:
        """Generate tags for suggestion categorization."""
        tags = [category.value]
        
        # Add context-based tags
        if 'activity' in context:
            tags.append(f"activity:{context['activity']}")
        
        if 'time_of_day' in context:
            tags.append(f"time:{context['time_of_day']}")
        
        if 'location' in context:
            tags.append(f"location:{context['location']}")
        
        # Add priority tag
        if 'urgent' in context and context['urgent']:
            tags.append("urgent")
        
        return tags
    
    async def _score_suggestions(self, 
                                suggestions: List[Suggestion],
                                context: Dict[str, Any]) -> List[Suggestion]:
        """Score and rank suggestions by relevance."""
        if not suggestions:
            return []
        
        scored = []
        for suggestion in suggestions:
            # Base score
            score = 0.5
            
            # Priority bonus
            score += suggestion.priority.value * 0.1
            
            # Relevance score from feedback collector
            if self.feedback_collector:
                context_key = self._get_context_key(context)
                relevance = self.feedback_collector.context_scores.get(context_key, 0.5)
                score += relevance * 0.2
            
            # Category preference
            category_pref = self.category_preferences.get(suggestion.category.value, 0.5)
            score += category_pref * 0.15
            
            # Novelty bonus (avoid repetition)
            if suggestion.id in self.last_suggestion_time:
                time_since = (datetime.now() - self.last_suggestion_time[suggestion.id]).total_seconds() / 3600
                if time_since < 24:  # Within last 24 hours
                    score *= 0.8  # Penalize repetition
            
            # Time-based adjustment
            if suggestion.expiry:
                time_until_expiry = (suggestion.expiry - datetime.now()).total_seconds()
                if time_until_expiry < 300:  # Less than 5 minutes
                    score *= 1.2  # Boost urgent suggestions
            
            suggestion.metadata['score'] = score
            scored.append((score, suggestion))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [s for _, s in scored]
    
    def _get_context_key(self, context: Dict[str, Any]) -> str:
        """Generate a context key for scoring."""
        important_keys = ['activity', 'time_of_day', 'day_of_week', 'location']
        key_parts = []
        
        for key in important_keys:
            if key in context:
                key_parts.append(f"{key}:{context[key]}")
        
        return "|".join(key_parts) if key_parts else "default"
    
    def _apply_cooldowns(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """Apply cooldown periods to suggestions."""
        filtered = []
        
        for suggestion in suggestions:
            # Check global cooldown for this suggestion type
            if suggestion.id in self.last_suggestion_time:
                time_since = (datetime.now() - self.last_suggestion_time[suggestion.id]).total_seconds() / 60
                if time_since < suggestion.cooldown_minutes:
                    continue  # Still in cooldown
            
            # Check category cooldown
            category_key = f"category_{suggestion.category.value}"
            if category_key in self.last_suggestion_time:
                time_since = (datetime.now() - self.last_suggestion_time[category_key]).total_seconds() / 60
                if time_since < 15:  # 15 minute category cooldown
                    continue
            
            filtered.append(suggestion)
        
        return filtered
    
    def _update_context_cache(self, context: Dict[str, Any]):
        """Update the context cache with new information."""
        # Merge contexts, keeping existing values if not present
        for key, value in context.items():
            if key not in self.context_cache or value is not None:
                self.context_cache[key] = value
    
    async def update_category_preferences(self, feedback: Dict[str, Any]):
        """
        Update category preferences based on feedback.
        
        Args:
            feedback: Feedback data from user
        """
        category = feedback.get('category')
        feedback_type = feedback.get('type')
        
        if not category:
            return
        
        # Calculate preference update
        if feedback_type in ['accepted', 'positive']:
            self.category_preferences[category] = min(
                1.0, 
                self.category_preferences[category] + 0.1
            )
        elif feedback_type in ['rejected', 'negative']:
            self.category_preferences[category] = max(
                0.0,
                self.category_preferences[category] - 0.1
            )
        
        logger.debug(f"Updated preference for {category}: {self.category_preferences[category]:.2f}")
    
    async def get_suggestion_by_id(self, suggestion_id: str) -> Optional[Suggestion]:
        """Get a suggestion by its ID."""
        return self.active_suggestions.get(suggestion_id)
    
    async def expire_suggestion(self, suggestion_id: str):
        """Mark a suggestion as expired and remove it."""
        if suggestion_id in self.active_suggestions:
            del self.active_suggestions[suggestion_id]
    
    async def cleanup_expired(self):
        """Remove expired suggestions."""
        now = datetime.now()
        expired_ids = [
            sid for sid, sug in self.active_suggestions.items()
            if sug.expiry and sug.expiry < now
        ]
        
        for sid in expired_ids:
            del self.active_suggestions[sid]
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired suggestions")
    
    async def get_suggestion_statistics(self) -> Dict[str, Any]:
        """Get statistics about generated suggestions."""
        total_generated = len(self.suggestion_history)
        
        # Count by category
        category_counts = defaultdict(int)
        for entry in self.suggestion_history:
            category_counts[entry['category']] += 1
        
        # Active suggestions
        active_by_priority = defaultdict(int)
        for suggestion in self.active_suggestions.values():
            active_by_priority[suggestion.priority.name] += 1
        
        return {
            'total_generated': total_generated,
            'active_suggestions': len(self.active_suggestions),
            'category_distribution': dict(category_counts),
            'active_by_priority': dict(active_by_priority),
            'category_preferences': dict(self.category_preferences)
        }