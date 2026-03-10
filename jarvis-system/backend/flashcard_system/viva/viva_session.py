"""
Viva Session module for managing oral examination sessions.
Handles session state, question flow, timing, and scoring.
"""

import asyncio
import uuid
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple, Set
import numpy as np

from pydantic import BaseModel, Field, field_validator

from .adaptive_questioner import (
    AdaptiveQuestioner,
    QuestionDifficulty,
    QuestionType,
    EmotionalState,
    Question,
    AnswerEvaluation
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VivaMode(Enum):
    """Operating modes for viva sessions."""
    PRACTICE = "practice"  # Unlimited time, learn at own pace
    TIMED = "timed"  # Time-limited session
    ADAPTIVE = "adaptive"  # Difficulty adapts to performance
    MOCK = "mock"  # Simulates real exam with fixed questions
    RESEARCH = "research"  # Experimental mode for testing


class VivaState(Enum):
    """States of a viva session."""
    CREATED = "created"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    ERROR = "error"



@dataclass
class SessionConfig:
    """Configuration for a viva session."""
    mode: VivaMode = VivaMode.PRACTICE
    duration_minutes: Optional[int] = None
    total_questions: Optional[int] = None
    initial_difficulty: QuestionDifficulty = QuestionDifficulty.MEDIUM
    passing_score: float = 60.0
    time_per_question_seconds: Optional[int] = None
    allow_skip: bool = True
    max_skips: int = 3
    show_hints: bool = True
    enable_emotion_tracking: bool = True
    enable_feedback: bool = True
    adaptive_difficulty: bool = True
    question_types: List[QuestionType] = field(default_factory=lambda: list(QuestionType))
    topics: List[str] = field(default_factory=list)
    subtopics: List[str] = field(default_factory=list)
    include_diagrams: bool = False
    require_drawing: bool = False
    custom_config: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self):
        """Validate configuration."""
        if self.mode == VivaMode.TIMED and not self.duration_minutes:
            raise ValueError("Timed mode requires duration_minutes")
        
        if self.mode == VivaMode.MOCK and not self.total_questions:
            raise ValueError("Mock mode requires total_questions")
        
        if self.duration_minutes and self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        
        if self.total_questions and self.total_questions <= 0:
            raise ValueError("total_questions must be positive")
        
        if not 0 <= self.passing_score <= 100:
            raise ValueError("passing_score must be between 0 and 100")


@dataclass
class Answer:
    """Student's answer to a question."""
    question_id: str
    answer_text: str
    response_time: float  # seconds
    confidence: float = 0.5  # 0-1 self-reported confidence
    emotional_state: Optional[Dict[str, Any]] = None
    attachments: Optional[List[str]] = None  # URLs or paths to diagrams/code
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'question_id': self.question_id,
            'answer_text': self.answer_text,
            'response_time': self.response_time,
            'confidence': self.confidence,
            'emotional_state': self.emotional_state,
            'attachments': self.attachments,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Feedback:
    """Feedback on an answer."""
    question_id: str
    evaluation: AnswerEvaluation
    score: float  # 0-100
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    hints: Optional[List[str]] = None
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    suggested_review: Optional[str] = None
    resources: List[Dict[str, str]] = field(default_factory=list)
    emotional_feedback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'question_id': self.question_id,
            'evaluation': self.evaluation.value,
            'score': self.score,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'hints': self.hints,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'suggested_review': self.suggested_review,
            'resources': self.resources,
            'emotional_feedback': self.emotional_feedback,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class QuestionRecord:
    """Record of a question and its answer."""
    question: Question
    answer: Optional[Answer] = None
    feedback: Optional[Feedback] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    skipped: bool = False
    timeout: bool = False
    
    @property
    def duration(self) -> Optional[float]:
        """Get time taken to answer in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def score(self) -> float:
        """Get score for this question."""
        if self.feedback:
            return self.feedback.score
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'question': self.question.to_dict(),
            'answer': self.answer.to_dict() if self.answer else None,
            'feedback': self.feedback.to_dict() if self.feedback else None,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'skipped': self.skipped,
            'timeout': self.timeout,
            'score': self.score
        }


class SessionMetrics:
    """Metrics collector for viva sessions."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.reset()
    
    def reset(self):
        """Reset all metrics."""
        self.question_count = 0
        self.correct_count = 0
        self.partial_count = 0
        self.incorrect_count = 0
        self.skipped_count = 0
        self.timeout_count = 0
        self.total_score = 0.0
        self.total_response_time = 0.0
        self.difficulty_progression = []
        self.emotional_states = []
        self.confidence_scores = []
        self.topic_performance = {}
        self.difficulty_performance = {
            QuestionDifficulty.VERY_EASY: {'correct': 0, 'total': 0},
            QuestionDifficulty.EASY: {'correct': 0, 'total': 0},
            QuestionDifficulty.MEDIUM: {'correct': 0, 'total': 0},
            QuestionDifficulty.HARD: {'correct': 0, 'total': 0},
            QuestionDifficulty.VERY_HARD: {'correct': 0, 'total': 0},
            QuestionDifficulty.EXPERT: {'correct': 0, 'total': 0}
        }
    
    def record_question(
        self,
        question: Question,
        answer: Optional[Answer],
        feedback: Feedback
    ):
        """Record metrics for a question."""
        self.question_count += 1
        
        # Track by difficulty
        diff = question.difficulty
        if diff in self.difficulty_performance:
            self.difficulty_performance[diff]['total'] += 1
            if feedback.evaluation == AnswerEvaluation.CORRECT:
                self.difficulty_performance[diff]['correct'] += 1
        
        # Track by topic
        topic = question.topic
        if topic not in self.topic_performance:
            self.topic_performance[topic] = {'correct': 0, 'partial': 0, 'incorrect': 0, 'total': 0}
        
        self.topic_performance[topic]['total'] += 1
        
        if feedback.evaluation == AnswerEvaluation.CORRECT:
            self.correct_count += 1
            self.topic_performance[topic]['correct'] += 1
        elif feedback.evaluation == AnswerEvaluation.PARTIALLY_CORRECT:
            self.partial_count += 1
            self.topic_performance[topic]['partial'] += 1
        else:
            self.incorrect_count += 1
            self.topic_performance[topic]['incorrect'] += 1
        
        if answer:
            self.total_response_time += answer.response_time
            self.confidence_scores.append(answer.confidence)
        
        self.total_score += feedback.score
        self.difficulty_progression.append(question.difficulty.value)
    
    def record_emotional_state(self, emotional_state: Dict[str, Any]):
        """Record emotional state."""
        self.emotional_states.append({
            'timestamp': datetime.now().isoformat(),
            'state': emotional_state
        })
    
    def get_average_score(self) -> float:
        """Get average score across all questions."""
        if self.question_count == 0:
            return 0.0
        return self.total_score / self.question_count
    
    def get_average_response_time(self) -> float:
        """Get average response time."""
        if self.question_count == 0:
            return 0.0
        return self.total_response_time / self.question_count
    
    def get_success_rate(self) -> float:
        """Get success rate (correct + partial)."""
        if self.question_count == 0:
            return 0.0
        successful = self.correct_count + self.partial_count
        return (successful / self.question_count) * 100
    
    def get_difficulty_mastery(self, difficulty: QuestionDifficulty) -> float:
        """Get mastery rate for a specific difficulty."""
        perf = self.difficulty_performance.get(difficulty, {'correct': 0, 'total': 0})
        if perf['total'] == 0:
            return 0.0
        return (perf['correct'] / perf['total']) * 100
    
    def get_weak_topics(self, threshold: float = 60.0) -> List[Tuple[str, float]]:
        """Get topics with performance below threshold."""
        weak = []
        for topic, perf in self.topic_performance.items():
            if perf['total'] > 0:
                success = (perf['correct'] + perf['partial'] * 0.5) / perf['total'] * 100
                if success < threshold:
                    weak.append((topic, success))
        return sorted(weak, key=lambda x: x[1])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'question_count': self.question_count,
            'correct_count': self.correct_count,
            'partial_count': self.partial_count,
            'incorrect_count': self.incorrect_count,
            'skipped_count': self.skipped_count,
            'timeout_count': self.timeout_count,
            'total_score': self.total_score,
            'average_score': self.get_average_score(),
            'average_response_time': self.get_average_response_time(),
            'success_rate': self.get_success_rate(),
            'difficulty_progression': self.difficulty_progression,
            'topic_performance': self.topic_performance,
            'difficulty_performance': {
                k.value: v for k, v in self.difficulty_performance.items()
            },
            'average_confidence': np.mean(self.confidence_scores) if self.confidence_scores else 0,
            'emotional_patterns': self._analyze_emotional_patterns()
        }
    
    def _analyze_emotional_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in emotional states."""
        if not self.emotional_states:
            return {}
        
        emotions = []
        for state in self.emotional_states:
            if 'state' in state and 'primary_emotion' in state['state']:
                emotions.append(state['state']['primary_emotion'])
        
        from collections import Counter
        emotion_counts = Counter(emotions)
        
        return {
            'most_common': emotion_counts.most_common(3),
            'unique_emotions': len(emotion_counts),
            'total_recorded': len(self.emotional_states)
        }


class VivaSession:
    """
    Main class for managing viva (oral exam) sessions.
    Handles session lifecycle, question flow, timing, and scoring.
    """
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        topic: str,
        subtopics: List[str],
        config: SessionConfig,
        questioner: AdaptiveQuestioner
    ):
        """
        Initialize a viva session.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            topic: Main topic
            subtopics: List of subtopics
            config: Session configuration
            questioner: Adaptive questioner instance
        """
        self.session_id = session_id
        self.user_id = user_id
        self.topic = topic
        self.subtopics = subtopics
        self.config = config
        self.questioner = questioner
        
        # Session state
        self.state = VivaState.CREATED
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.pause_time: Optional[datetime] = None
        self.total_paused_seconds: float = 0.0
        
        # Question management
        self.current_question: Optional[Question] = None
        self.current_question_start: Optional[datetime] = None
        self.question_history: List[QuestionRecord] = []
        self.asked_question_ids: Set[str] = set()
        
        # Metrics
        self.metrics = SessionMetrics()
        
        # Preloaded questions
        self.question_queue: asyncio.Queue = asyncio.Queue(maxsize=10)
        self._preload_task: Optional[asyncio.Task] = None
        
        # Locks for thread safety
        self._state_lock = asyncio.Lock()
        self._metrics_lock = asyncio.Lock()
        
        logger.info(f"Created viva session {session_id} for user {user_id} on topic: {topic}")
    
    async def add_questions(self, questions: List[Question]):
        """
        Add a list of pre-generated questions to the session queue.
        
        Args:
            questions: List of Question objects
        """
        for question in questions:
            try:
                await self.question_queue.put(question)
                self.asked_question_ids.add(question.id)
            except asyncio.QueueFull:
                logger.warning(f"Question queue full for session {self.session_id}")
                break
        
        logger.info(f"Added {len(questions)} pre-generated questions to session {self.session_id}")

    async def start(self) -> Optional[Question]:
        """
        Start the viva session.
        
        Returns:
            First question or None if failed
        """
        async with self._state_lock:
            if self.state != VivaState.CREATED:
                raise ValueError(f"Cannot start session in state: {self.state}")
            
            self.state = VivaState.INITIALIZING
            self.start_time = datetime.now()
            
            logger.info(f"Starting viva session {self.session_id}")
        
        try:
            # Start preloading questions
            self._preload_task = asyncio.create_task(self._preload_questions())
            
            # Get first question
            first_question = await self._get_next_question()
            
            async with self._state_lock:
                self.state = VivaState.ACTIVE
                self.current_question = first_question
                self.current_question_start = datetime.now()
            
            logger.info(f"Session {self.session_id} started with first question")
            return first_question
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            async with self._state_lock:
                self.state = VivaState.ERROR
            raise
    
    async def pause(self):
        """Pause the session."""
        async with self._state_lock:
            if self.state != VivaState.ACTIVE:
                raise ValueError(f"Cannot pause session in state: {self.state}")
            
            self.state = VivaState.PAUSED
            self.pause_time = datetime.now()
            logger.info(f"Session {self.session_id} paused")
    
    async def resume(self):
        """Resume a paused session."""
        async with self._state_lock:
            if self.state != VivaState.PAUSED:
                raise ValueError(f"Cannot resume session in state: {self.state}")
            
            if self.pause_time:
                pause_duration = (datetime.now() - self.pause_time).total_seconds()
                self.total_paused_seconds += pause_duration
                self.pause_time = None
            
            self.state = VivaState.ACTIVE
            logger.info(f"Session {self.session_id} resumed")
    
    async def end(self) -> Dict[str, Any]:
        """
        End the session and generate summary.
        
        Returns:
            Session summary
        """
        async with self._state_lock:
            if self.state in [VivaState.COMPLETED, VivaState.TERMINATED]:
                logger.warning(f"Session {self.session_id} already ended")
                return await self.get_summary()
            
            self.state = VivaState.COMPLETED
            self.end_time = datetime.now()
        
        # Cancel preload task
        if self._preload_task and not self._preload_task.done():
            self._preload_task.cancel()
            try:
                await self._preload_task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"Session {self.session_id} ended")
        return await self.get_summary()
    
    async def answer_question(
        self,
        answer: Answer
    ) -> Tuple[Optional[Feedback], Optional[Question]]:
        """
        Submit an answer for the current question.
        
        Args:
            answer: Student's answer
            
        Returns:
            Tuple of (feedback, next_question)
        """
        async with self._state_lock:
            if self.state != VivaState.ACTIVE:
                raise ValueError(f"Cannot answer in state: {self.state}")
            
            if not self.current_question:
                raise ValueError("No active question")
            
            if answer.question_id != self.current_question.id:
                raise ValueError("Answer does not match current question")
        
        # Calculate time taken
        time_taken = (datetime.now() - self.current_question_start).total_seconds()
        
        # Check for timeout
        if self.config.time_per_question_seconds:
            if time_taken > self.config.time_per_question_seconds:
                return await self._handle_timeout()
        
        # Evaluate answer
        feedback = await self._evaluate_answer(self.current_question, answer, time_taken)
        
        # Record emotional state if provided
        if answer.emotional_state and self.config.enable_emotion_tracking:
            self.metrics.record_emotional_state(answer.emotional_state)
        
        # Create question record
        record = QuestionRecord(
            question=self.current_question,
            answer=answer,
            feedback=feedback,
            start_time=self.current_question_start,
            end_time=datetime.now()
        )
        
        # Update metrics
        async with self._metrics_lock:
            self.question_history.append(record)
            self.metrics.record_question(self.current_question, answer, feedback)
        
        # Get next question
        next_question = await self._get_next_question(feedback)
        
        # Update current question
        async with self._state_lock:
            self.current_question = next_question
            self.current_question_start = datetime.now() if next_question else None
        
        logger.debug(f"Question {self.current_question.id if self.current_question else 'None'} answered")
        
        return feedback, next_question
    
    async def skip_question(self) -> Optional[Question]:
        """
        Skip the current question.
        
        Returns:
            Next question or None
        """
        async with self._state_lock:
            if not self.config.allow_skip:
                raise ValueError("Skipping not allowed")
            
            if self.metrics.skipped_count >= self.config.max_skips:
                raise ValueError("Maximum skips reached")
        
        # Record skipped question
        if self.current_question:
            record = QuestionRecord(
                question=self.current_question,
                start_time=self.current_question_start,
                end_time=datetime.now(),
                skipped=True
            )
            
            async with self._metrics_lock:
                self.question_history.append(record)
                self.metrics.skipped_count += 1
        
        # Get next question
        next_question = await self._get_next_question()
        
        async with self._state_lock:
            self.current_question = next_question
            self.current_question_start = datetime.now() if next_question else None
        
        return next_question
    
    async def _handle_timeout(self) -> Tuple[Feedback, Optional[Question]]:
        """Handle question timeout."""
        feedback = Feedback(
            question_id=self.current_question.id,
            evaluation=AnswerEvaluation.TIMEOUT,
            score=0,
            explanation="Time limit exceeded"
        )
        
        record = QuestionRecord(
            question=self.current_question,
            start_time=self.current_question_start,
            end_time=datetime.now(),
            timeout=True
        )
        
        async with self._metrics_lock:
            self.question_history.append(record)
            self.metrics.timeout_count += 1
        
        next_question = await self._get_next_question(feedback)
        
        async with self._state_lock:
            self.current_question = next_question
            self.current_question_start = datetime.now() if next_question else None
        
        return feedback, next_question
    
    async def _evaluate_answer(
        self,
        question: Question,
        answer: Answer,
        time_taken: float
    ) -> Feedback:
        """
        Evaluate the student's answer.
        
        Args:
            question: The question being answered
            answer: Student's answer
            time_taken: Time taken to answer
            
        Returns:
            Feedback object
        """
        # Use questioner to evaluate
        evaluation = await self.questioner.evaluate_answer(
            question=question,
            answer_text=answer.answer_text,
            expected_answer=question.answer,
            context={
                'time_taken': time_taken,
                'confidence': answer.confidence,
                'emotional_state': answer.emotional_state,
                'topic': question.topic,
                'difficulty': question.difficulty
            }
        )
        
        # Create feedback
        feedback = Feedback(
            question_id=question.id,
            evaluation=evaluation['evaluation'],
            score=evaluation['score'],
            correct_answer=question.answer if evaluation['score'] < 100 else None,
            explanation=evaluation.get('explanation'),
            hints=evaluation.get('hints'),
            strengths=evaluation.get('strengths', []),
            weaknesses=evaluation.get('weaknesses', []),
            suggested_review=evaluation.get('suggested_review'),
            resources=evaluation.get('resources', [])
        )
        
        # Add emotional feedback if enabled
        if self.config.enable_emotion_tracking and answer.emotional_state:
            feedback.emotional_feedback = self._generate_emotional_feedback(
                answer.emotional_state,
                evaluation['score']
            )
        
        return feedback
    
    def _generate_emotional_feedback(
        self,
        emotional_state: Dict[str, Any],
        score: float
    ) -> str:
        """Generate feedback based on emotional state."""
        primary = emotional_state.get('primary_emotion', 'neutral')
        intensity = emotional_state.get('intensity', 0.5)
        
        if score >= 80:
            if primary in ['confident', 'happy']:
                return "Excellent! Your confidence is well-placed."
            elif primary in ['anxious', 'stressed']:
                return "Great job despite feeling anxious! You're doing better than you think."
            else:
                return "Excellent work! Keep up this momentum."
        elif score >= 60:
            if primary == 'confident':
                return "Good effort! You're on the right track."
            elif primary == 'frustrated':
                return "Don't let frustration get to you. You're making progress."
            else:
                return "Good attempt. Let's build on this."
        else:
            if primary == 'frustrated':
                return "This topic is challenging. Let's break it down together."
            elif primary == 'anxious':
                return "Take a deep breath. We'll work through this step by step."
            else:
                return "This is a tough one. Let's review the concepts."
    
    async def _get_next_question(
        self,
        last_feedback: Optional[Feedback] = None
    ) -> Optional[Question]:
        """
        Get the next question from queue or generate new one.
        
        Args:
            last_feedback: Feedback from last question
            
        Returns:
            Next question or None if session should end
        """
        # Check if session should end
        if self._should_end_session():
            return None
        
        # Try to get from queue first
        try:
            if not self.question_queue.empty():
                question = await asyncio.wait_for(
                    self.question_queue.get(),
                    timeout=1.0
                )
                self.asked_question_ids.add(question.id)
                return question
        except asyncio.TimeoutError:
            pass
        
        # Generate new question
        context = {
            'session_id': self.session_id,
            'topic': self.topic,
            'subtopics': self.subtopics,
            'history': self.question_history[-5:] if self.question_history else [],
            'metrics': self.metrics.to_dict(),
            'last_feedback': last_feedback.to_dict() if last_feedback else None
        }
        
        question = await self.questioner.generate_question(
            topic=self.topic,
            difficulty=self._get_current_difficulty(),
            context=context,
            exclude_ids=list(self.asked_question_ids)[-50:]  # Exclude recent questions
        )
        
        if question:
            self.asked_question_ids.add(question.id)
        
        return question
    
    async def _preload_questions(self):
        """Background task to preload questions."""
        try:
            while not self._should_end_session():
                # Generate and queue questions
                question = await self.questioner.generate_question(
                    topic=self.topic,
                    difficulty=self._get_current_difficulty(),
                    context={'preloading': True}
                )
                
                if question:
                    try:
                        # Don't block if queue is full
                        await asyncio.wait_for(
                            self.question_queue.put(question),
                            timeout=0.5
                        )
                    except asyncio.TimeoutError:
                        # Queue full, wait a bit
                        await asyncio.sleep(1)
                
                await asyncio.sleep(0.5)  # Prevent overwhelming
                
        except asyncio.CancelledError:
            logger.debug(f"Preload task cancelled for session {self.session_id}")
        except Exception as e:
            logger.error(f"Error in preload task: {e}")
    
    def _should_end_session(self) -> bool:
        """Check if session should end based on config."""
        # Check by question count
        if self.config.total_questions:
            if len(self.question_history) >= self.config.total_questions:
                return True
        
        # Check by time
        if self.config.duration_minutes and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds() / 60
            elapsed -= self.total_paused_seconds / 60
            if elapsed >= self.config.duration_minutes:
                return True
        
        return False
    
    def _get_current_difficulty(self) -> QuestionDifficulty:
        """Get current difficulty based on performance."""
        if not self.config.adaptive_difficulty:
            return self.config.initial_difficulty
        
        if len(self.question_history) < 3:
            return self.config.initial_difficulty
        
        # Calculate recent performance
        recent = self.question_history[-3:]
        avg_score = np.mean([r.score for r in recent])
        
        current = self.config.initial_difficulty
        
        # Adjust difficulty based on performance
        if avg_score >= 80:
            # Move up one level
            levels = list(QuestionDifficulty)
            try:
                idx = levels.index(current)
                if idx < len(levels) - 1:
                    return levels[idx + 1]
            except ValueError:
                pass
        elif avg_score <= 40:
            # Move down one level
            levels = list(QuestionDifficulty)
            try:
                idx = levels.index(current)
                if idx > 0:
                    return levels[idx - 1]
            except ValueError:
                pass
        
        return current
    
    def get_progress(self) -> float:
        """Get session progress percentage."""
        if self.config.total_questions:
            return (len(self.question_history) / self.config.total_questions) * 100
        elif self.config.duration_minutes and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds() / 60
            elapsed -= self.total_paused_seconds / 60
            return (elapsed / self.config.duration_minutes) * 100
        else:
            # Practice mode - use performance as progress
            return self.metrics.get_average_score()
    
    def get_time_remaining(self) -> Optional[int]:
        """Get time remaining in seconds."""
        if not self.config.duration_minutes or not self.start_time:
            return None
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        elapsed -= self.total_paused_seconds
        
        total_seconds = self.config.duration_minutes * 60
        remaining = total_seconds - elapsed
        
        return max(0, int(remaining))
    
    def get_questions_remaining(self) -> Optional[int]:
        """Get number of questions remaining."""
        if not self.config.total_questions:
            return None
        
        return max(0, self.config.total_questions - len(self.question_history))
    
    async def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary."""
        passed = self.metrics.get_average_score() >= self.config.passing_score
        
        summary = {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'topic': self.topic,
            'subtopics': self.subtopics,
            'mode': self.config.mode.value,
            'state': self.state.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time else None
            ),
            'paused_seconds': self.total_paused_seconds,
            'metrics': self.metrics.to_dict(),
            'passed': passed,
            'passing_score': self.config.passing_score,
            'config': {
                'mode': self.config.mode.value,
                'duration_minutes': self.config.duration_minutes,
                'total_questions': self.config.total_questions,
                'passing_score': self.config.passing_score,
                'allow_skip': self.config.allow_skip,
                'max_skips': self.config.max_skips
            },
            'weak_topics': self.metrics.get_weak_topics(),
            'recommendations': await self._generate_recommendations()
        }
        
        return summary
    
    async def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate study recommendations based on session performance."""
        recommendations = []
        
        # Get weak topics
        weak_topics = self.metrics.get_weak_topics(threshold=70)
        
        for topic, score in weak_topics[:3]:
            recommendations.append({
                'type': 'review_topic',
                'topic': topic,
                'reason': f'Performance: {score:.1f}%',
                'priority': 'high' if score < 50 else 'medium'
            })
        
        # Suggest difficulty adjustment
        if self.config.adaptive_difficulty:
            avg_score = self.metrics.get_average_score()
            if avg_score > 85:
                recommendations.append({
                    'type': 'increase_difficulty',
                    'reason': 'Consistently high performance',
                    'priority': 'low'
                })
            elif avg_score < 50:
                recommendations.append({
                    'type': 'decrease_difficulty',
                    'reason': 'Struggling with current level',
                    'priority': 'high'
                })
        
        # Emotional recommendations
        if self.metrics.emotional_states:
            # Check for stress patterns
            stress_count = sum(
                1 for s in self.metrics.emotional_states
                if s['state'].get('primary_emotion') in ['stressed', 'anxious', 'frustrated']
            )
            
            if stress_count > len(self.metrics.emotional_states) * 0.3:
                recommendations.append({
                    'type': 'take_break',
                    'reason': 'High stress levels detected',
                    'priority': 'medium'
                })
        
        return recommendations
    
    def update_emotional_state(self, emotional_state: Dict[str, Any]):
        """Update current emotional state."""
        if self.config.enable_emotion_tracking:
            self.metrics.record_emotional_state(emotional_state)
    
    async def cleanup(self):
        """Clean up session resources."""
        if self._preload_task and not self._preload_task.done():
            self._preload_task.cancel()
            try:
                await self._preload_task
            except asyncio.CancelledError:
                pass
        
        # Clear queue
        while not self.question_queue.empty():
            try:
                self.question_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        logger.info(f"Cleaned up session {self.session_id}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()