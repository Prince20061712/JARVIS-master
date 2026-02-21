import json
import datetime
import os
import math
import random
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict, deque
from enum import Enum
import numpy as np
from statistics import mean, median, stdev
import warnings
warnings.filterwarnings('ignore')

class StudyMode(Enum):
    FOCUS = "focus"
    REVIEW = "review"
    QUIZ = "quiz"
    PRACTICE = "practice"
    LEARNING = "learning"

class DifficultyLevel(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MASTER = "master"

class CardStatus(Enum):
    NEW = "new"
    LEARNING = "learning"
    REVIEW = "review"
    MASTERED = "mastered"
    SUSPENDED = "suspended"

@dataclass
class Flashcard:
    id: str
    subject: str
    front: str
    back: str
    tags: List[str]
    created_date: str
    last_reviewed: Optional[str]
    next_review: str
    review_count: int
    ease_factor: float
    interval_days: int
    status: CardStatus
    confidence_history: List[int]
    metadata: Dict[str, Any]
    
    @property
    def difficulty_score(self) -> float:
        """Calculate difficulty score based on review history"""
        if not self.confidence_history:
            return 2.5  # Default medium difficulty
        
        avg_confidence = mean(self.confidence_history[-5:]) if len(self.confidence_history) >= 5 else mean(self.confidence_history)
        return max(1.0, min(5.0, 6 - avg_confidence))  # Invert confidence to difficulty

@dataclass
class StudySession:
    id: str
    subject: str
    mode: StudyMode
    start_time: str
    end_time: Optional[str]
    duration_minutes: int
    cards_studied: int
    correct_count: int
    notes: List[str]
    metrics: Dict[str, Any]
    interruptions: int
    focus_score: float

@dataclass
class StudyGoal:
    id: str
    subject: str
    description: str
    target_hours: float
    current_hours: float
    deadline: Optional[str]
    priority: int  # 1-5
    status: str  # active, completed, failed, paused
    subgoals: List[str]
    progress_history: List[Dict[str, Any]]

class AdvancedStudyManager:
    def __init__(self, data_dir="study_data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Data files
        self.cards_file = os.path.join(data_dir, "flashcards.jsonl")
        self.sessions_file = os.path.join(data_dir, "sessions.jsonl")
        self.goals_file = os.path.join(data_dir, "goals.json")
        self.analytics_file = os.path.join(data_dir, "analytics.json")
        
        # Initialize data structures
        self.flashcards: Dict[str, Flashcard] = {}
        self.study_sessions: List[StudySession] = []
        self.study_goals: Dict[str, StudyGoal] = {}
        self.current_session: Optional[StudySession] = None
        
        # Learning parameters (SM-2 spaced repetition algorithm)
        self.learning_steps = [1, 10]  # minutes until next review
        self.review_intervals = [1, 3, 7, 16, 35]  # days for reviews
        self.max_interval = 365  # Maximum days between reviews
        self.min_ease_factor = 1.3
        self.max_ease_factor = 5.0
        
        # Session tracking
        self.session_cards = deque()
        self.session_start_time = None
        self.session_metrics = defaultdict(list)
        
        # Statistics
        self.analytics = self._load_analytics()
        
        # Load existing data
        self._load_data()
        
    def _load_data(self):
        """Load all study data"""
        # Load flashcards
        if os.path.exists(self.cards_file):
            with open(self.cards_file, 'r') as f:
                for line in f:
                    data = json.loads(line.strip())
                    card = Flashcard(**data)
                    self.flashcards[card.id] = card
        
        # Load study sessions
        if os.path.exists(self.sessions_file):
            with open(self.sessions_file, 'r') as f:
                for line in f:
                    data = json.loads(line.strip())
                    session = StudySession(**data)
                    self.study_sessions.append(session)
        
        # Load study goals
        if os.path.exists(self.goals_file):
            with open(self.goals_file, 'r') as f:
                goals_data = json.load(f)
                for goal_id, goal_data in goals_data.items():
                    goal = StudyGoal(**goal_data)
                    self.study_goals[goal.id] = goal
    
    def _save_flashcards(self):
        """Save flashcards to JSONL file"""
        with open(self.cards_file, 'w') as f:
            for card in self.flashcards.values():
                json_line = json.dumps({
                    "id": card.id,
                    "subject": card.subject,
                    "front": card.front,
                    "back": card.back,
                    "tags": card.tags,
                    "created_date": card.created_date,
                    "last_reviewed": card.last_reviewed,
                    "next_review": card.next_review,
                    "review_count": card.review_count,
                    "ease_factor": card.ease_factor,
                    "interval_days": card.interval_days,
                    "status": card.status.value,
                    "confidence_history": card.confidence_history,
                    "metadata": card.metadata
                })
                f.write(json_line + '\n')
    
    def _save_sessions(self):
        """Save study sessions to JSONL file"""
        with open(self.sessions_file, 'w') as f:
            for session in self.study_sessions:
                json_line = json.dumps({
                    "id": session.id,
                    "subject": session.subject,
                    "mode": session.mode.value,
                    "start_time": session.start_time,
                    "end_time": session.end_time,
                    "duration_minutes": session.duration_minutes,
                    "cards_studied": session.cards_studied,
                    "correct_count": session.correct_count,
                    "notes": session.notes,
                    "metrics": session.metrics,
                    "interruptions": session.interruptions,
                    "focus_score": session.focus_score
                })
                f.write(json_line + '\n')
    
    def _save_goals(self):
        """Save study goals to JSON file"""
        goals_data = {
            goal_id: {
                "id": goal.id,
                "subject": goal.subject,
                "description": goal.description,
                "target_hours": goal.target_hours,
                "current_hours": goal.current_hours,
                "deadline": goal.deadline,
                "priority": goal.priority,
                "status": goal.status,
                "subgoals": goal.subgoals,
                "progress_history": goal.progress_history
            }
            for goal_id, goal in self.study_goals.items()
        }
        with open(self.goals_file, 'w') as f:
            json.dump(goals_data, f, indent=2)
    
    def _load_analytics(self) -> Dict[str, Any]:
        """Load analytics data"""
        if os.path.exists(self.analytics_file):
            try:
                with open(self.analytics_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "total_study_minutes": 0,
            "total_cards_created": 0,
            "total_reviews": 0,
            "average_accuracy": 0.0,
            "streak_days": 0,
            "last_study_date": None,
            "subject_stats": defaultdict(lambda: {
                "study_minutes": 0,
                "cards_created": 0,
                "reviews": 0,
                "average_accuracy": 0.0
            }),
            "daily_progress": defaultdict(int),
            "weekly_progress": defaultdict(int),
            "monthly_progress": defaultdict(int)
        }
    
    def _save_analytics(self):
        """Save analytics data"""
        # Convert defaultdict to regular dict for JSON serialization
        analytics_copy = self.analytics.copy()
        analytics_copy["subject_stats"] = dict(analytics_copy["subject_stats"])
        analytics_copy["daily_progress"] = dict(analytics_copy["daily_progress"])
        analytics_copy["weekly_progress"] = dict(analytics_copy["weekly_progress"])
        analytics_copy["monthly_progress"] = dict(analytics_copy["monthly_progress"])
        
        with open(self.analytics_file, 'w') as f:
            json.dump(analytics_copy, f, indent=2)
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        return hashlib.md5(str(datetime.datetime.now().timestamp()).encode()).hexdigest()[:12]
    
    def create_flashcard(self, subject: str, front: str, back: str, 
                        tags: List[str] = None, metadata: Dict[str, Any] = None) -> Flashcard:
        """Create a new flashcard with spaced repetition scheduling"""
        card_id = self._generate_id()
        now = datetime.datetime.now().isoformat()
        
        # Calculate initial next review (tomorrow for new cards)
        next_review_date = datetime.datetime.now() + datetime.timedelta(days=1)
        
        card = Flashcard(
            id=card_id,
            subject=subject,
            front=front,
            back=back,
            tags=tags or [],
            created_date=now,
            last_reviewed=None,
            next_review=next_review_date.isoformat(),
            review_count=0,
            ease_factor=2.5,  # Default ease factor
            interval_days=0,
            status=CardStatus.NEW,
            confidence_history=[],
            metadata=metadata or {}
        )
        
        self.flashcards[card_id] = card
        
        # Update analytics
        self.analytics["total_cards_created"] += 1
        self.analytics["subject_stats"][subject]["cards_created"] += 1
        
        self._save_flashcards()
        self._save_analytics()
        
        return card
    
    def update_card_review(self, card_id: str, confidence: int, 
                          response_time_seconds: Optional[float] = None):
        """
        Update card after review using SM-2 spaced repetition algorithm
        
        confidence: 0-5 where:
            0: Complete blackout
            1: Incorrect response
            2: Incorrect response after hesitation
            3: Correct response with difficulty
            4: Correct response after hesitation
            5: Perfect response
        """
        if card_id not in self.flashcards:
            raise ValueError(f"Card {card_id} not found")
        
        card = self.flashcards[card_id]
        now = datetime.datetime.now()
        
        # Update review history
        card.review_count += 1
        card.last_reviewed = now.isoformat()
        card.confidence_history.append(confidence)
        
        # Limit confidence history
        if len(card.confidence_history) > 50:
            card.confidence_history = card.confidence_history[-50:]
        
        # SM-2 Algorithm
        if card.status == CardStatus.NEW or card.status == CardStatus.LEARNING:
            if confidence >= 3:  # Good response
                if card.interval_days == 0:
                    card.interval_days = 1
                else:
                    card.interval_days = math.ceil(card.interval_days * card.ease_factor)
                
                if card.interval_days >= 7:
                    card.status = CardStatus.REVIEW
                else:
                    card.status = CardStatus.LEARNING
            else:
                # Reset learning
                card.interval_days = 0
                card.status = CardStatus.LEARNING
            
        else:  # REVIEW or MASTERED cards
            if confidence >= 3:  # Good response
                card.interval_days = math.ceil(card.interval_days * card.ease_factor)
                
                # Update ease factor (modify based on response quality)
                if confidence == 5:
                    card.ease_factor = min(self.max_ease_factor, card.ease_factor + 0.1)
                elif confidence == 4:
                    card.ease_factor = max(self.min_ease_factor, card.ease_factor - 0.05)
                elif confidence == 3:
                    card.ease_factor = max(self.min_ease_factor, card.ease_factor - 0.15)
                elif confidence <= 2:
                    card.ease_factor = max(self.min_ease_factor, card.ease_factor - 0.2)
                
                # Cap interval
                card.interval_days = min(self.max_interval, card.interval_days)
                
                if card.interval_days >= 30:
                    card.status = CardStatus.MASTERED
                else:
                    card.status = CardStatus.REVIEW
                    
            else:  # Bad response
                card.interval_days = 1
                card.ease_factor = max(self.min_ease_factor, card.ease_factor - 0.2)
                card.status = CardStatus.LEARNING
        
        # Calculate next review date
        next_review = now + datetime.timedelta(days=card.interval_days)
        card.next_review = next_review.isoformat()
        
        # Update metadata
        if response_time_seconds:
            if "response_times" not in card.metadata:
                card.metadata["response_times"] = []
            card.metadata["response_times"].append(response_time_seconds)
        
        self._save_flashcards()
        
        return card
    
    def get_due_cards(self, subject: Optional[str] = None, 
                     limit: Optional[int] = None) -> List[Flashcard]:
        """Get cards that are due for review"""
        now = datetime.datetime.now()
        due_cards = []
        
        for card in self.flashcards.values():
            if card.status == CardStatus.SUSPENDED:
                continue
            
            if subject and card.subject != subject:
                continue
            
            next_review = datetime.datetime.fromisoformat(card.next_review)
            if next_review <= now:
                due_cards.append(card)
        
        # Sort by priority (cards that are overdue more get higher priority)
        due_cards.sort(key=lambda c: (
            datetime.datetime.fromisoformat(c.next_review),
            -c.ease_factor,  # Lower ease factor = harder cards first
            c.review_count   # Fewer reviews = newer cards first
        ))
        
        if limit:
            due_cards = due_cards[:limit]
        
        return due_cards
    
    def start_study_session(self, subject: str, mode: StudyMode = StudyMode.REVIEW,
                          goal_cards: int = 20, focus_duration: int = 25) -> StudySession:
        """Start a new study session with focus timer"""
        session_id = self._generate_id()
        now = datetime.datetime.now()
        
        # Get due cards for the session
        due_cards = self.get_due_cards(subject, limit=goal_cards)
        
        # Create session
        session = StudySession(
            id=session_id,
            subject=subject,
            mode=mode,
            start_time=now.isoformat(),
            end_time=None,
            duration_minutes=0,
            cards_studied=0,
            correct_count=0,
            notes=[],
            metrics={
                "goal_cards": goal_cards,
                "focus_duration": focus_duration,
                "initial_due_cards": len(due_cards)
            },
            interruptions=0,
            focus_score=0.0
        )
        
        self.current_session = session
        self.session_start_time = now
        self.session_cards = deque(due_cards)
        self.session_metrics = defaultdict(list)
        
        return session
    
    def process_card_review(self, card_id: str, confidence: int, 
                          response_time_seconds: float = None) -> Dict[str, Any]:
        """Process a card review during a study session"""
        if not self.current_session:
            raise ValueError("No active study session")
        
        # Update card
        card = self.update_card_review(card_id, confidence, response_time_seconds)
        
        # Update session metrics
        self.current_session.cards_studied += 1
        if confidence >= 3:  # Consider correct if confidence >= 3
            self.current_session.correct_count += 1
        
        # Store metrics
        self.session_metrics["confidences"].append(confidence)
        if response_time_seconds:
            self.session_metrics["response_times"].append(response_time_seconds)
        
        # Remove from session cards
        for i, session_card in enumerate(self.session_cards):
            if session_card.id == card_id:
                del self.session_cards[i]
                break
        
        return {
            "card": card,
            "session_progress": {
                "cards_studied": self.current_session.cards_studied,
                "correct_count": self.current_session.correct_count,
                "remaining_cards": len(self.session_cards)
            }
        }
    
    def end_study_session(self, notes: List[str] = None) -> StudySession:
        """End the current study session and save results"""
        if not self.current_session:
            raise ValueError("No active study session")
        
        end_time = datetime.datetime.now()
        start_time = datetime.datetime.fromisoformat(self.current_session.start_time)
        duration_minutes = (end_time - start_time).seconds // 60
        
        # Update session
        self.current_session.end_time = end_time.isoformat()
        self.current_session.duration_minutes = duration_minutes
        self.current_session.notes = notes or []
        
        # Calculate focus score
        total_cards = self.current_session.cards_studied
        if total_cards > 0:
            accuracy = self.current_session.correct_count / total_cards
            avg_response_time = mean(self.session_metrics.get("response_times", [30]))
            
            # Focus score formula (adjust weights as needed)
            time_efficiency = min(1.0, 30 / avg_response_time) if avg_response_time > 0 else 0.5
            self.current_session.focus_score = (accuracy * 0.6 + time_efficiency * 0.4) * 100
        
        # Add to sessions list
        self.study_sessions.append(self.current_session)
        
        # Update analytics
        self._update_analytics(self.current_session)
        
        # Save data
        self._save_sessions()
        self._save_analytics()
        
        session_summary = self.current_session
        self.current_session = None
        self.session_cards.clear()
        self.session_metrics.clear()
        
        return session_summary
    
    def _update_analytics(self, session: StudySession):
        """Update analytics with session data"""
        # Update total study time
        self.analytics["total_study_minutes"] += session.duration_minutes
        
        # Update subject stats
        subject_stats = self.analytics["subject_stats"][session.subject]
        subject_stats["study_minutes"] += session.duration_minutes
        subject_stats["reviews"] += session.cards_studied
        
        # Calculate accuracy
        if session.cards_studied > 0:
            accuracy = session.correct_count / session.cards_studied
            # Update average accuracy (weighted)
            current_avg = subject_stats["average_accuracy"]
            total_reviews = subject_stats["reviews"]
            subject_stats["average_accuracy"] = (
                (current_avg * (total_reviews - session.cards_studied) + 
                 accuracy * session.cards_studied) / total_reviews
                if total_reviews > 0 else accuracy
            )
        
        # Update streak
        today = datetime.date.today().isoformat()
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        
        if self.analytics["last_study_date"] == yesterday:
            self.analytics["streak_days"] += 1
        elif self.analytics["last_study_date"] != today:
            # Only increment if first study session today
            self.analytics["streak_days"] += 1
        
        self.analytics["last_study_date"] = today
        
        # Update progress tracking
        date_key = today
        week_key = f"{datetime.date.today().isocalendar()[0]}-{datetime.date.today().isocalendar()[1]}"
        month_key = f"{datetime.date.today().year}-{datetime.date.today().month:02d}"
        
        self.analytics["daily_progress"][date_key] += session.duration_minutes
        self.analytics["weekly_progress"][week_key] += session.duration_minutes
        self.analytics["monthly_progress"][month_key] += session.duration_minutes
    
    def create_study_goal(self, subject: str, description: str, 
                         target_hours: float, deadline: Optional[str] = None,
                         priority: int = 3) -> StudyGoal:
        """Create a new study goal"""
        goal_id = self._generate_id()
        
        goal = StudyGoal(
            id=goal_id,
            subject=subject,
            description=description,
            target_hours=target_hours,
            current_hours=0.0,
            deadline=deadline,
            priority=priority,
            status="active",
            subgoals=[],
            progress_history=[]
        )
        
        self.study_goals[goal_id] = goal
        self._save_goals()
        
        return goal
    
    def update_goal_progress(self, goal_id: str, minutes_studied: float):
        """Update progress for a study goal"""
        if goal_id not in self.study_goals:
            raise ValueError(f"Goal {goal_id} not found")
        
        goal = self.study_goals[goal_id]
        goal.current_hours += minutes_studied / 60
        
        # Add progress history entry
        progress_entry = {
            "date": datetime.datetime.now().isoformat(),
            "minutes_studied": minutes_studied,
            "total_hours": goal.current_hours,
            "completion_percentage": min(100.0, (goal.current_hours / goal.target_hours) * 100)
        }
        goal.progress_history.append(progress_entry)
        
        # Check if goal is completed
        if goal.current_hours >= goal.target_hours:
            goal.status = "completed"
        
        self._save_goals()
        
        return goal
    
    def get_study_analytics(self, time_period: str = "all") -> Dict[str, Any]:
        """Get comprehensive study analytics"""
        now = datetime.datetime.now()
        
        # Filter sessions based on time period
        if time_period == "day":
            cutoff = now - datetime.timedelta(days=1)
            sessions = [s for s in self.study_sessions 
                       if datetime.datetime.fromisoformat(s.start_time) >= cutoff]
        elif time_period == "week":
            cutoff = now - datetime.timedelta(weeks=1)
            sessions = [s for s in self.study_sessions 
                       if datetime.datetime.fromisoformat(s.start_time) >= cutoff]
        elif time_period == "month":
            cutoff = now - datetime.timedelta(days=30)
            sessions = [s for s in self.study_sessions 
                       if datetime.datetime.fromisoformat(s.start_time) >= cutoff]
        else:
            sessions = self.study_sessions
        
        # Calculate statistics
        total_minutes = sum(s.duration_minutes for s in sessions)
        total_cards = sum(s.cards_studied for s in sessions)
        total_correct = sum(s.correct_count for s in sessions)
        
        avg_accuracy = total_correct / total_cards if total_cards > 0 else 0
        avg_session_length = mean([s.duration_minutes for s in sessions]) if sessions else 0
        avg_focus_score = mean([s.focus_score for s in sessions]) if sessions else 0
        
        # Subject distribution
        subject_distribution = defaultdict(int)
        for session in sessions:
            subject_distribution[session.subject] += session.duration_minutes
        
        # Time of day analysis
        time_of_day_distribution = defaultdict(int)
        for session in sessions:
            hour = datetime.datetime.fromisoformat(session.start_time).hour
            if 5 <= hour < 12:
                time_of_day_distribution["morning"] += session.duration_minutes
            elif 12 <= hour < 17:
                time_of_day_distribution["afternoon"] += session.duration_minutes
            elif 17 <= hour < 22:
                time_of_day_distribution["evening"] += session.duration_minutes
            else:
                time_of_day_distribution["night"] += session.duration_minutes
        
        # Difficulty progression
        difficulty_progression = []
        if sessions:
            # Sort sessions by date
            sorted_sessions = sorted(sessions, 
                                   key=lambda s: datetime.datetime.fromisoformat(s.start_time))
            
            # Take samples at regular intervals
            step = max(1, len(sorted_sessions) // 10)
            for i in range(0, len(sorted_sessions), step):
                session = sorted_sessions[i]
                difficulty_progression.append({
                    "date": session.start_time,
                    "accuracy": session.correct_count / session.cards_studied if session.cards_studied > 0 else 0,
                    "focus_score": session.focus_score,
                    "cards_per_minute": session.cards_studied / max(1, session.duration_minutes)
                })
        
        return {
            "time_period": time_period,
            "total_minutes": total_minutes,
            "total_sessions": len(sessions),
            "total_cards_studied": total_cards,
            "average_accuracy": round(avg_accuracy * 100, 2),
            "average_session_length": round(avg_session_length, 2),
            "average_focus_score": round(avg_focus_score, 2),
            "subject_distribution": dict(sorted(
                subject_distribution.items(), 
                key=lambda x: x[1], 
                reverse=True
            )),
            "time_of_day_distribution": dict(time_of_day_distribution),
            "difficulty_progression": difficulty_progression,
            "streak_days": self.analytics["streak_days"],
            "active_goals": len([g for g in self.study_goals.values() if g.status == "active"]),
            "card_status_distribution": self._get_card_status_distribution()
        }
    
    def _get_card_status_distribution(self) -> Dict[str, int]:
        """Get distribution of card statuses"""
        distribution = defaultdict(int)
        for card in self.flashcards.values():
            distribution[card.status.value] += 1
        return dict(distribution)
    
    def generate_study_plan(self, available_minutes: int = 60) -> Dict[str, Any]:
        """Generate personalized study plan based on analytics"""
        due_cards_by_subject = defaultdict(list)
        
        # Get due cards grouped by subject
        for card in self.get_due_cards():
            due_cards_by_subject[card.subject].append(card)
        
        # Calculate priority for each subject
        subject_priority = {}
        for subject, cards in due_cards_by_subject.items():
            # Priority based on:
            # 1. Number of due cards
            # 2. Average difficulty
            # 3. Time since last study
            subject_stats = self.analytics["subject_stats"][subject]
            avg_difficulty = mean([c.difficulty_score for c in cards]) if cards else 2.5
            
            priority_score = (
                len(cards) * 0.4 +  # Number of due cards (40%)
                avg_difficulty * 0.3 +  # Difficulty (30%)
                (100 - min(100, subject_stats["average_accuracy"])) * 0.3  # Weakness (30%)
            )
            
            subject_priority[subject] = priority_score
        
        # Sort subjects by priority
        prioritized_subjects = sorted(subject_priority.items(), key=lambda x: x[1], reverse=True)
        
        # Allocate time based on priority
        study_plan = []
        remaining_minutes = available_minutes
        
        for subject, priority in prioritized_subjects:
            if remaining_minutes <= 0:
                break
            
            # Allocate time proportional to priority
            subject_time = min(remaining_minutes, 
                             int(available_minutes * (priority / sum(subject_priority.values()))))
            
            cards_to_review = min(len(due_cards_by_subject[subject]), 
                                max(5, subject_time // 2))  # Approx 2 minutes per card
            
            study_plan.append({
                "subject": subject,
                "allocated_minutes": subject_time,
                "cards_to_review": cards_to_review,
                "priority_score": round(priority, 2),
                "cards": due_cards_by_subject[subject][:cards_to_review]
            })
            
            remaining_minutes -= subject_time
        
        return {
            "total_available_minutes": available_minutes,
            "subjects_covered": len(study_plan),
            "total_cards_to_review": sum(item["cards_to_review"] for item in study_plan),
            "study_plan": study_plan,
            "estimated_completion_time": available_minutes - remaining_minutes
        }
    
    def export_data(self, format: str = "json") -> Dict[str, Any]:
        """Export study data for backup or analysis"""
        return {
            "metadata": {
                "export_date": datetime.datetime.now().isoformat(),
                "total_flashcards": len(self.flashcards),
                "total_sessions": len(self.study_sessions),
                "total_goals": len(self.study_goals)
            },
            "analytics_summary": self.get_study_analytics("all"),
            "recent_sessions": [
                {
                    "subject": s.subject,
                    "date": s.start_time,
                    "duration": s.duration_minutes,
                    "cards_studied": s.cards_studied,
                    "accuracy": s.correct_count / max(1, s.cards_studied)
                }
                for s in self.study_sessions[-10:]
            ],
            "active_goals": [
                {
                    "subject": g.subject,
                    "description": g.description,
                    "progress": f"{g.current_hours:.1f}/{g.target_hours:.1f} hours",
                    "completion_percentage": min(100, (g.current_hours / g.target_hours) * 100)
                }
                for g in self.study_goals.values()
                if g.status == "active"
            ],
            "card_statistics": self._get_card_status_distribution()
        }
    
    def get_daily_reminder(self) -> str:
        """Generate daily study reminder"""
        due_cards = self.get_due_cards()
        today = datetime.date.today()
        
        if not due_cards:
            return f"Great work! You're all caught up on reviews for today. Consider adding new cards or exploring new topics."
        
        # Group by subject
        due_by_subject = defaultdict(list)
        for card in due_cards:
            due_by_subject[card.subject].append(card)
        
        # Create reminder message
        message_parts = [f"You have {len(due_cards)} cards due for review today:"]
        
        for subject, cards in due_by_subject.items():
            # Calculate average difficulty
            avg_difficulty = mean([c.difficulty_score for c in cards])
            difficulty_text = "easy" if avg_difficulty < 2 else "moderate" if avg_difficulty < 3.5 else "challenging"
            
            message_parts.append(f"  • {subject}: {len(cards)} cards ({difficulty_text})")
        
        # Add streak motivation
        if self.analytics["streak_days"] >= 3:
            message_parts.append(f"\nYou're on a {self.analytics['streak_days']}-day streak! Keep it up!")
        
        # Estimated study time
        estimated_minutes = len(due_cards) * 2  # Approx 2 minutes per card
        message_parts.append(f"\nEstimated study time: {estimated_minutes} minutes")
        
        return "\n".join(message_parts)


# Example usage
if __name__ == "__main__":
    print("📚 Testing Advanced Study Manager...")
    print("=" * 60)
    
    # Initialize study manager
    study_manager = AdvancedStudyManager()
    
    # Create some flashcards
    print("\n📝 Creating flashcards...")
    subjects = ["Python", "Machine Learning", "Mathematics", "History"]
    
    for subject in subjects:
        for i in range(3):
            card = study_manager.create_flashcard(
                subject=subject,
                front=f"What is the key concept {i+1} in {subject}?",
                back=f"This is the explanation for concept {i+1} in {subject}.",
                tags=[f"concept{i+1}", subject.lower().replace(" ", "_")]
            )
            print(f"  Created card: {card.front[:40]}...")
    
    # Start a study session
    print("\n🎯 Starting study session...")
    session = study_manager.start_study_session(
        subject="Python",
        mode=StudyMode.REVIEW,
        goal_cards=5,
        focus_duration=25
    )
    print(f"  Session started: {session.subject} - Goal: {session.metrics['goal_cards']} cards")
    
    # Simulate reviewing some cards
    print("\n🔄 Simulating card reviews...")
    due_cards = study_manager.get_due_cards("Python", limit=5)
    
    for i, card in enumerate(due_cards[:3], 1):
        # Simulate random confidence (3-5 for successful reviews)
        confidence = random.choice([4, 5])
        result = study_manager.process_card_review(card.id, confidence, response_time_seconds=15)
        print(f"  Reviewed card {i}: Confidence {confidence}, Response time: 15s")
    
    # End session
    print("\n⏹️ Ending study session...")
    ended_session = study_manager.end_study_session(
        notes=["Good focus today", "Need to review OOP concepts more"]
    )
    print(f"  Session ended: {ended_session.duration_minutes} minutes, "
          f"{ended_session.cards_studied} cards studied, "
          f"Accuracy: {ended_session.correct_count/ended_session.cards_studied*100:.1f}%")
    
    # Create study goal
    print("\n🎯 Creating study goal...")
    goal = study_manager.create_study_goal(
        subject="Python",
        description="Master Python OOP concepts",
        target_hours=10,
        deadline=(datetime.datetime.now() + datetime.timedelta(days=30)).isoformat(),
        priority=4
    )
    print(f"  Goal created: {goal.description} - Target: {goal.target_hours} hours")
    
    # Update goal progress
    study_manager.update_goal_progress(goal.id, ended_session.duration_minutes)
    print(f"  Goal progress: {goal.current_hours:.1f}/{goal.target_hours:.1f} hours")
    
    # Get analytics
    print("\n📊 Getting analytics...")
    analytics = study_manager.get_study_analytics("all")
    print(f"  Total study minutes: {analytics['total_minutes']}")
    print(f"  Average accuracy: {analytics['average_accuracy']}%")
    print(f"  Streak days: {analytics['streak_days']}")
    print(f"  Subject distribution: {list(analytics['subject_distribution'].keys())}")
    
    # Generate study plan
    print("\n📋 Generating study plan...")
    study_plan = study_manager.generate_study_plan(available_minutes=60)
    print(f"  Study plan for {study_plan['total_available_minutes']} minutes:")
    for item in study_plan["study_plan"]:
        print(f"    • {item['subject']}: {item['allocated_minutes']} min, {item['cards_to_review']} cards")
    
    # Daily reminder
    print("\n🔔 Daily reminder:")
    reminder = study_manager.get_daily_reminder()
    print(f"  {reminder}")
    
    print("\n✅ Advanced Study Manager test complete!")