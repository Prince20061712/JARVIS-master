"""
Revision Planner Module - Enhanced version
Intelligent revision planning using spaced repetition and learning analytics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np
from collections import defaultdict
from dataclasses import dataclass, field
import json
from pathlib import Path
import asyncio
import math

logger = logging.getLogger(__name__)

class RevisionType(Enum):
    """Types of revision sessions."""
    INITIAL_REVIEW = "initial_review"
    QUICK_REVIEW = "quick_review"
    DEEP_REVIEW = "deep_review"
    PRACTICE_TEST = "practice_test"
    SUMMARY_REVIEW = "summary_review"
    FINAL_REVIEW = "final_review"

class RetentionLevel(Enum):
    """Retention levels for spaced repetition."""
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95

@dataclass
class RevisionItem:
    """Data class for items to be revised."""
    item_id: str
    topic: str
    content: str
    difficulty: float  # 1-5
    importance: int  # 1-5
    created_at: datetime
    last_reviewed: Optional[datetime] = None
    next_review: Optional[datetime] = None
    review_count: int = 0
    ease_factor: float = 2.5  # SM-2 algorithm factor
    interval: int = 1  # days
    retention_score: float = 0.0
    mastery_level: float = 0.0  # 0-1
    notes: str = ""
    tags: List[str] = field(default_factory=list)

@dataclass
class RevisionSchedule:
    """Data class for revision schedule."""
    schedule_id: str
    name: str
    items: List[RevisionItem]
    start_date: datetime
    end_date: datetime
    sessions_per_day: int = 1
    minutes_per_session: int = 30
    priority: str = "medium"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class SpacedRepetition:
    """Implementation of spaced repetition algorithm."""
    
    @staticmethod
    def calculate_next_review(item: RevisionItem,
                             quality: int) -> Tuple[datetime, float, int]:
        """
        Calculate next review date using SM-2 algorithm.
        
        Args:
            item: Revision item
            quality: Recall quality (0-5, where 5 is perfect recall)
            
        Returns:
            Tuple of (next_review_date, new_ease_factor, new_interval)
        """
        if quality < 0 or quality > 5:
            raise ValueError("Quality must be between 0 and 5")
        
        # SM-2 algorithm
        if quality >= 3:
            # Successful recall
            if item.review_count == 0:
                interval = 1
            elif item.review_count == 1:
                interval = 6
            else:
                interval = round(item.interval * item.ease_factor)
            
            # Update ease factor
            ease_factor = item.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            ease_factor = max(1.3, ease_factor)  # Minimum ease factor
            
            next_review = datetime.now() + timedelta(days=interval)
            return next_review, ease_factor, interval
        else:
            # Failed recall - reset
            interval = 1
            ease_factor = max(1.3, item.ease_factor - 0.2)
            next_review = datetime.now() + timedelta(days=1)
            return next_review, ease_factor, interval

class RevisionPlanner:
    """
    Enhanced revision planner using spaced repetition and learning analytics.
    """
    
    def __init__(self, storage_path: str = "data/scheduler/revision"):
        """
        Initialize the revision planner.
        
        Args:
            storage_path: Path to store revision data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Revision data storage
        self.revision_items: Dict[str, RevisionItem] = {}
        self.schedules: Dict[str, RevisionSchedule] = {}
        self.revision_history: List[Dict] = []
        
        # Learning parameters
        self.forgetting_curve_params = {'a': 0.5, 'b': 0.1}  # Ebbinghaus parameters
        self.optimal_review_window = timedelta(days=7)
        self.mastery_threshold = 0.85
        
        # Performance tracking
        self.topic_mastery: Dict[str, float] = defaultdict(float)
        self.review_effectiveness: Dict[str, List[float]] = defaultdict(list)
        
        # Load existing data
        self._load_data()
        
        logger.info("RevisionPlanner initialized successfully")
    
    def _load_data(self):
        """Load revision data from storage."""
        items_file = self.storage_path / "revision_items.json"
        schedules_file = self.storage_path / "schedules.json"
        history_file = self.storage_path / "history.json"
        
        if items_file.exists():
            try:
                with open(items_file, 'r') as f:
                    data = json.load(f)
                    for item_id, item_data in data.items():
                        item = RevisionItem(
                            item_id=item_id,
                            topic=item_data['topic'],
                            content=item_data['content'],
                            difficulty=item_data['difficulty'],
                            importance=item_data['importance'],
                            created_at=datetime.fromisoformat(item_data['created_at']),
                            last_reviewed=datetime.fromisoformat(item_data['last_reviewed']) if item_data.get('last_reviewed') else None,
                            next_review=datetime.fromisoformat(item_data['next_review']) if item_data.get('next_review') else None,
                            review_count=item_data.get('review_count', 0),
                            ease_factor=item_data.get('ease_factor', 2.5),
                            interval=item_data.get('interval', 1),
                            retention_score=item_data.get('retention_score', 0.0),
                            mastery_level=item_data.get('mastery_level', 0.0),
                            notes=item_data.get('notes', ''),
                            tags=item_data.get('tags', [])
                        )
                        self.revision_items[item_id] = item
                logger.info(f"Loaded {len(self.revision_items)} revision items")
            except Exception as e:
                logger.error(f"Error loading revision items: {e}")
        
        if schedules_file.exists():
            try:
                with open(schedules_file, 'r') as f:
                    data = json.load(f)
                    for sched_id, sched_data in data.items():
                        items = []
                        for item_id in sched_data.get('item_ids', []):
                            if item_id in self.revision_items:
                                items.append(self.revision_items[item_id])
                        
                        schedule = RevisionSchedule(
                            schedule_id=sched_id,
                            name=sched_data['name'],
                            items=items,
                            start_date=datetime.fromisoformat(sched_data['start_date']),
                            end_date=datetime.fromisoformat(sched_data['end_date']),
                            sessions_per_day=sched_data.get('sessions_per_day', 1),
                            minutes_per_session=sched_data.get('minutes_per_session', 30),
                            priority=sched_data.get('priority', 'medium'),
                            created_at=datetime.fromisoformat(sched_data['created_at']),
                            updated_at=datetime.fromisoformat(sched_data['updated_at'])
                        )
                        self.schedules[sched_id] = schedule
                logger.info(f"Loaded {len(self.schedules)} revision schedules")
            except Exception as e:
                logger.error(f"Error loading revision schedules: {e}")
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    self.revision_history = json.load(f)
                logger.info(f"Loaded {len(self.revision_history)} revision history entries")
            except Exception as e:
                logger.error(f"Error loading revision history: {e}")
    
    async def add_revision_item(self,
                               topic: str,
                               content: str,
                               difficulty: float = 3.0,
                               importance: int = 3,
                               tags: Optional[List[str]] = None,
                               notes: str = "") -> RevisionItem:
        """
        Add a new item to be revised.
        
        Args:
            topic: Topic of the item
            content: Content to be revised
            difficulty: Difficulty level (1-5)
            importance: Importance level (1-5)
            tags: Tags for categorization
            notes: Additional notes
            
        Returns:
            Created RevisionItem
        """
        item_id = self._generate_item_id(topic)
        
        item = RevisionItem(
            item_id=item_id,
            topic=topic,
            content=content,
            difficulty=difficulty,
            importance=importance,
            created_at=datetime.now(),
            tags=tags or [],
            notes=notes
        )
        
        self.revision_items[item_id] = item
        
        await self._save_data()
        
        logger.info(f"Added revision item: {topic} (ID: {item_id})")
        
        return item
    
    def _generate_item_id(self, topic: str) -> str:
        """Generate a unique item ID."""
        import hashlib
        import random
        
        unique_string = f"{topic}_{datetime.now().isoformat()}_{random.random()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    async def create_revision_schedule(self,
                                      name: str,
                                      item_ids: List[str],
                                      target_date: Optional[datetime] = None,
                                      sessions_per_day: int = 1,
                                      minutes_per_session: int = 30) -> RevisionSchedule:
        """
        Create a revision schedule for a set of items.
        
        Args:
            name: Schedule name
            item_ids: List of item IDs to include
            target_date: Target date to complete by (default: 30 days from now)
            sessions_per_day: Number of revision sessions per day
            minutes_per_session: Minutes per session
            
        Returns:
            Created RevisionSchedule
        """
        items = []
        for item_id in item_ids:
            if item_id in self.revision_items:
                items.append(self.revision_items[item_id])
        
        if not items:
            raise ValueError("No valid items provided")
        
        # Set target date if not specified
        if not target_date:
            target_date = datetime.now() + timedelta(days=30)
        
        schedule_id = self._generate_schedule_id(name)
        
        schedule = RevisionSchedule(
            schedule_id=schedule_id,
            name=name,
            items=items,
            start_date=datetime.now(),
            end_date=target_date,
            sessions_per_day=sessions_per_day,
            minutes_per_session=minutes_per_session
        )
        
        self.schedules[schedule_id] = schedule
        
        await self._save_data()
        
        logger.info(f"Created revision schedule: {name} with {len(items)} items")
        
        return schedule
    
    def _generate_schedule_id(self, name: str) -> str:
        """Generate a unique schedule ID."""
        import hashlib
        import random
        
        unique_string = f"{name}_{datetime.now().isoformat()}_{random.random()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    async def get_due_revisions(self, max_items: int = 20) -> List[RevisionItem]:
        """Get items that are due for revision now."""
        now = datetime.now()
        due = []
        
        for item in self.revision_items.values():
            if item.next_review and item.next_review <= now:
                due.append(item)
        
        # Sort by priority (importance * (1 - mastery_level))
        due.sort(
            key=lambda i: (i.importance * (1 - i.mastery_level), i.next_review),
            reverse=True
        )
        
        return due[:max_items]
    
    async def get_upcoming_revisions(self, days: int = 7) -> Dict[datetime.date, List[RevisionItem]]:
        """Get revisions scheduled for upcoming days."""
        now = datetime.now()
        cutoff = now + timedelta(days=days)
        
        upcoming = defaultdict(list)
        
        for item in self.revision_items.values():
            if item.next_review and now < item.next_review <= cutoff:
                review_date = item.next_review.date()
                upcoming[review_date].append(item)
        
        # Sort by date
        return dict(sorted(upcoming.items()))
    
    async def record_revision(self,
                            item_id: str,
                            quality: int,
                            time_spent_minutes: int = 0,
                            notes: str = "") -> Dict[str, Any]:
        """
        Record a revision session for an item.
        
        Args:
            item_id: ID of the revised item
            quality: Recall quality (0-5)
            time_spent_minutes: Minutes spent on revision
            notes: Additional notes
            
        Returns:
            Dictionary with updated item information
        """
        item = self.revision_items.get(item_id)
        if not item:
            raise ValueError(f"Item {item_id} not found")
        
        # Update review count
        item.review_count += 1
        item.last_reviewed = datetime.now()
        
        # Calculate next review using spaced repetition
        next_review, ease_factor, interval = SpacedRepetition.calculate_next_review(item, quality)
        
        item.next_review = next_review
        item.ease_factor = ease_factor
        item.interval = interval
        
        # Update retention and mastery scores
        retention = quality / 5.0
        item.retention_score = 0.7 * item.retention_score + 0.3 * retention if item.retention_score > 0 else retention
        
        # Calculate mastery (combination of review count, retention, and consistency)
        base_mastery = item.retention_score
        count_factor = min(1.0, item.review_count / 10)
        item.mastery_level = 0.6 * base_mastery + 0.4 * count_factor
        
        # Update topic mastery
        self.topic_mastery[item.topic] = max(
            self.topic_mastery[item.topic],
            item.mastery_level
        )
        
        # Track effectiveness
        self.review_effectiveness[item.topic].append(retention)
        
        # Record in history
        history_entry = {
            'item_id': item_id,
            'topic': item.topic,
            'quality': quality,
            'time_spent_minutes': time_spent_minutes,
            'next_review': next_review.isoformat(),
            'retention_score': item.retention_score,
            'mastery_level': item.mastery_level,
            'notes': notes,
            'timestamp': datetime.now().isoformat()
        }
        self.revision_history.append(history_entry)
        
        await self._save_data()
        
        logger.info(f"Recorded revision for {item.topic} with quality {quality}")
        
        return {
            'item_id': item_id,
            'topic': item.topic,
            'quality': quality,
            'next_review': next_review.isoformat(),
            'retention_score': item.retention_score,
            'mastery_level': item.mastery_level
        }
    
    async def get_revision_plan(self,
                              available_minutes: int = 30,
                              focus_topics: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Generate an optimal revision plan for available time.
        
        Args:
            available_minutes: Minutes available for revision
            focus_topics: Optional list of topics to focus on
            
        Returns:
            List of recommended revision items with estimated times
        """
        # Get due items
        due_items = await self.get_due_revisions()
        
        if focus_topics:
            due_items = [i for i in due_items if i.topic in focus_topics]
        
        if not due_items:
            # If nothing due, recommend items nearing due
            now = datetime.now()
            upcoming = []
            for item in self.revision_items.values():
                if item.next_review and item.next_review <= now + timedelta(days=3):
                    upcoming.append(item)
            due_items = upcoming
        
        # Calculate time estimates for each item
        recommendations = []
        total_time = 0
        
        for item in due_items:
            # Estimate time needed based on difficulty and mastery
            base_time = 5  # minutes
            difficulty_factor = item.difficulty / 3.0
            mastery_factor = 1.0 - item.mastery_level
            estimated_time = base_time * difficulty_factor * (1 + mastery_factor)
            
            # Cap at reasonable limits
            estimated_time = min(20, max(3, estimated_time))
            
            if total_time + estimated_time <= available_minutes:
                recommendations.append({
                    'item_id': item.item_id,
                    'topic': item.topic,
                    'content': item.content[:100] + "..." if len(item.content) > 100 else item.content,
                    'difficulty': item.difficulty,
                    'importance': item.importance,
                    'mastery_level': item.mastery_level,
                    'estimated_minutes': round(estimated_time, 1),
                    'last_reviewed': item.last_reviewed.isoformat() if item.last_reviewed else None,
                    'days_overdue': (datetime.now() - item.next_review).days if item.next_review and item.next_review < datetime.now() else 0
                })
                total_time += estimated_time
        
        return recommendations
    
    async def get_mastery_progress(self, topic: Optional[str] = None) -> Dict[str, Any]:
        """Get mastery progress for topics."""
        if topic:
            items = [i for i in self.revision_items.values() if i.topic == topic]
            topic_items = {topic: items}
        else:
            # Group by topic
            topic_items = defaultdict(list)
            for item in self.revision_items.values():
                topic_items[item.topic].append(item)
        
        progress = {}
        for tpc, items in topic_items.items():
            if not items:
                continue
            
            # Calculate topic statistics
            avg_mastery = np.mean([i.mastery_level for i in items])
            avg_importance = np.mean([i.importance for i in items])
            avg_difficulty = np.mean([i.difficulty for i in items])
            
            # Count items by status
            total = len(items)
            mastered = sum(1 for i in items if i.mastery_level >= self.mastery_threshold)
            in_progress = sum(1 for i in items if 0.3 <= i.mastery_level < self.mastery_threshold)
            not_started = sum(1 for i in items if i.mastery_level < 0.3)
            
            # Get due items
            now = datetime.now()
            due = sum(1 for i in items if i.next_review and i.next_review <= now)
            
            # Get effectiveness trend
            effectiveness = self.review_effectiveness.get(tpc, [])
            trend = 'improving' if len(effectiveness) > 1 and effectiveness[-1] > effectiveness[0] else 'stable'
            
            progress[tpc] = {
                'total_items': total,
                'mastered': mastered,
                'in_progress': in_progress,
                'not_started': not_started,
                'mastery_percentage': (mastered / total) * 100 if total > 0 else 0,
                'average_mastery': avg_mastery,
                'average_importance': avg_importance,
                'average_difficulty': avg_difficulty,
                'due_items': due,
                'effectiveness_trend': trend,
                'last_reviewed': max((i.last_reviewed for i in items if i.last_reviewed), default=None)
            }
        
        # Calculate overall statistics
        all_items = list(self.revision_items.values())
        if all_items:
            overall = {
                'total_items': len(all_items),
                'mastered': sum(1 for i in all_items if i.mastery_level >= self.mastery_threshold),
                'average_mastery': np.mean([i.mastery_level for i in all_items]),
                'due_today': len(await self.get_due_revisions())
            }
        else:
            overall = {}
        
        return {
            'by_topic': progress,
            'overall': overall
        }
    
    async def optimize_schedule(self, schedule_id: str) -> Optional[RevisionSchedule]:
        """Optimize a revision schedule based on item priorities and due dates."""
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return None
        
        # Calculate available time
        days_available = (schedule.end_date - schedule.start_date).days
        total_slots = days_available * schedule.sessions_per_day
        minutes_available = total_slots * schedule.minutes_per_session
        
        # Estimate total time needed
        total_needed = 0
        for item in schedule.items:
            # Estimate reviews needed to reach mastery
            remaining = max(0, 1 - item.mastery_level)
            reviews_needed = math.ceil(remaining * 10)  # Rough estimate
            time_per_review = 5 * (item.difficulty / 3)
            total_needed += reviews_needed * time_per_review
        
        if total_needed > minutes_available:
            logger.warning(f"Schedule {schedule_id} may be too ambitious: "
                          f"{total_needed} minutes needed, {minutes_available} available")
        
        # Update schedule priority
        if total_needed > minutes_available * 1.2:
            schedule.priority = "high"
        elif total_needed < minutes_available * 0.5:
            schedule.priority = "low"
        else:
            schedule.priority = "medium"
        
        schedule.updated_at = datetime.now()
        
        await self._save_data()
        
        return schedule
    
    async def predict_retention(self,
                              item_id: str,
                              days_ahead: int = 30) -> List[float]:
        """
        Predict retention curve for an item using Ebbinghaus forgetting curve.
        
        Args:
            item_id: ID of the item
            days_ahead: Number of days to predict
            
        Returns:
            List of predicted retention scores for each day
        """
        item = self.revision_items.get(item_id)
        if not item:
            return []
        
        # Base retention on last review
        if not item.last_reviewed:
            return [0.5] * days_ahead
        
        days_since = (datetime.now() - item.last_reviewed).days
        
        # Ebbinghaus forgetting curve: R = e^(-t/S)
        # where S is stability based on review count and ease factor
        stability = item.interval * (0.5 + 0.1 * item.review_count)
        
        predictions = []
        for day in range(days_ahead):
            t = days_since + day
            retention = math.exp(-t / stability) * item.retention_score
            predictions.append(max(0.1, min(0.99, retention)))
        
        return predictions
    
    async def get_weak_areas(self, threshold: float = 0.6) -> List[Dict[str, Any]]:
        """Identify weak areas that need more revision."""
        weak_areas = []
        
        # Group by topic
        topic_items = defaultdict(list)
        for item in self.revision_items.values():
            topic_items[item.topic].append(item)
        
        for topic, items in topic_items.items():
            avg_mastery = np.mean([i.mastery_level for i in items])
            if avg_mastery < threshold:
                # Find specific weak items
                weak_items = [
                    {
                        'item_id': i.item_id,
                        'content': i.content[:100],
                        'mastery': i.mastery_level,
                        'last_reviewed': i.last_reviewed.isoformat() if i.last_reviewed else None
                    }
                    for i in items if i.mastery_level < threshold
                ]
                
                weak_areas.append({
                    'topic': topic,
                    'average_mastery': avg_mastery,
                    'items_count': len(items),
                    'weak_items_count': len(weak_items),
                    'weak_items': weak_items[:5],  # Top 5 weak items
                    'recommendation': f"Focus on {topic} - {len(weak_items)} items need review"
                })
        
        # Sort by average mastery (lowest first)
        weak_areas.sort(key=lambda x: x['average_mastery'])
        
        return weak_areas
    
    async def generate_review_quiz(self,
                                  topic: Optional[str] = None,
                                  num_questions: int = 5) -> List[Dict[str, Any]]:
        """
        Generate a quiz from revision items for active recall practice.
        
        Args:
            topic: Optional topic to focus on
            num_questions: Number of questions to generate
            
        Returns:
            List of quiz questions
        """
        # Get candidate items
        if topic:
            candidates = [i for i in self.revision_items.values() if i.topic == topic]
        else:
            candidates = list(self.revision_items.values())
        
        if len(candidates) < num_questions:
            num_questions = len(candidates)
        
        # Prioritize items that are due or have low mastery
        def priority_score(item):
            due_boost = 2.0 if item.next_review and item.next_review <= datetime.now() else 1.0
            mastery_penalty = 1.0 - item.mastery_level
            importance_boost = item.importance / 3.0
            return due_boost * mastery_penalty * importance_boost
        
        candidates.sort(key=priority_score, reverse=True)
        
        # Select top items
        selected = candidates[:num_questions]
        
        # Generate questions (simplified - in practice, you'd have question banks)
        quiz = []
        for item in selected:
            # Simple question generation from content
            content_preview = item.content[:200]
            quiz.append({
                'item_id': item.item_id,
                'topic': item.topic,
                'question': f"What do you remember about: {item.topic}?",
                'context': content_preview,
                'difficulty': item.difficulty,
                'importance': item.importance,
                'mastery_level': item.mastery_level
            })
        
        return quiz
    
    async def get_revision_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive revision statistics."""
        cutoff = datetime.now() - timedelta(days=days)
        
        # Filter recent history
        recent_history = [
            h for h in self.revision_history
            if datetime.fromisoformat(h['timestamp']) > cutoff
        ]
        
        if not self.revision_items and not recent_history:
            return {'message': 'No revision data available'}
        
        # Calculate statistics
        total_reviews = len(recent_history)
        avg_quality = np.mean([h['quality'] for h in recent_history]) if recent_history else 0
        avg_time = np.mean([h.get('time_spent_minutes', 0) for h in recent_history]) if recent_history else 0
        
        # Quality distribution
        quality_dist = defaultdict(int)
        for h in recent_history:
            quality_dist[h['quality']] += 1
        
        # Topic performance
        topic_performance = defaultdict(list)
        for h in recent_history:
            topic_performance[h['topic']].append(h['quality'])
        
        topic_avg = {
            topic: np.mean(scores) for topic, scores in topic_performance.items()
        }
        
        # Calculate retention improvement
        mastery_progress = await self.get_mastery_progress()
        
        # Review schedule adherence
        scheduled_vs_actual = []
        for item in self.revision_items.values():
            if item.last_reviewed and item.next_review:
                scheduled_vs_actual.append({
                    'topic': item.topic,
                    'scheduled': item.next_review.isoformat(),
                    'actual': item.last_reviewed.isoformat(),
                    'on_time': item.last_reviewed <= item.next_review
                })
        
        on_time_rate = sum(1 for s in scheduled_vs_actual if s['on_time']) / len(scheduled_vs_actual) if scheduled_vs_actual else 0
        
        return {
            'period_days': days,
            'total_reviews': total_reviews,
            'average_quality': avg_quality,
            'average_time_minutes': avg_time,
            'quality_distribution': dict(quality_dist),
            'topic_performance': topic_avg,
            'mastery_progress': mastery_progress,
            'schedule_adherence': on_time_rate,
            'total_items': len(self.revision_items),
            'items_mastered': sum(1 for i in self.revision_items.values() if i.mastery_level >= self.mastery_threshold),
            'items_due': len(await self.get_due_revisions())
        }
    
    async def _save_data(self):
        """Save revision data to storage."""
        try:
            # Save revision items
            items_file = self.storage_path / "revision_items.json"
            items_data = {}
            for item_id, item in self.revision_items.items():
                items_data[item_id] = {
                    'topic': item.topic,
                    'content': item.content,
                    'difficulty': item.difficulty,
                    'importance': item.importance,
                    'created_at': item.created_at.isoformat(),
                    'last_reviewed': item.last_reviewed.isoformat() if item.last_reviewed else None,
                    'next_review': item.next_review.isoformat() if item.next_review else None,
                    'review_count': item.review_count,
                    'ease_factor': item.ease_factor,
                    'interval': item.interval,
                    'retention_score': item.retention_score,
                    'mastery_level': item.mastery_level,
                    'notes': item.notes,
                    'tags': item.tags
                }
            
            with open(items_file, 'w') as f:
                json.dump(items_data, f, indent=2, default=str)
            
            # Save schedules
            schedules_file = self.storage_path / "schedules.json"
            schedules_data = {}
            for sched_id, schedule in self.schedules.items():
                schedules_data[sched_id] = {
                    'name': schedule.name,
                    'item_ids': [i.item_id for i in schedule.items],
                    'start_date': schedule.start_date.isoformat(),
                    'end_date': schedule.end_date.isoformat(),
                    'sessions_per_day': schedule.sessions_per_day,
                    'minutes_per_session': schedule.minutes_per_session,
                    'priority': schedule.priority,
                    'created_at': schedule.created_at.isoformat(),
                    'updated_at': schedule.updated_at.isoformat()
                }
            
            with open(schedules_file, 'w') as f:
                json.dump(schedules_data, f, indent=2, default=str)
            
            # Save history
            history_file = self.storage_path / "history.json"
            with open(history_file, 'w') as f:
                json.dump(self.revision_history[-1000:], f, indent=2, default=str)
            
            logger.debug("Revision data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving revision data: {e}")