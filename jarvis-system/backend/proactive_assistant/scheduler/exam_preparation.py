"""
Exam Preparation Module - Enhanced version
Creates intelligent study plans and preparation schedules for exams.
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
from scipy import stats

logger = logging.getLogger(__name__)

class ExamPriority(Enum):
    """Priority levels for exams."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class StudySessionType(Enum):
    """Types of study sessions."""
    INITIAL_LEARNING = "initial_learning"
    REVIEW = "review"
    PRACTICE = "practice"
    DEEP_DIVE = "deep_dive"
    QUICK_REVIEW = "quick_review"
    MOCK_TEST = "mock_test"
    GROUP_STUDY = "group_study"

class TopicMastery(Enum):
    """Mastery levels for topics."""
    NOT_STARTED = "not_started"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    MASTERED = "mastered"

@dataclass
class StudyTopic:
    """Data class for study topics."""
    name: str
    estimated_hours: float
    priority: int  # 1-5
    difficulty: float  # 1-5
    mastery_level: TopicMastery
    prerequisites: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    notes: str = ""

@dataclass
class StudySession:
    """Data class for study sessions."""
    session_id: str
    topic: str
    session_type: StudySessionType
    start_time: datetime
    end_time: datetime
    duration_hours: float
    completed: bool = False
    effectiveness_score: Optional[float] = None
    notes: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StudyPlan:
    """Data class for comprehensive study plans."""
    plan_id: str
    exam_name: str
    exam_date: datetime
    priority: ExamPriority
    topics: List[StudyTopic]
    sessions: List[StudySession] = field(default_factory=list)
    total_study_hours: float = 0
    completed_hours: float = 0
    projected_score: Optional[float] = None
    confidence_level: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class ExamPreparation:
    """
    Enhanced exam preparation system that creates adaptive study plans
    based on time available, topic difficulty, and learning patterns.
    """
    
    def __init__(self, storage_path: str = "data/scheduler/exams"):
        """
        Initialize the exam preparation system.
        
        Args:
            storage_path: Path to store exam data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Study plans storage
        self.study_plans: Dict[str, StudyPlan] = {}
        self.active_sessions: Dict[str, StudySession] = {}
        
        # Learning efficiency metrics
        self.learning_rate_by_topic: Dict[str, float] = defaultdict(lambda: 1.0)
        self.retention_by_topic: Dict[str, float] = defaultdict(lambda: 0.7)
        self.optimal_session_duration = timedelta(hours=2)
        
        # Study effectiveness tracking
        self.study_effectiveness: Dict[StudySessionType, List[float]] = defaultdict(list)
        
        # Load existing data
        self._load_data()
        
        logger.info("ExamPreparation initialized successfully")
    
    def _load_data(self):
        """Load exam preparation data from storage."""
        plans_file = self.storage_path / "study_plans.json"
        
        if plans_file.exists():
            try:
                with open(plans_file, 'r') as f:
                    data = json.load(f)
                    for plan_id, plan_data in data.items():
                        # Convert topics
                        topics = []
                        for topic_data in plan_data['topics']:
                            topic = StudyTopic(
                                name=topic_data['name'],
                                estimated_hours=topic_data['estimated_hours'],
                                priority=topic_data['priority'],
                                difficulty=topic_data['difficulty'],
                                mastery_level=TopicMastery(topic_data['mastery_level']),
                                prerequisites=topic_data.get('prerequisites', []),
                                resources=topic_data.get('resources', []),
                                notes=topic_data.get('notes', '')
                            )
                            topics.append(topic)
                        
                        # Convert sessions
                        sessions = []
                        for session_data in plan_data.get('sessions', []):
                            session = StudySession(
                                session_id=session_data['session_id'],
                                topic=session_data['topic'],
                                session_type=StudySessionType(session_data['session_type']),
                                start_time=datetime.fromisoformat(session_data['start_time']),
                                end_time=datetime.fromisoformat(session_data['end_time']),
                                duration_hours=session_data['duration_hours'],
                                completed=session_data.get('completed', False),
                                effectiveness_score=session_data.get('effectiveness_score'),
                                notes=session_data.get('notes', ''),
                                context=session_data.get('context', {})
                            )
                            sessions.append(session)
                        
                        plan = StudyPlan(
                            plan_id=plan_id,
                            exam_name=plan_data['exam_name'],
                            exam_date=datetime.fromisoformat(plan_data['exam_date']),
                            priority=ExamPriority(plan_data['priority']),
                            topics=topics,
                            sessions=sessions,
                            total_study_hours=plan_data['total_study_hours'],
                            completed_hours=plan_data.get('completed_hours', 0),
                            projected_score=plan_data.get('projected_score'),
                            confidence_level=plan_data.get('confidence_level', 0.5),
                            created_at=datetime.fromisoformat(plan_data['created_at']),
                            updated_at=datetime.fromisoformat(plan_data['updated_at'])
                        )
                        self.study_plans[plan_id] = plan
                        
                logger.info(f"Loaded {len(self.study_plans)} study plans")
            except Exception as e:
                logger.error(f"Error loading study plans: {e}")
    
    async def create_study_plan(self,
                               exam_name: str,
                               exam_date: datetime,
                               topics: List[Dict[str, Any]],
                               priority: ExamPriority = ExamPriority.MEDIUM,
                               available_hours_per_day: float = 2.0) -> StudyPlan:
        """
        Create a comprehensive study plan for an exam.
        
        Args:
            exam_name: Name of the exam
            exam_date: Date of the exam
            topics: List of topics with details
            priority: Priority of the exam
            available_hours_per_day: Available study hours per day
            
        Returns:
            StudyPlan object
        """
        # Calculate days until exam
        days_until_exam = (exam_date - datetime.now()).days
        
        if days_until_exam <= 0:
            raise ValueError("Exam date must be in the future")
        
        # Convert topics to StudyTopic objects
        study_topics = []
        for topic_data in topics:
            topic = StudyTopic(
                name=topic_data['name'],
                estimated_hours=topic_data.get('estimated_hours', 5),
                priority=topic_data.get('priority', 3),
                difficulty=topic_data.get('difficulty', 3),
                mastery_level=TopicMastery(topic_data.get('mastery_level', 'not_started')),
                prerequisites=topic_data.get('prerequisites', []),
                resources=topic_data.get('resources', []),
                notes=topic_data.get('notes', '')
            )
            study_topics.append(topic)
        
        # Calculate total study hours needed
        total_hours = sum(t.estimated_hours for t in study_topics)
        
        # Check if feasible
        max_possible_hours = days_until_exam * available_hours_per_day
        
        if total_hours > max_possible_hours:
            logger.warning(f"Study plan may be too ambitious: {total_hours} hours needed, "
                          f"only {max_possible_hours} hours available")
            
            # Adjust by prioritizing high-priority topics
            study_topics.sort(key=lambda t: (-t.priority, t.difficulty))
            
            # Recalculate feasible total
            feasible_topics = []
            remaining_hours = max_possible_hours
            
            for topic in study_topics:
                if topic.estimated_hours <= remaining_hours:
                    feasible_topics.append(topic)
                    remaining_hours -= topic.estimated_hours
                else:
                    # Partially cover this topic
                    topic.estimated_hours = remaining_hours
                    feasible_topics.append(topic)
                    break
            
            study_topics = feasible_topics
            total_hours = sum(t.estimated_hours for t in study_topics)
        
        # Create study plan
        plan_id = self._generate_plan_id(exam_name)
        
        # Sort topics by prerequisites and priority
        study_topics = self._sort_topics_by_dependencies(study_topics)
        
        # Generate study sessions
        sessions = await self._generate_study_sessions(
            study_topics,
            exam_date,
            available_hours_per_day
        )
        
        # Calculate projected score based on time and difficulty
        projected_score = self._calculate_projected_score(study_topics, sessions, days_until_exam)
        
        # Determine confidence level
        confidence = min(1.0, (max_possible_hours / total_hours) * 0.8 + 0.2)
        
        plan = StudyPlan(
            plan_id=plan_id,
            exam_name=exam_name,
            exam_date=exam_date,
            priority=priority,
            topics=study_topics,
            sessions=sessions,
            total_study_hours=total_hours,
            projected_score=projected_score,
            confidence_level=confidence,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.study_plans[plan_id] = plan
        
        # Save data
        await self._save_data()
        
        logger.info(f"Created study plan for {exam_name} with {len(sessions)} sessions")
        
        return plan
    
    def _sort_topics_by_dependencies(self, topics: List[StudyTopic]) -> List[StudyTopic]:
        """Sort topics based on prerequisites."""
        # Create dependency graph
        topic_names = [t.name for t in topics]
        topic_dict = {t.name: t for t in topics}
        
        # Build adjacency list
        graph = {name: [] for name in topic_names}
        for topic in topics:
            for prereq in topic.prerequisites:
                if prereq in topic_dict:
                    graph[prereq].append(topic.name)
        
        # Topological sort
        visited = set()
        temp_visited = set()
        order = []
        
        def dfs(topic_name):
            if topic_name in temp_visited:
                # Cycle detected, ignore
                return
            if topic_name in visited:
                return
            
            temp_visited.add(topic_name)
            
            for neighbor in graph[topic_name]:
                dfs(neighbor)
            
            temp_visited.remove(topic_name)
            visited.add(topic_name)
            order.append(topic_name)
        
        for topic_name in topic_names:
            if topic_name not in visited:
                dfs(topic_name)
        
        # Reverse to get correct order
        order.reverse()
        
        # Return topics in order
        return [topic_dict[name] for name in order if name in topic_dict]
    
    async def _generate_study_sessions(self,
                                      topics: List[StudyTopic],
                                      exam_date: datetime,
                                      hours_per_day: float) -> List[StudySession]:
        """Generate optimal study sessions."""
        sessions = []
        current_date = datetime.now()
        days_until_exam = (exam_date - current_date).days
        
        # Distribute topics across available days
        total_hours = sum(t.estimated_hours for t in topics)
        hours_per_topic = {t.name: t.estimated_hours for t in topics}
        
        # Create study schedule
        session_id_counter = 0
        
        for day in range(days_until_exam):
            study_date = current_date + timedelta(days=day)
            daily_hours = 0
            
            # Skip weekends if desired? (configurable)
            if study_date.weekday() >= 5:  # Weekend
                daily_hours = hours_per_day * 0.7  # Reduced hours on weekends
            else:
                daily_hours = hours_per_day
            
            # Allocate time to topics based on priority and days remaining
            remaining_days = days_until_exam - day
            if remaining_days <= 0:
                break
            
            # Calculate priority weights
            priority_weights = []
            for topic in topics:
                if hours_per_topic[topic.name] > 0:
                    # Higher priority and closer to exam = higher weight
                    time_factor = 1.0 + (1.0 - day / days_until_exam) * 0.5
                    priority_weights.append(topic.priority * time_factor)
                else:
                    priority_weights.append(0)
            
            total_weight = sum(priority_weights)
            
            if total_weight > 0:
                # Allocate hours to topics
                for i, topic in enumerate(topics):
                    if hours_per_topic[topic.name] <= 0:
                        continue
                    
                    topic_hours = daily_hours * (priority_weights[i] / total_weight)
                    topic_hours = min(topic_hours, hours_per_topic[topic.name])
                    
                    if topic_hours > 0.25:  # At least 15 minutes
                        # Determine session type
                        if hours_per_topic[topic.name] == topic.estimated_hours:
                            # First time studying this topic
                            session_type = StudySessionType.INITIAL_LEARNING
                        elif day > days_until_exam - 3:
                            # Near exam, do review
                            session_type = StudySessionType.REVIEW
                        else:
                            session_type = StudySessionType.PRACTICE
                        
                        # Create session
                        session_id = f"session_{session_id_counter}_{topic.name}"
                        session_id_counter += 1
                        
                        # Split into multiple sessions if too long
                        if topic_hours > 2.5:
                            # Break into 2-hour chunks
                            num_sessions = int(np.ceil(topic_hours / 2))
                            for j in range(num_sessions):
                                session_hours = min(2, topic_hours - j * 2)
                                if session_hours < 0.5:
                                    continue
                                
                                start_time = study_date.replace(hour=9 + j * 2, minute=0)
                                if start_time.hour > 20:  # Too late
                                    start_time = study_date.replace(hour=9, minute=0)
                                
                                session = StudySession(
                                    session_id=f"{session_id}_part{j}",
                                    topic=topic.name,
                                    session_type=session_type,
                                    start_time=start_time,
                                    end_time=start_time + timedelta(hours=session_hours),
                                    duration_hours=session_hours,
                                    context={'day': day, 'part': j}
                                )
                                sessions.append(session)
                                hours_per_topic[topic.name] -= session_hours
                        else:
                            # Single session
                            start_time = study_date.replace(hour=9, minute=0)
                            
                            session = StudySession(
                                session_id=session_id,
                                topic=topic.name,
                                session_type=session_type,
                                start_time=start_time,
                                end_time=start_time + timedelta(hours=topic_hours),
                                duration_hours=topic_hours,
                                context={'day': day}
                            )
                            sessions.append(session)
                            hours_per_topic[topic.name] -= topic_hours
        
        # Sort sessions by time
        sessions.sort(key=lambda s: s.start_time)
        
        return sessions
    
    def _calculate_projected_score(self,
                                  topics: List[StudyTopic],
                                  sessions: List[StudySession],
                                  days_until_exam: int) -> float:
        """Calculate projected exam score based on study plan."""
        if not topics or not sessions:
            return 0.5
        
        # Base score on topic coverage
        total_weight = sum(t.priority * t.estimated_hours for t in topics)
        if total_weight == 0:
            return 0.5
        
        weighted_score = 0
        for topic in topics:
            # Find sessions for this topic
            topic_sessions = [s for s in sessions if s.topic == topic.name]
            hours_studied = sum(s.duration_hours for s in topic_sessions)
            
            # Coverage ratio
            coverage = min(1.0, hours_studied / topic.estimated_hours)
            
            # Adjust for difficulty (harder topics need more time)
            difficulty_factor = 1.0 / topic.difficulty
            
            # Time until exam (recent study is more valuable)
            recency_factor = 1.0
            if topic_sessions:
                last_session = max(s.end_time for s in topic_sessions)
                days_since = (datetime.now() - last_session).days
                if days_since > 7:
                    recency_factor = max(0.5, 1.0 - days_since / 30)
            
            topic_score = coverage * (1.0 + difficulty_factor) * recency_factor
            weighted_score += topic_score * topic.priority * topic.estimated_hours
        
        # Normalize
        projected = weighted_score / total_weight
        
        # Ensure between 0 and 1
        return max(0.1, min(0.99, projected))
    
    def _generate_plan_id(self, exam_name: str) -> str:
        """Generate a unique plan ID."""
        import hashlib
        import random
        
        unique_string = f"{exam_name}_{datetime.now().isoformat()}_{random.random()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    async def get_study_plan(self, plan_id: str) -> Optional[StudyPlan]:
        """Get a study plan by ID."""
        return self.study_plans.get(plan_id)
    
    async def update_session_completion(self,
                                       session_id: str,
                                       effectiveness: Optional[float] = None,
                                       notes: str = "") -> bool:
        """Mark a study session as completed."""
        for plan in self.study_plans.values():
            for session in plan.sessions:
                if session.session_id == session_id and not session.completed:
                    session.completed = True
                    session.effectiveness_score = effectiveness
                    session.notes = notes
                    
                    # Update plan stats
                    plan.completed_hours += session.duration_hours
                    plan.updated_at = datetime.now()
                    
                    # Update learning rate for this topic
                    if effectiveness:
                        current_rate = self.learning_rate_by_topic[session.topic]
                        self.learning_rate_by_topic[session.topic] = 0.7 * current_rate + 0.3 * effectiveness
                    
                    # Update study effectiveness tracking
                    self.study_effectiveness[session.session_type].append(effectiveness or 0.7)
                    
                    # Recalculate projected score
                    days_until_exam = (plan.exam_date - datetime.now()).days
                    plan.projected_score = self._calculate_projected_score(
                        plan.topics, plan.sessions, days_until_exam
                    )
                    
                    # Save data
                    await self._save_data()
                    
                    logger.info(f"Session {session_id} completed with effectiveness {effectiveness}")
                    return True
        
        return False
    
    async def get_next_study_session(self, plan_id: str) -> Optional[StudySession]:
        """Get the next upcoming study session for a plan."""
        plan = self.study_plans.get(plan_id)
        if not plan:
            return None
        
        now = datetime.now()
        upcoming = [
            s for s in plan.sessions
            if not s.completed and s.start_time > now
        ]
        
        if upcoming:
            return min(upcoming, key=lambda s: s.start_time)
        
        return None
    
    async def get_today_sessions(self, plan_id: str) -> List[StudySession]:
        """Get today's study sessions for a plan."""
        plan = self.study_plans.get(plan_id)
        if not plan:
            return []
        
        today = datetime.now().date()
        return [
            s for s in plan.sessions
            if not s.completed and s.start_time.date() == today
        ]
    
    async def adjust_plan(self, plan_id: str, new_hours_per_day: Optional[float] = None) -> Optional[StudyPlan]:
        """Adjust study plan based on progress."""
        plan = self.study_plans.get(plan_id)
        if not plan:
            return None
        
        # Calculate remaining hours
        completed_sessions = [s for s in plan.sessions if s.completed]
        completed_hours = sum(s.duration_hours for s in completed_sessions)
        
        remaining_hours = plan.total_study_hours - completed_hours
        
        if remaining_hours <= 0:
            # All done!
            return plan
        
        # Calculate days until exam
        days_until_exam = (plan.exam_date - datetime.now()).days
        
        if days_until_exam <= 0:
            logger.warning(f"Exam date passed for plan {plan_id}")
            return plan
        
        # Calculate required daily hours
        required_daily = remaining_hours / days_until_exam
        
        # Check if still feasible
        if new_hours_per_day:
            available_daily = new_hours_per_day
        else:
            # Estimate based on past performance
            if completed_sessions:
                avg_session_length = np.mean([s.duration_hours for s in completed_sessions])
                available_daily = avg_session_length * 1.2  # Slight increase
            else:
                available_daily = 2.0  # Default
        
        if required_daily > available_daily * 1.2:
            # Need to reprioritize
            logger.info(f"Adjusting plan {plan_id}: need {required_daily:.1f}h/day, "
                       f"can do {available_daily:.1f}h/day")
            
            # Get incomplete topics
            completed_topics = set(s.topic for s in completed_sessions)
            incomplete_topics = [
                t for t in plan.topics
                if t.name not in completed_topics
            ]
            
            # Sort by priority
            incomplete_topics.sort(key=lambda t: (-t.priority, t.difficulty))
            
            # Calculate new total feasible hours
            max_possible = days_until_exam * available_daily
            new_total = 0
            feasible_topics = []
            
            for topic in incomplete_topics:
                if new_total + topic.estimated_hours <= max_possible:
                    feasible_topics.append(topic)
                    new_total += topic.estimated_hours
                else:
                    # Partial coverage
                    remaining = max_possible - new_total
                    if remaining > 0.5:
                        topic.estimated_hours = remaining
                        feasible_topics.append(topic)
                    break
            
            # Update plan
            plan.topics = feasible_topics + [t for t in plan.topics if t.name in completed_topics]
            plan.total_study_hours = completed_hours + new_total
            
            # Regenerate sessions for remaining topics
            new_sessions = await self._generate_study_sessions(
                feasible_topics,
                plan.exam_date,
                available_daily
            )
            
            # Keep completed sessions
            plan.sessions = completed_sessions + new_sessions
            plan.updated_at = datetime.now()
            
            # Recalculate projected score
            plan.projected_score = self._calculate_projected_score(
                plan.topics, plan.sessions, days_until_exam
            )
            
            await self._save_data()
        
        return plan
    
    async def get_study_recommendations(self, plan_id: str) -> Dict[str, Any]:
        """Get personalized study recommendations."""
        plan = self.study_plans.get(plan_id)
        if not plan:
            return {'error': 'Plan not found'}
        
        recommendations = []
        
        # Calculate progress
        progress = (plan.completed_hours / plan.total_study_hours) * 100 if plan.total_study_hours > 0 else 0
        
        # Check if behind schedule
        days_until_exam = (plan.exam_date - datetime.now()).days
        days_passed = (datetime.now() - plan.created_at).days
        expected_progress = (days_passed / max(days_passed + days_until_exam, 1)) * 100
        
        if progress < expected_progress - 10:
            recommendations.append({
                'type': 'warning',
                'message': f"You're behind schedule. Consider increasing daily study time "
                          f"or focusing on high-priority topics."
            })
        
        # Identify weak topics
        topic_effectiveness = defaultdict(list)
        for session in plan.sessions:
            if session.completed and session.effectiveness_score:
                topic_effectiveness[session.topic].append(session.effectiveness_score)
        
        weak_topics = []
        for topic, scores in topic_effectiveness.items():
            avg_effectiveness = np.mean(scores)
            if avg_effectiveness < 0.6 and len(scores) >= 2:
                weak_topics.append({
                    'topic': topic,
                    'effectiveness': avg_effectiveness,
                    'sessions': len(scores)
                })
        
        if weak_topics:
            recommendations.append({
                'type': 'weak_topics',
                'message': "These topics need more attention:",
                'topics': weak_topics
            })
        
        # Recommend study techniques based on time until exam
        if days_until_exam < 3:
            recommendations.append({
                'type': 'technique',
                'message': "Focus on active recall and practice tests rather than passive reading."
            })
        elif days_until_exam < 7:
            recommendations.append({
                'type': 'technique',
                'message': "Use spaced repetition and teach concepts to others to reinforce learning."
            })
        
        # Analyze session effectiveness
        if self.study_effectiveness:
            best_session_type = max(
                self.study_effectiveness.items(),
                key=lambda x: np.mean(x[1]) if x[1] else 0
            )
            recommendations.append({
                'type': 'insight',
                'message': f"Your most effective study sessions are {best_session_type[0].value}. "
                          f"Consider incorporating more of these."
            })
        
        return {
            'plan_id': plan_id,
            'exam_name': plan.exam_name,
            'days_until_exam': days_until_exam,
            'progress_percentage': progress,
            'completed_hours': plan.completed_hours,
            'remaining_hours': plan.total_study_hours - plan.completed_hours,
            'projected_score': plan.projected_score,
            'recommendations': recommendations
        }
    
    async def get_all_plans_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all study plans."""
        summaries = []
        
        for plan_id, plan in self.study_plans.items():
            progress = (plan.completed_hours / plan.total_study_hours) * 100 if plan.total_study_hours > 0 else 0
            
            summaries.append({
                'plan_id': plan_id,
                'exam_name': plan.exam_name,
                'exam_date': plan.exam_date.isoformat(),
                'days_until': (plan.exam_date - datetime.now()).days,
                'priority': plan.priority.value,
                'progress': progress,
                'projected_score': plan.projected_score,
                'confidence': plan.confidence_level,
                'total_hours': plan.total_study_hours,
                'completed_hours': plan.completed_hours
            })
        
        # Sort by exam date (closest first)
        summaries.sort(key=lambda x: x['days_until'])
        
        return summaries
    
    async def _save_data(self):
        """Save exam preparation data to storage."""
        try:
            plans_file = self.storage_path / "study_plans.json"
            
            plans_data = {}
            for plan_id, plan in self.study_plans.items():
                plans_data[plan_id] = {
                    'exam_name': plan.exam_name,
                    'exam_date': plan.exam_date.isoformat(),
                    'priority': plan.priority.value,
                    'topics': [
                        {
                            'name': t.name,
                            'estimated_hours': t.estimated_hours,
                            'priority': t.priority,
                            'difficulty': t.difficulty,
                            'mastery_level': t.mastery_level.value,
                            'prerequisites': t.prerequisites,
                            'resources': t.resources,
                            'notes': t.notes
                        }
                        for t in plan.topics
                    ],
                    'sessions': [
                        {
                            'session_id': s.session_id,
                            'topic': s.topic,
                            'session_type': s.session_type.value,
                            'start_time': s.start_time.isoformat(),
                            'end_time': s.end_time.isoformat(),
                            'duration_hours': s.duration_hours,
                            'completed': s.completed,
                            'effectiveness_score': s.effectiveness_score,
                            'notes': s.notes,
                            'context': s.context
                        }
                        for s in plan.sessions
                    ],
                    'total_study_hours': plan.total_study_hours,
                    'completed_hours': plan.completed_hours,
                    'projected_score': plan.projected_score,
                    'confidence_level': plan.confidence_level,
                    'created_at': plan.created_at.isoformat(),
                    'updated_at': plan.updated_at.isoformat()
                }
            
            with open(plans_file, 'w') as f:
                json.dump(plans_data, f, indent=2, default=str)
            
            logger.debug("Exam preparation data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving exam preparation data: {e}")