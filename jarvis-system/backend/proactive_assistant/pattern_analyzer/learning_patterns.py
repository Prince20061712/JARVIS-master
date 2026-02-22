"""
Learning Patterns Module - Enhanced version
Analyzes learning patterns, styles, and memory retention for optimized learning.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass, field
import json
from pathlib import Path
import asyncio
from scipy import stats, optimize
from sklearn.cluster import KMeans
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class LearningStyle(Enum):
    """Enum for learning styles."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    READING = "reading"
    KINESTHETIC = "kinesthetic"
    MIXED = "mixed"

class MemoryRetention(Enum):
    """Enum for memory retention levels."""
    SHORT_TERM = "short_term"  # Hours to days
    MEDIUM_TERM = "medium_term"  # Days to weeks
    LONG_TERM = "long_term"  # Weeks to months
    MASTERED = "mastered"  # Permanent

class ContentType(Enum):
    """Types of learning content."""
    VIDEO = "video"
    ARTICLE = "article"
    CODE = "code"
    EXERCISE = "exercise"
    QUIZ = "quiz"
    DISCUSSION = "discussion"
    PROJECT = "project"
    THEORY = "theory"

@dataclass
class LearningSession:
    """Data class for learning sessions."""
    session_id: str
    topic: str
    content_type: ContentType
    duration: timedelta
    engagement_score: float
    comprehension_score: float
    retention_score: Optional[float]
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class KnowledgeGap:
    """Data class for identified knowledge gaps."""
    topic: str
    confidence: float
    related_topics: List[str]
    suggested_resources: List[str]
    priority: int  # 1-5
    identified_at: datetime

@dataclass
class SpacedRepetitionItem:
    """Data class for spaced repetition scheduling."""
    topic: str
    last_reviewed: datetime
    next_review: datetime
    ease_factor: float  # 1.3 - 2.5
    interval: int  # Days
    repetitions: int
    retention_score: float

class LearningPatterns:
    """
    Enhanced learning patterns analyzer that identifies learning styles,
    optimizes spaced repetition, and detects knowledge gaps.
    """
    
    def __init__(self, storage_path: str = "data/patterns/learning"):
        """
        Initialize the learning patterns analyzer.
        
        Args:
            storage_path: Path to store learning data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Learning data storage
        self.sessions: List[LearningSession] = []
        self.knowledge_gaps: List[KnowledgeGap] = []
        self.repetition_items: Dict[str, SpacedRepetitionItem] = {}
        
        # Learning metrics
        self.learning_style_scores: Dict[LearningStyle, float] = defaultdict(float)
        self.content_preferences: Dict[ContentType, float] = defaultdict(float)
        self.topic_mastery: Dict[str, float] = defaultdict(float)  # 0-1
        self.topic_relationships: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        
        # Learning parameters
        self.forgetting_curve_params = {'a': 0.5, 'b': 0.1}  # Ebbinghaus parameters
        self.optimal_review_window = timedelta(days=7)
        self.mastery_threshold = 0.85
        
        # Load existing data
        self._load_data()
        
        logger.info("LearningPatterns initialized successfully")
    
    def _load_data(self):
        """Load learning data from storage."""
        sessions_file = self.storage_path / "sessions.json"
        gaps_file = self.storage_path / "knowledge_gaps.json"
        repetition_file = self.storage_path / "repetition.json"
        
        if sessions_file.exists():
            try:
                with open(sessions_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        session = LearningSession(
                            session_id=item['session_id'],
                            topic=item['topic'],
                            content_type=ContentType(item['content_type']),
                            duration=timedelta(seconds=item['duration']),
                            engagement_score=item['engagement_score'],
                            comprehension_score=item['comprehension_score'],
                            retention_score=item.get('retention_score'),
                            timestamp=datetime.fromisoformat(item['timestamp']),
                            context=item.get('context', {}),
                            metadata=item.get('metadata', {})
                        )
                        self.sessions.append(session)
                logger.info(f"Loaded {len(self.sessions)} learning sessions")
            except Exception as e:
                logger.error(f"Error loading sessions: {e}")
        
        if gaps_file.exists():
            try:
                with open(gaps_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        gap = KnowledgeGap(
                            topic=item['topic'],
                            confidence=item['confidence'],
                            related_topics=item['related_topics'],
                            suggested_resources=item['suggested_resources'],
                            priority=item['priority'],
                            identified_at=datetime.fromisoformat(item['identified_at'])
                        )
                        self.knowledge_gaps.append(gap)
                logger.info(f"Loaded {len(self.knowledge_gaps)} knowledge gaps")
            except Exception as e:
                logger.error(f"Error loading knowledge gaps: {e}")
        
        if repetition_file.exists():
            try:
                with open(repetition_file, 'r') as f:
                    data = json.load(f)
                    for topic, item in data.items():
                        self.repetition_items[topic] = SpacedRepetitionItem(
                            topic=item['topic'],
                            last_reviewed=datetime.fromisoformat(item['last_reviewed']),
                            next_review=datetime.fromisoformat(item['next_review']),
                            ease_factor=item['ease_factor'],
                            interval=item['interval'],
                            repetitions=item['repetitions'],
                            retention_score=item['retention_score']
                        )
                logger.info(f"Loaded {len(self.repetition_items)} repetition items")
            except Exception as e:
                logger.error(f"Error loading repetition items: {e}")
    
    async def record_learning_session(self,
                                    session_id: str,
                                    topic: str,
                                    content_type: ContentType,
                                    duration: timedelta,
                                    engagement_score: float,
                                    comprehension_score: float,
                                    retention_score: Optional[float] = None,
                                    context: Optional[Dict] = None,
                                    metadata: Optional[Dict] = None) -> LearningSession:
        """
        Record a learning session for analysis.
        
        Args:
            session_id: Unique session identifier
            topic: Topic being learned
            content_type: Type of content
            duration: Session duration
            engagement_score: User engagement (0-1)
            comprehension_score: Understanding level (0-1)
            retention_score: Retention score if tested
            context: Context information
            metadata: Additional metadata
            
        Returns:
            LearningSession object
        """
        try:
            session = LearningSession(
                session_id=session_id,
                topic=topic,
                content_type=content_type,
                duration=duration,
                engagement_score=engagement_score,
                comprehension_score=comprehension_score,
                retention_score=retention_score,
                timestamp=datetime.now(),
                context=context or {},
                metadata=metadata or {}
            )
            
            self.sessions.append(session)
            
            # Update learning metrics
            self._update_learning_metrics(session)
            
            # Update spaced repetition if retention score available
            if retention_score is not None:
                await self.update_spaced_repetition(topic, retention_score)
            
            # Detect knowledge gaps
            await self.detect_knowledge_gaps(topic, comprehension_score, retention_score)
            
            # Trim history
            self._trim_history()
            
            # Save data
            await self._save_data()
            
            logger.info(f"Recorded learning session: {session_id} - {topic}")
            
            return session
            
        except Exception as e:
            logger.error(f"Error recording learning session: {e}")
            raise
    
    def _update_learning_metrics(self, session: LearningSession):
        """Update learning metrics based on session."""
        # Update learning style scores
        style_indicators = self._detect_learning_style(session)
        for style, indicator in style_indicators.items():
            self.learning_style_scores[style] += indicator
        
        # Update content preferences
        self.content_preferences[session.content_type] = (
            0.7 * self.content_preferences[session.content_type] +
            0.3 * session.engagement_score
        )
        
        # Update topic mastery (using exponential moving average)
        current_mastery = self.topic_mastery[session.topic]
        new_mastery = 0.7 * session.comprehension_score + 0.3 * (session.retention_score or 0)
        self.topic_mastery[session.topic] = 0.8 * current_mastery + 0.2 * new_mastery
    
    def _detect_learning_style(self, session: LearningSession) -> Dict[LearningStyle, float]:
        """
        Detect learning style from session characteristics.
        
        Returns:
            Dictionary mapping learning styles to indicator strengths
        """
        indicators = defaultdict(float)
        
        # Content type indicators
        content_style_map = {
            ContentType.VIDEO: LearningStyle.VISUAL,
            ContentType.ARTICLE: LearningStyle.READING,
            ContentType.CODE: LearningStyle.KINESTHETIC,
            ContentType.EXERCISE: LearningStyle.KINESTHETIC,
            ContentType.DISCUSSION: LearningStyle.AUDITORY
        }
        
        if session.content_type in content_style_map:
            style = content_style_map[session.content_type]
            indicators[style] += session.engagement_score
        
        # Engagement pattern indicators
        if session.duration > timedelta(minutes=45):
            # Longer sessions might indicate kinesthetic/reading preference
            indicators[LearningStyle.KINESTHETIC] += 0.3
            indicators[LearningStyle.READING] += 0.3
        elif session.duration < timedelta(minutes=15):
            # Short sessions might indicate visual/auditory preference
            indicators[LearningStyle.VISUAL] += 0.2
            indicators[LearningStyle.AUDITORY] += 0.2
        
        # Context-based indicators
        context = session.context
        if context.get('note_taking', False):
            indicators[LearningStyle.READING] += 0.4
        if context.get('discussion_participation', False):
            indicators[LearningStyle.AUDITORY] += 0.4
        if context.get('hands_on', False):
            indicators[LearningStyle.KINESTHETIC] += 0.4
        
        return dict(indicators)
    
    async def get_learning_style_analysis(self) -> Dict[str, Any]:
        """Get detailed analysis of learning style preferences."""
        # Normalize scores
        total = sum(self.learning_style_scores.values())
        if total > 0:
            normalized_scores = {
                style.value: score / total
                for style, score in self.learning_style_scores.items()
            }
        else:
            normalized_scores = {style.value: 0.25 for style in LearningStyle}
        
        # Identify primary and secondary styles
        sorted_styles = sorted(
            normalized_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        primary_style = sorted_styles[0][0] if sorted_styles else None
        secondary_style = sorted_styles[1][0] if len(sorted_styles) > 1 else None
        
        # Generate recommendations
        recommendations = self._generate_style_recommendations(primary_style, secondary_style)
        
        return {
            'learning_style_scores': normalized_scores,
            'primary_style': primary_style,
            'secondary_style': secondary_style,
            'confidence': total / len(self.sessions) if self.sessions else 0,
            'recommendations': recommendations,
            'content_preferences': {
                ct.value: score for ct, score in self.content_preferences.items()
            }
        }
    
    def _generate_style_recommendations(self,
                                       primary_style: Optional[str],
                                       secondary_style: Optional[str]) -> List[str]:
        """Generate learning recommendations based on style."""
        recommendations = []
        
        style_recommendations = {
            'visual': [
                "Use diagrams, mind maps, and visual aids",
                "Watch video tutorials and demonstrations",
                "Color-code your notes and materials"
            ],
            'auditory': [
                "Discuss topics with others or explain aloud",
                "Use text-to-speech for reading materials",
                "Record and listen to your own summaries"
            ],
            'reading': [
                "Write detailed notes and summaries",
                "Read multiple sources on the same topic",
                "Create written study guides"
            ],
            'kinesthetic': [
                "Build hands-on projects",
                "Take frequent breaks for physical activity",
                "Use physical objects to model concepts"
            ]
        }
        
        if primary_style:
            recommendations.extend(style_recommendations.get(primary_style, []))
        
        if secondary_style and secondary_style != primary_style:
            recommendations.append(
                f"Complement your {primary_style} learning with "
                f"{secondary_style} techniques for variety"
            )
        
        return recommendations
    
    async def update_spaced_repetition(self,
                                      topic: str,
                                      retention_score: float):
        """
        Update spaced repetition schedule based on retention.
        Uses SM-2 algorithm variant for optimal scheduling.
        
        Args:
            topic: Topic being reviewed
            retention_score: Retention score (0-1)
        """
        now = datetime.now()
        
        if topic in self.repetition_items:
            item = self.repetition_items[topic]
            
            # Calculate new ease factor (SM-2 algorithm)
            quality = retention_score * 5  # Convert to 0-5 scale
            item.ease_factor = max(1.3, item.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
            
            # Calculate new interval
            if retention_score >= 0.8:  # Good retention
                if item.repetitions == 0:
                    item.interval = 1
                elif item.repetitions == 1:
                    item.interval = 6
                else:
                    item.interval = round(item.interval * item.ease_factor)
                item.repetitions += 1
            else:  # Poor retention, reset
                item.interval = 1
                item.repetitions = 0
        else:
            # New item
            item = SpacedRepetitionItem(
                topic=topic,
                last_reviewed=now,
                next_review=now + timedelta(days=1),
                ease_factor=2.5,
                interval=1,
                repetitions=1,
                retention_score=retention_score
            )
        
        # Update next review date
        item.last_reviewed = now
        item.next_review = now + timedelta(days=item.interval)
        item.retention_score = retention_score
        
        self.repetition_items[topic] = item
        
        logger.info(f"Updated spaced repetition for '{topic}': next review in {item.interval} days")
    
    async def get_review_schedule(self, days: int = 30) -> Dict[str, Any]:
        """
        Get optimal review schedule for all topics.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            Dictionary with review schedule
        """
        now = datetime.now()
        schedule = defaultdict(list)
        
        for topic, item in self.repetition_items.items():
            if item.next_review <= now + timedelta(days=days):
                days_until = (item.next_review - now).days
                schedule[days_until].append({
                    'topic': topic,
                    'retention_score': item.retention_score,
                    'ease_factor': item.ease_factor,
                    'repetitions': item.repetitions,
                    'priority': self._calculate_review_priority(item)
                })
        
        # Sort by priority within each day
        for day in schedule:
            schedule[day].sort(key=lambda x: x['priority'], reverse=True)
        
        # Calculate forgetting curve predictions
        forgetting_curve = self._predict_forgetting_curve()
        
        return {
            'schedule': dict(schedule),
            'total_reviews': sum(len(items) for items in schedule.values()),
            'forgetting_curve_predictions': forgetting_curve,
            'recommendations': self._generate_review_recommendations(schedule)
        }
    
    def _calculate_review_priority(self, item: SpacedRepetitionItem) -> float:
        """Calculate review priority based on various factors."""
        now = datetime.now()
        
        # Time until next review (closer = higher priority)
        days_until = (item.next_review - now).days
        time_factor = max(0, 1 - days_until / 7)  # Higher when closer
        
        # Retention score (lower retention = higher priority)
        retention_factor = 1 - item.retention_score
        
        # Repetition count (newer items might need more attention)
        repetition_factor = min(1, 1 / (item.repetitions + 1))
        
        # Combine factors
        priority = 0.4 * time_factor + 0.4 * retention_factor + 0.2 * repetition_factor
        
        return priority
    
    def _predict_forgetting_curve(self) -> Dict[str, List[float]]:
        """Predict forgetting curves for topics."""
        predictions = {}
        
        for topic, item in self.repetition_items.items():
            if item.repetitions < 3:
                continue
            
            # Model forgetting curve: R = e^(-t/S)
            # where S is stability based on repetitions
            stability = item.interval * (0.5 + 0.1 * item.repetitions)
            
            # Predict retention for next 30 days
            days = list(range(31))
            retention = [
                np.exp(-d / stability) * item.retention_score
                for d in days
            ]
            
            predictions[topic] = retention
        
        return predictions
    
    def _generate_review_recommendations(self,
                                       schedule: Dict[int, List]) -> List[str]:
        """Generate recommendations for review optimization."""
        recommendations = []
        
        # Check for overdue items
        overdue = schedule.get(-1, [])
        if overdue:
            recommendations.append(
                f"You have {len(overdue)} overdue reviews. "
                "Prioritize these for better retention."
            )
        
        # Check for upcoming workload
        next_week = sum(len(schedule.get(i, [])) for i in range(1, 8))
        if next_week > 20:
            recommendations.append(
                f"Heavy review week ahead ({next_week} reviews). "
                "Consider spacing them out throughout the week."
            )
        elif next_week < 5:
            recommendations.append(
                "Light review week. Consider adding new topics to learn."
            )
        
        # Check for topics needing reinforcement
        low_retention = [
            t for t, item in self.repetition_items.items()
            if item.retention_score < 0.6
        ]
        if low_retention:
            recommendations.append(
                f"Topics needing reinforcement: {', '.join(low_retention[:3])}"
            )
        
        return recommendations
    
    async def detect_knowledge_gaps(self,
                                   current_topic: str,
                                   comprehension_score: float,
                                   retention_score: Optional[float]) -> List[KnowledgeGap]:
        """
        Detect knowledge gaps based on learning patterns.
        
        Args:
            current_topic: Topic being studied
            comprehension_score: Current comprehension
            retention_score: Retention if available
            
        Returns:
            List of identified knowledge gaps
        """
        gaps = []
        
        # Check for low comprehension
        if comprehension_score < 0.6:
            gap = KnowledgeGap(
                topic=current_topic,
                confidence=1 - comprehension_score,
                related_topics=self._find_related_topics(current_topic),
                suggested_resources=self._suggest_resources(current_topic),
                priority=3,
                identified_at=datetime.now()
            )
            gaps.append(gap)
        
        # Check for retention drop
        if retention_score is not None and retention_score < 0.5:
            # Check if this topic had better comprehension before
            previous_sessions = [
                s for s in self.sessions[-20:]
                if s.topic == current_topic and s.retention_score is not None
            ]
            
            if previous_sessions:
                avg_previous = np.mean([s.retention_score for s in previous_sessions])
                if avg_previous > retention_score + 0.2:
                    gap = KnowledgeGap(
                        topic=f"{current_topic} (reinforcement needed)",
                        confidence=avg_previous - retention_score,
                        related_topics=self._find_related_topics(current_topic),
                        suggested_resources=self._suggest_resources(current_topic, reinforcement=True),
                        priority=4,
                        identified_at=datetime.now()
                    )
                    gaps.append(gap)
        
        # Check for prerequisite gaps
        prerequisites = self._identify_prerequisites(current_topic)
        for prereq in prerequisites:
            mastery = self.topic_mastery.get(prereq, 0)
            if mastery < 0.5:
                gap = KnowledgeGap(
                    topic=prereq,
                    confidence=1 - mastery,
                    related_topics=[current_topic],
                    suggested_resources=self._suggest_resources(prereq),
                    priority=5 - int(mastery * 5),  # Higher priority for lower mastery
                    identified_at=datetime.now()
                )
                gaps.append(gap)
        
        # Add to knowledge gaps list
        self.knowledge_gaps.extend(gaps)
        
        # Keep only recent gaps
        cutoff = datetime.now() - timedelta(days=30)
        self.knowledge_gaps = [g for g in self.knowledge_gaps if g.identified_at > cutoff]
        
        return gaps
    
    def _find_related_topics(self, topic: str) -> List[str]:
        """Find topics related to the given topic."""
        related = []
        
        # Look for co-occurrence in sessions
        topic_sessions = [s for s in self.sessions if s.topic == topic]
        if topic_sessions:
            # Find other topics in same sessions
            for session in topic_sessions:
                if 'related_topics' in session.metadata:
                    related.extend(session.metadata['related_topics'])
            
            # Find topics studied around the same time
            session_times = [s.timestamp for s in topic_sessions]
            nearby_sessions = [
                s for s in self.sessions
                if any(abs((s.timestamp - t).total_seconds()) < 3600 for t in session_times)
                and s.topic != topic
            ]
            related.extend([s.topic for s in nearby_sessions])
        
        return list(set(related))[:5]  # Return unique, limit to 5
    
    def _identify_prerequisites(self, topic: str) -> List[str]:
        """Identify prerequisite topics."""
        prerequisites = []
        
        # Check metadata for explicitly defined prerequisites
        topic_sessions = [s for s in self.sessions if s.topic == topic]
        for session in topic_sessions:
            if 'prerequisites' in session.metadata:
                prerequisites.extend(session.metadata['prerequisites'])
        
        # Infer from topic relationships
        if topic_relationships := self.topic_relationships.get(topic):
            prerequisites.extend([rel for rel, strength in topic_relationships if strength > 0.5])
        
        return list(set(prerequisites))
    
    def _suggest_resources(self, topic: str, reinforcement: bool = False) -> List[str]:
        """Suggest learning resources for a topic."""
        suggestions = []
        
        # Find successful sessions for this topic
        successful_sessions = [
            s for s in self.sessions
            if s.topic == topic and s.comprehension_score > 0.8
        ]
        
        if successful_sessions:
            # Recommend content types that worked well
            content_types = [s.content_type.value for s in successful_sessions]
            suggestions.append(f"Try {', '.join(set(content_types[:3]))} formats")
        
        # Style-based suggestions
        style_analysis = asyncio.run(self.get_learning_style_analysis())
        primary_style = style_analysis.get('primary_style')
        
        style_resources = {
            'visual': "Look for video tutorials and visual explanations",
            'auditory': "Find podcasts or discussion groups on this topic",
            'reading': "Search for in-depth articles and documentation",
            'kinesthetic': "Work on hands-on projects and exercises"
        }
        
        if primary_style and primary_style in style_resources:
            suggestions.append(style_resources[primary_style])
        
        if reinforcement:
            suggestions.append("Use spaced repetition and practice tests")
        
        return suggestions
    
    async def get_learning_insights(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive learning insights."""
        recent_sessions = [
            s for s in self.sessions
            if s.timestamp > datetime.now() - timedelta(days=days)
        ]
        
        if not recent_sessions:
            return {'message': 'No recent learning data'}
        
        # Calculate learning velocity
        topics_by_day = defaultdict(set)
        for session in recent_sessions:
            day = session.timestamp.date()
            topics_by_day[day].add(session.topic)
        
        days_with_data = len(topics_by_day)
        total_topics = len(set(s.topic for s in recent_sessions))
        avg_topics_per_day = total_topics / max(days_with_data, 1)
        
        # Calculate comprehension trends
        comprehension_scores = [s.comprehension_score for s in recent_sessions]
        if len(comprehension_scores) > 1:
            comprehension_trend = stats.linregress(
                range(len(comprehension_scores)),
                comprehension_scores
            ).slope
        else:
            comprehension_trend = 0
        
        # Identify best learning times
        hour_scores = defaultdict(list)
        for session in recent_sessions:
            hour_scores[session.timestamp.hour].append(session.comprehension_score)
        
        best_hours = sorted(
            [(hour, np.mean(scores)) for hour, scores in hour_scores.items() if len(scores) >= 3],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return {
            'learning_velocity': {
                'topics_per_day': avg_topics_per_day,
                'total_topics': total_topics,
                'active_days': days_with_data
            },
            'comprehension_trend': comprehension_trend,
            'average_comprehension': np.mean(comprehension_scores),
            'best_learning_times': [hour for hour, _ in best_hours],
            'topic_mastery': dict(sorted(
                self.topic_mastery.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            'active_knowledge_gaps': len(self.knowledge_gaps),
            'spaced_repetition_items': len(self.repetition_items),
            'learning_style': await self.get_learning_style_analysis()
        }
    
    def _trim_history(self, max_entries: int = 5000):
        """Trim session history to prevent unlimited growth."""
        if len(self.sessions) > max_entries:
            self.sessions = self.sessions[-max_entries:]
    
    async def _save_data(self):
        """Save learning data to storage."""
        try:
            # Save sessions
            sessions_file = self.storage_path / "sessions.json"
            with open(sessions_file, 'w') as f:
                json.dump([
                    {
                        'session_id': s.session_id,
                        'topic': s.topic,
                        'content_type': s.content_type.value,
                        'duration': s.duration.total_seconds(),
                        'engagement_score': s.engagement_score,
                        'comprehension_score': s.comprehension_score,
                        'retention_score': s.retention_score,
                        'timestamp': s.timestamp.isoformat(),
                        'context': s.context,
                        'metadata': s.metadata
                    }
                    for s in self.sessions[-1000:]  # Save last 1000
                ], f, indent=2, default=str)
            
            # Save knowledge gaps
            gaps_file = self.storage_path / "knowledge_gaps.json"
            with open(gaps_file, 'w') as f:
                json.dump([
                    {
                        'topic': g.topic,
                        'confidence': g.confidence,
                        'related_topics': g.related_topics,
                        'suggested_resources': g.suggested_resources,
                        'priority': g.priority,
                        'identified_at': g.identified_at.isoformat()
                    }
                    for g in self.knowledge_gaps
                ], f, indent=2, default=str)
            
            # Save repetition items
            repetition_file = self.storage_path / "repetition.json"
            with open(repetition_file, 'w') as f:
                json.dump({
                    topic: {
                        'topic': item.topic,
                        'last_reviewed': item.last_reviewed.isoformat(),
                        'next_review': item.next_review.isoformat(),
                        'ease_factor': item.ease_factor,
                        'interval': item.interval,
                        'repetitions': item.repetitions,
                        'retention_score': item.retention_score
                    }
                    for topic, item in self.repetition_items.items()
                }, f, indent=2, default=str)
            
            logger.debug("Learning data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")