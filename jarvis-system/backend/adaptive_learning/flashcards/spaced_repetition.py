"""
Spaced repetition module implementing the SuperMemo-2 (SM-2) algorithm
for optimal flashcard scheduling and review timing.
"""

import math
import json
import logging
import sqlite3
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field, asdict
from enum import IntEnum
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import threading
import pickle
import hashlib

import numpy as np
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReviewQuality(IntEnum):
    """Quality of response for SM-2 algorithm (0-5)."""
    COMPLETE_BLACKOUT = 0  # Complete blackout, wrong answer
    INCORRECT_BUT_FAMILIAR = 1  # Incorrect, but remembered upon seeing answer
    INCORRECT_EASY = 2  # Incorrect, but easy to remember
    CORRECT_DIFFICULT = 3  # Correct, but required significant effort
    CORRECT_HESITANT = 4  # Correct, with some hesitation
    CORRECT_PERFECT = 5  # Correct, perfect recall


@dataclass
class SM2Parameters:
    """Parameters for the SM-2 algorithm."""
    initial_ease_factor: float = 2.5
    minimum_ease_factor: float = 1.3
    easy_bonus: float = 1.5
    hard_penalty: float = 0.8
    again_interval: int = 1  # days
    hard_interval: int = 3  # days
    good_interval: int = 5  # days
    easy_interval: int = 7  # days
    max_interval: int = 36500  # ~100 years
    
    def validate(self):
        """Validate parameters."""
        if self.initial_ease_factor < self.minimum_ease_factor:
            raise ValueError("Initial ease factor cannot be less than minimum")
        if self.minimum_ease_factor < 1.0:
            raise ValueError("Minimum ease factor must be >= 1.0")
        if self.max_interval < 1:
            raise ValueError("Max interval must be at least 1")


@dataclass
class SchedulingInfo:
    """Information about card scheduling."""
    interval: int  # Days until next review
    ease_factor: float  # Current ease factor
    due_date: datetime  # When the card is due
    repetitions: int  # Number of times reviewed
    lapses: int  # Number of times forgotten
    last_review: Optional[datetime] = None
    
    def days_overdue(self, current_date: Optional[datetime] = None) -> int:
        """Calculate days overdue."""
        if current_date is None:
            current_date = datetime.now()
        
        if self.due_date < current_date:
            delta = current_date - self.due_date
            return delta.days
        return 0
    
    def is_due(self, current_date: Optional[datetime] = None) -> bool:
        """Check if card is due for review."""
        if current_date is None:
            current_date = datetime.now()
        return current_date >= self.due_date


class ReviewLog(BaseModel):
    """Log entry for a single review."""
    card_id: str
    user_id: str
    review_time: datetime = Field(default_factory=datetime.now)
    quality: ReviewQuality
    response_time: float  # seconds
    previous_interval: Optional[int] = None
    new_interval: Optional[int] = None
    ease_factor: Optional[float] = None
    repetitions: int = 0
    lapses: int = 0
    scheduled_days: Optional[int] = None
    deck_name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ReviewQuality: lambda v: v.value
        }
    
    def dict(self, *args, **kwargs):
        """Override dict to handle enum serialization."""
        d = super().dict(*args, **kwargs)
        d['quality'] = self.quality.value
        d['review_time'] = self.review_time.isoformat()
        return d


class CardProgress(BaseModel):
    """Progress tracking for a flashcard."""
    card_id: str
    user_id: str
    deck_name: Optional[str] = None
    
    # SM-2 state
    interval: int = 0  # Current interval in days
    ease_factor: float = 2.5  # Current ease factor
    repetitions: int = 0  # Number of successful reviews
    lapses: int = 0  # Number of times forgotten
    
    # Scheduling
    due_date: datetime = Field(default_factory=datetime.now)
    last_review: Optional[datetime] = None
    
    # Statistics
    total_reviews: int = 0
    average_response_time: float = 0.0
    review_history: List[ReviewLog] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def update_from_review(self, quality: ReviewQuality, response_time: float):
        """
        Update progress based on review quality.
        
        Args:
            quality: Quality of response (0-5)
            response_time: Time taken to respond in seconds
        """
        # Update statistics
        self.total_reviews += 1
        self.average_response_time = (
            (self.average_response_time * (self.total_reviews - 1) + response_time) /
            self.total_reviews
        )
        
        # Create review log
        log = ReviewLog(
            card_id=self.card_id,
            user_id=self.user_id,
            quality=quality,
            response_time=response_time,
            previous_interval=self.interval,
            repetitions=self.repetitions,
            lapses=self.lapses,
            scheduled_days=self.interval,
            deck_name=self.deck_name
        )
        
        self.review_history.append(log)
        self.last_review = log.review_time
        self.updated_at = datetime.now()
    
    def is_due(self, current_date: Optional[datetime] = None) -> bool:
        """Check if card is due for review."""
        if current_date is None:
            current_date = datetime.now()
        return current_date >= self.due_date
    
    def days_overdue(self, current_date: Optional[datetime] = None) -> int:
        """Calculate days overdue."""
        if current_date is None:
            current_date = datetime.now()
        
        if self.due_date < current_date:
            delta = current_date - self.due_date
            return delta.days
        return 0
    
    def get_review_stats(self) -> Dict[str, Any]:
        """Get review statistics."""
        if not self.review_history:
            return {
                'total_reviews': 0,
                'success_rate': 0,
                'average_quality': 0
            }
        
        qualities = [r.quality for r in self.review_history]
        success_rate = sum(1 for q in qualities if q >= 3) / len(qualities) * 100
        
        return {
            'total_reviews': self.total_reviews,
            'success_rate': success_rate,
            'average_quality': sum(qualities) / len(qualities),
            'average_response_time': self.average_response_time,
            'repetitions': self.repetitions,
            'lapses': self.lapses,
            'current_interval': self.interval,
            'current_ease': self.ease_factor,
            'days_overdue': self.days_overdue()
        }
    
    def get_learning_curve(self) -> List[Dict[str, Any]]:
        """Get learning curve data points."""
        curve = []
        for i, review in enumerate(self.review_history):
            curve.append({
                'review_number': i + 1,
                'quality': review.quality,
                'interval': review.new_interval or 0,
                'response_time': review.response_time,
                'date': review.review_time.isoformat()
            })
        return curve


class SpacedRepetition:
    """
    Implementation of SuperMemo-2 (SM-2) spaced repetition algorithm
    with enhancements for modern flashcard systems.
    """
    
    def __init__(
        self,
        db_path: Optional[Path] = None,
        params: Optional[SM2Parameters] = None
    ):
        """
        Initialize spaced repetition system.
        
        Args:
            db_path: Path to SQLite database for persistence
            params: SM-2 algorithm parameters
        """
        self.params = params or SM2Parameters()
        self.params.validate()
        
        # Database setup
        if db_path is None:
            db_path = Path.home() / '.jarvis' / 'spaced_repetition.db'
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self._progress_cache: Dict[str, CardProgress] = {}
        self._lock = threading.RLock()
        
        # Initialize database
        self._init_database()
        
        logger.info(f"SpacedRepetition initialized with db: {db_path}")
    
    def _init_database(self):
        """Initialize SQLite database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS card_progress (
                        card_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        deck_name TEXT,
                        interval INTEGER NOT NULL,
                        ease_factor REAL NOT NULL,
                        repetitions INTEGER NOT NULL,
                        lapses INTEGER NOT NULL,
                        due_date TIMESTAMP NOT NULL,
                        last_review TIMESTAMP,
                        total_reviews INTEGER NOT NULL,
                        average_response_time REAL NOT NULL,
                        data TEXT,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS review_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        card_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        review_time TIMESTAMP NOT NULL,
                        quality INTEGER NOT NULL,
                        response_time REAL NOT NULL,
                        previous_interval INTEGER,
                        new_interval INTEGER,
                        ease_factor REAL,
                        repetitions INTEGER,
                        lapses INTEGER,
                        data TEXT,
                        FOREIGN KEY (card_id) REFERENCES card_progress (card_id)
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_due_date 
                    ON card_progress (due_date)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_due 
                    ON card_progress (user_id, due_date)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_review_time 
                    ON review_logs (review_time)
                """)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _calculate_next_interval(
        self,
        quality: ReviewQuality,
        repetitions: int,
        ease_factor: float,
        interval: int
    ) -> Tuple[int, float]:
        """
        Calculate next interval using SM-2 algorithm.
        
        Args:
            quality: Quality of response (0-5)
            repetitions: Number of successful reviews
            ease_factor: Current ease factor
            interval: Current interval
            
        Returns:
            Tuple of (new_interval, new_ease_factor)
        """
        # Handle failed reviews
        if quality < 3:
            # Reset repetitions
            repetitions = 0
            interval = self.params.again_interval
            
            # Decrease ease factor for failed reviews
            if quality == 0:
                ease_factor = max(
                    self.params.minimum_ease_factor,
                    ease_factor - 0.3
                )
            elif quality == 1:
                ease_factor = max(
                    self.params.minimum_ease_factor,
                    ease_factor - 0.2
                )
            elif quality == 2:
                ease_factor = max(
                    self.params.minimum_ease_factor,
                    ease_factor - 0.15
                )
            
            return interval, ease_factor
        
        # Successful review (quality >= 3)
        
        # Update ease factor based on quality
        if quality == 3:  # Correct with difficulty
            ease_factor = max(
                self.params.minimum_ease_factor,
                ease_factor - 0.15
            )
        elif quality == 4:  # Correct with hesitation
            ease_factor = ease_factor  # No change
        elif quality == 5:  # Perfect recall
            ease_factor = ease_factor + 0.15
        
        # Calculate new interval
        if repetitions == 0:
            # First successful review
            if quality == 3:
                interval = self.params.hard_interval
            elif quality == 4:
                interval = self.params.good_interval
            else:  # quality == 5
                interval = self.params.easy_interval
        else:
            # Subsequent reviews
            if quality == 3:  # Hard
                interval = int(interval * self.params.hard_penalty)
            elif quality == 4:  # Good
                interval = int(interval * ease_factor)
            else:  # Easy
                interval = int(interval * ease_factor * self.params.easy_bonus)
        
        # Enforce maximum interval
        interval = min(interval, self.params.max_interval)
        
        return interval, ease_factor
    
    def process_review(
        self,
        card_id: str,
        user_id: str,
        quality: Union[int, ReviewQuality],
        response_time: float,
        deck_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> CardProgress:
        """
        Process a flashcard review.
        
        Args:
            card_id: Card identifier
            user_id: User identifier
            quality: Review quality (0-5)
            response_time: Response time in seconds
            deck_name: Optional deck name
            metadata: Additional metadata
            
        Returns:
            Updated CardProgress
        """
        # Convert quality to enum
        if isinstance(quality, int):
            quality = ReviewQuality(quality)
        
        with self._lock:
            # Get or create progress
            progress = self.get_card_progress(card_id, user_id)
            if progress is None:
                progress = CardProgress(
                    card_id=card_id,
                    user_id=user_id,
                    deck_name=deck_name
                )
            
            # Store old values
            old_repetitions = progress.repetitions
            old_interval = progress.interval
            old_ease = progress.ease_factor
            
            # Calculate new interval
            new_interval, new_ease = self._calculate_next_interval(
                quality=quality,
                repetitions=progress.repetitions,
                ease_factor=progress.ease_factor,
                interval=progress.interval
            )
            
            # Update progress
            progress.interval = new_interval
            progress.ease_factor = new_ease
            
            if quality >= 3:
                progress.repetitions += 1
            else:
                progress.lapses += 1
            
            # Set due date
            progress.due_date = datetime.now() + timedelta(days=new_interval)
            
            # Update review log
            log = ReviewLog(
                card_id=card_id,
                user_id=user_id,
                quality=quality,
                response_time=response_time,
                previous_interval=old_interval,
                new_interval=new_interval,
                ease_factor=new_ease,
                repetitions=progress.repetitions,
                lapses=progress.lapses,
                scheduled_days=new_interval,
                deck_name=deck_name or progress.deck_name,
                metadata=metadata or {}
            )
            
            progress.review_history.append(log)
            progress.total_reviews += 1
            progress.last_review = datetime.now()
            progress.updated_at = datetime.now()
            
            # Update average response time
            progress.average_response_time = (
                (progress.average_response_time * (progress.total_reviews - 1) + response_time) /
                progress.total_reviews
            )
            
            # Save to cache and database
            self._progress_cache[f"{user_id}:{card_id}"] = progress
            self._save_progress(progress)
            self._save_review_log(log)
            
            logger.debug(
                f"Processed review for card {card_id}: quality={quality.value}, "
                f"interval={old_interval}->{new_interval}, ease={old_ease:.2f}->{new_ease:.2f}"
            )
            
            return progress
    
    def get_card_progress(
        self,
        card_id: str,
        user_id: str
    ) -> Optional[CardProgress]:
        """
        Get progress for a specific card.
        
        Args:
            card_id: Card identifier
            user_id: User identifier
            
        Returns:
            CardProgress if found, None otherwise
        """
        cache_key = f"{user_id}:{card_id}"
        
        # Check cache first
        with self._lock:
            if cache_key in self._progress_cache:
                return self._progress_cache[cache_key]
        
        # Check database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT * FROM card_progress 
                    WHERE card_id = ? AND user_id = ?
                    """,
                    (card_id, user_id)
                )
                row = cursor.fetchone()
                
                if row:
                    # Load review history
                    review_cursor = conn.execute(
                        """
                        SELECT * FROM review_logs 
                        WHERE card_id = ? AND user_id = ?
                        ORDER BY review_time
                        """,
                        (card_id, user_id)
                    )
                    reviews = []
                    for review_row in review_cursor.fetchall():
                        log_data = json.loads(review_row['data']) if review_row['data'] else {}
                        reviews.append(ReviewLog(
                            card_id=review_row['card_id'],
                            user_id=review_row['user_id'],
                            review_time=datetime.fromisoformat(review_row['review_time']),
                            quality=ReviewQuality(review_row['quality']),
                            response_time=review_row['response_time'],
                            previous_interval=review_row['previous_interval'],
                            new_interval=review_row['new_interval'],
                            ease_factor=review_row['ease_factor'],
                            repetitions=review_row['repetitions'],
                            lapses=review_row['lapses'],
                            **log_data
                        ))
                    
                    # Create progress object
                    progress = CardProgress(
                        card_id=row['card_id'],
                        user_id=row['user_id'],
                        deck_name=row['deck_name'],
                        interval=row['interval'],
                        ease_factor=row['ease_factor'],
                        repetitions=row['repetitions'],
                        lapses=row['lapses'],
                        due_date=datetime.fromisoformat(row['due_date']),
                        last_review=datetime.fromisoformat(row['last_review']) if row['last_review'] else None,
                        total_reviews=row['total_reviews'],
                        average_response_time=row['average_response_time'],
                        review_history=reviews,
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                    
                    # Update cache
                    with self._lock:
                        self._progress_cache[cache_key] = progress
                    
                    return progress
                    
        except Exception as e:
            logger.error(f"Failed to load progress for card {card_id}: {e}")
        
        return None
    
    def get_due_cards(
        self,
        user_id: str,
        deck_name: Optional[str] = None,
        limit: int = 100,
        current_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get cards due for review.
        
        Args:
            user_id: User identifier
            deck_name: Optional deck filter
            limit: Maximum number of cards
            current_date: Current date (defaults to now)
            
        Returns:
            List of due cards with progress info
        """
        if current_date is None:
            current_date = datetime.now()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = """
                    SELECT * FROM card_progress 
                    WHERE user_id = ? 
                    AND due_date <= ?
                """
                params = [user_id, current_date.isoformat()]
                
                if deck_name:
                    query += " AND deck_name = ?"
                    params.append(deck_name)
                
                query += " ORDER BY due_date LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                
                due_cards = []
                for row in cursor.fetchall():
                    progress = CardProgress(
                        card_id=row['card_id'],
                        user_id=row['user_id'],
                        deck_name=row['deck_name'],
                        interval=row['interval'],
                        ease_factor=row['ease_factor'],
                        repetitions=row['repetitions'],
                        lapses=row['lapses'],
                        due_date=datetime.fromisoformat(row['due_date']),
                        last_review=datetime.fromisoformat(row['last_review']) if row['last_review'] else None,
                        total_reviews=row['total_reviews'],
                        average_response_time=row['average_response_time'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                    
                    due_cards.append({
                        'card_id': progress.card_id,
                        'deck_name': progress.deck_name,
                        'interval': progress.interval,
                        'ease_factor': progress.ease_factor,
                        'repetitions': progress.repetitions,
                        'lapses': progress.lapses,
                        'due_date': progress.due_date.isoformat(),
                        'days_overdue': progress.days_overdue(current_date),
                        'last_review': progress.last_review.isoformat() if progress.last_review else None
                    })
                
                return due_cards
                
        except Exception as e:
            logger.error(f"Failed to get due cards: {e}")
            return []
    
    def get_review_stats(
        self,
        user_id: str,
        deck_name: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get review statistics for a user.
        
        Args:
            user_id: User identifier
            deck_name: Optional deck filter
            days: Number of days to analyze
            
        Returns:
            Statistics dictionary
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get all progress for user
                query = "SELECT * FROM card_progress WHERE user_id = ?"
                params = [user_id]
                
                if deck_name:
                    query += " AND deck_name = ?"
                    params.append(deck_name)
                
                cursor = conn.execute(query, params)
                cards = cursor.fetchall()
                
                # Calculate statistics
                total_cards = len(cards)
                if total_cards == 0:
                    return {
                        'total_cards': 0,
                        'cards_learned': 0,
                        'cards_in_learning': 0,
                        'average_ease': 0,
                        'average_interval': 0,
                        'retention_rate': 0
                    }
                
                # Card states
                cards_learned = sum(1 for c in cards if c['repetitions'] >= 5)
                cards_in_learning = total_cards - cards_learned
                
                # Averages
                average_ease = sum(c['ease_factor'] for c in cards) / total_cards
                average_interval = sum(c['interval'] for c in cards) / total_cards
                
                # Get recent reviews
                cutoff = (datetime.now() - timedelta(days=days)).isoformat()
                review_cursor = conn.execute(
                    """
                    SELECT quality FROM review_logs 
                    WHERE user_id = ? AND review_time >= ?
                    """,
                    (user_id, cutoff)
                )
                
                reviews = review_cursor.fetchall()
                if reviews:
                    successful = sum(1 for r in reviews if r['quality'] >= 3)
                    retention_rate = (successful / len(reviews)) * 100
                else:
                    retention_rate = 0
                
                # Get due counts
                now = datetime.now().isoformat()
                due_cursor = conn.execute(
                    """
                    SELECT COUNT(*) as count FROM card_progress 
                    WHERE user_id = ? AND due_date <= ?
                    """,
                    (user_id, now)
                )
                due_today = due_cursor.fetchone()['count']
                
                # Get learning curve
                learning_curve = []
                for card in cards[:10]:  # Top 10 cards
                    curve_cursor = conn.execute(
                        """
                        SELECT review_time, quality FROM review_logs 
                        WHERE card_id = ? AND user_id = ?
                        ORDER BY review_time
                        """,
                        (card['card_id'], user_id)
                    )
                    card_curve = []
                    for i, r in enumerate(curve_cursor.fetchall()):
                        card_curve.append({
                            'review': i + 1,
                            'quality': r['quality'],
                            'date': r['review_time']
                        })
                    learning_curve.append({
                        'card_id': card['card_id'],
                        'curve': card_curve
                    })
                
                return {
                    'total_cards': total_cards,
                    'cards_learned': cards_learned,
                    'cards_in_learning': cards_in_learning,
                    'average_ease': round(average_ease, 2),
                    'average_interval': round(average_interval, 1),
                    'retention_rate': round(retention_rate, 1),
                    'due_today': due_today,
                    'learning_curve': learning_curve[:5],  # Limit to 5 cards
                    'period_days': days
                }
                
        except Exception as e:
            logger.error(f"Failed to get review stats: {e}")
            return {
                'error': str(e),
                'total_cards': 0
            }
    
    def predict_next_review(
        self,
        card_id: str,
        user_id: str,
        quality: Optional[ReviewQuality] = None
    ) -> Dict[str, Any]:
        """
        Predict when a card will be due next based on hypothetical quality.
        
        Args:
            card_id: Card identifier
            user_id: User identifier
            quality: Optional review quality for prediction
            
        Returns:
            Prediction dictionary
        """
        progress = self.get_card_progress(card_id, user_id)
        if not progress:
            return {
                'error': 'Card not found',
                'card_id': card_id
            }
        
        predictions = {}
        
        if quality is not None:
            # Predict for specific quality
            interval, ease = self._calculate_next_interval(
                quality=quality,
                repetitions=progress.repetitions,
                ease_factor=progress.ease_factor,
                interval=progress.interval
            )
            
            predictions[quality.value] = {
                'interval_days': interval,
                'due_date': (datetime.now() + timedelta(days=interval)).isoformat(),
                'ease_factor': ease
            }
        else:
            # Predict for all qualities
            for q in ReviewQuality:
                interval, ease = self._calculate_next_interval(
                    quality=q,
                    repetitions=progress.repetitions,
                    ease_factor=progress.ease_factor,
                    interval=progress.interval
                )
                
                predictions[q.value] = {
                    'interval_days': interval,
                    'due_date': (datetime.now() + timedelta(days=interval)).isoformat(),
                    'ease_factor': ease
                }
        
        return {
            'card_id': card_id,
            'current_interval': progress.interval,
            'current_ease': progress.ease_factor,
            'current_repetitions': progress.repetitions,
            'current_due': progress.due_date.isoformat(),
            'predictions': predictions
        }
    
    def reset_card(
        self,
        card_id: str,
        user_id: str
    ) -> bool:
        """
        Reset a card to its initial state.
        
        Args:
            card_id: Card identifier
            user_id: User identifier
            
        Returns:
            True if successful
        """
        try:
            with self._lock:
                # Remove from cache
                cache_key = f"{user_id}:{card_id}"
                if cache_key in self._progress_cache:
                    del self._progress_cache[cache_key]
                
                # Delete from database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "DELETE FROM card_progress WHERE card_id = ? AND user_id = ?",
                        (card_id, user_id)
                    )
                    conn.execute(
                        "DELETE FROM review_logs WHERE card_id = ? AND user_id = ?",
                        (card_id, user_id)
                    )
                    conn.commit()
                
                logger.info(f"Reset card {card_id} for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to reset card {card_id}: {e}")
            return False
    
    def _save_progress(self, progress: CardProgress):
        """Save card progress to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO card_progress 
                    (card_id, user_id, deck_name, interval, ease_factor, repetitions, lapses,
                     due_date, last_review, total_reviews, average_response_time, data,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        progress.card_id,
                        progress.user_id,
                        progress.deck_name,
                        progress.interval,
                        progress.ease_factor,
                        progress.repetitions,
                        progress.lapses,
                        progress.due_date.isoformat(),
                        progress.last_review.isoformat() if progress.last_review else None,
                        progress.total_reviews,
                        progress.average_response_time,
                        json.dumps({
                            'tags': progress.tags,
                            'metadata': progress.metadata
                        }),
                        progress.created_at.isoformat(),
                        progress.updated_at.isoformat()
                    )
                )
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to save progress for {progress.card_id}: {e}")
    
    def _save_review_log(self, log: ReviewLog):
        """Save review log to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO review_logs 
                    (card_id, user_id, review_time, quality, response_time,
                     previous_interval, new_interval, ease_factor, repetitions, lapses, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        log.card_id,
                        log.user_id,
                        log.review_time.isoformat(),
                        log.quality,
                        log.response_time,
                        log.previous_interval,
                        log.new_interval,
                        log.ease_factor,
                        log.repetitions,
                        log.lapses,
                        json.dumps(log.metadata)
                    )
                )
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to save review log: {e}")
    
    def optimize_schedule(
        self,
        user_id: str,
        target_reviews_per_day: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Optimize review schedule to spread out cards evenly.
        
        Args:
            user_id: User identifier
            target_reviews_per_day: Target number of daily reviews
            
        Returns:
            Optimized schedule
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get all active cards
                cursor = conn.execute(
                    """
                    SELECT * FROM card_progress 
                    WHERE user_id = ? 
                    ORDER BY due_date
                    """,
                    (user_id,)
                )
                
                cards = cursor.fetchall()
                
                if not cards:
                    return []
                
                # Calculate load distribution
                today = datetime.now().date()
                schedule = []
                
                for i, card in enumerate(cards):
                    due_date = datetime.fromisoformat(card['due_date']).date()
                    days_from_now = (due_date - today).days
                    
                    schedule.append({
                        'card_id': card['card_id'],
                        'deck_name': card['deck_name'],
                        'due_date': card['due_date'],
                        'days_from_now': days_from_now,
                        'interval': card['interval'],
                        'ease_factor': card['ease_factor'],
                        'suggested_date': due_date.isoformat()
                    })
                
                # Group by due date
                from collections import defaultdict
                by_date = defaultdict(list)
                for item in schedule:
                    by_date[item['due_date'][:10]].append(item)
                
                # Find overloaded days
                overloaded = []
                for date_str, items in by_date.items():
                    if len(items) > target_reviews_per_day * 1.5:  # 50% over target
                        overloaded.append({
                            'date': date_str,
                            'count': len(items),
                            'target': target_reviews_per_day,
                            'excess': len(items) - target_reviews_per_day
                        })
                
                return {
                    'total_cards': len(schedule),
                    'unique_dates': len(by_date),
                    'target_per_day': target_reviews_per_day,
                    'overloaded_days': overloaded,
                    'schedule': schedule[:100]  # Limit output
                }
                
        except Exception as e:
            logger.error(f"Failed to optimize schedule: {e}")
            return []
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export all user data for backup or analysis.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with all user data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get all progress
                progress_cursor = conn.execute(
                    "SELECT * FROM card_progress WHERE user_id = ?",
                    (user_id,)
                )
                
                progress_data = []
                for row in progress_cursor.fetchall():
                    progress_data.append(dict(row))
                
                # Get all reviews
                review_cursor = conn.execute(
                    "SELECT * FROM review_logs WHERE user_id = ? ORDER BY review_time",
                    (user_id,)
                )
                
                review_data = []
                for row in review_cursor.fetchall():
                    review_data.append(dict(row))
                
                return {
                    'user_id': user_id,
                    'export_time': datetime.now().isoformat(),
                    'progress': progress_data,
                    'reviews': review_data,
                    'stats': self.get_review_stats(user_id)
                }
                
        except Exception as e:
            logger.error(f"Failed to export user data: {e}")
            return {'error': str(e)}
    
    def import_user_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """
        Import user data from backup.
        
        Args:
            user_id: User identifier
            data: Previously exported data
            
        Returns:
            True if successful
        """
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    # Clear existing data
                    conn.execute("DELETE FROM card_progress WHERE user_id = ?", (user_id,))
                    conn.execute("DELETE FROM review_logs WHERE user_id = ?", (user_id,))
                    
                    # Import progress
                    for progress in data.get('progress', []):
                        conn.execute(
                            """
                            INSERT INTO card_progress 
                            (card_id, user_id, deck_name, interval, ease_factor, repetitions, lapses,
                             due_date, last_review, total_reviews, average_response_time, data,
                             created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                progress['card_id'],
                                progress['user_id'],
                                progress.get('deck_name'),
                                progress['interval'],
                                progress['ease_factor'],
                                progress['repetitions'],
                                progress['lapses'],
                                progress['due_date'],
                                progress.get('last_review'),
                                progress['total_reviews'],
                                progress['average_response_time'],
                                progress.get('data', '{}'),
                                progress['created_at'],
                                progress['updated_at']
                            )
                        )
                    
                    # Import reviews
                    for review in data.get('reviews', []):
                        conn.execute(
                            """
                            INSERT INTO review_logs 
                            (card_id, user_id, review_time, quality, response_time,
                             previous_interval, new_interval, ease_factor, repetitions, lapses, data)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                review['card_id'],
                                review['user_id'],
                                review['review_time'],
                                review['quality'],
                                review['response_time'],
                                review.get('previous_interval'),
                                review.get('new_interval'),
                                review.get('ease_factor'),
                                review.get('repetitions'),
                                review.get('lapses'),
                                review.get('data', '{}')
                            )
                        )
                    
                    conn.commit()
                
                # Clear cache for this user
                with self._lock:
                    keys_to_remove = [
                        k for k in self._progress_cache 
                        if k.startswith(f"{user_id}:")
                    ]
                    for k in keys_to_remove:
                        del self._progress_cache[k]
                
                logger.info(f"Imported data for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to import user data: {e}")
            return False
    
    def get_learning_insights(self, user_id: str) -> Dict[str, Any]:
        """
        Get learning insights based on review history.
        
        Args:
            user_id: User identifier
            
        Returns:
            Learning insights dictionary
        """
        stats = self.get_review_stats(user_id)
        
        if stats['total_cards'] == 0:
            return {
                'message': 'No learning data available',
                'user_id': user_id
            }
        
        # Calculate additional insights
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Best time of day for learning
                cursor = conn.execute(
                    """
                    SELECT strftime('%H', review_time) as hour,
                           AVG(quality) as avg_quality,
                           COUNT(*) as review_count
                    FROM review_logs
                    WHERE user_id = ? AND quality >= 0
                    GROUP BY hour
                    ORDER BY avg_quality DESC
                    """,
                    (user_id,)
                )
                
                best_hours = []
                for row in cursor.fetchall():
                    best_hours.append({
                        'hour': int(row['hour']),
                        'avg_quality': round(row['avg_quality'], 2),
                        'review_count': row['review_count']
                    })
                
                # Learning speed by deck
                cursor = conn.execute(
                    """
                    SELECT deck_name,
                           AVG(repetitions) as avg_repetitions,
                           COUNT(*) as card_count
                    FROM card_progress
                    WHERE user_id = ? AND deck_name IS NOT NULL
                    GROUP BY deck_name
                    """,
                    (user_id,)
                )
                
                deck_performance = []
                for row in cursor.fetchall():
                    deck_performance.append({
                        'deck': row['deck_name'],
                        'avg_repetitions': round(row['avg_repetitions'], 1),
                        'card_count': row['card_count']
                    })
                
                # Retention trend
                cursor = conn.execute(
                    """
                    SELECT date(review_time) as review_date,
                           AVG(CAST(quality >= 3 AS INTEGER)) * 100 as retention_rate
                    FROM review_logs
                    WHERE user_id = ?
                    GROUP BY review_date
                    ORDER BY review_date DESC
                    LIMIT 30
                    """,
                    (user_id,)
                )
                
                retention_trend = []
                for row in cursor.fetchall():
                    retention_trend.append({
                        'date': row['review_date'],
                        'retention_rate': round(row['retention_rate'], 1)
                    })
                
                return {
                    'user_id': user_id,
                    'best_learning_hours': best_hours[:3],
                    'deck_performance': deck_performance,
                    'retention_trend': retention_trend,
                    'total_stats': stats
                }
                
        except Exception as e:
            logger.error(f"Failed to get learning insights: {e}")
            return {
                'error': str(e),
                'user_id': user_id
            }