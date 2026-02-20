"""
Advanced question bank management with intelligent retrieval and generation
"""

import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import random
import numpy as np
from collections import defaultdict
import logging
from enum import Enum

from .exam_patterns import ExamQuestion, QuestionType
from .difficulty_mapper import DifficultyLevel

class QuestionStatus(Enum):
    """Question status in bank"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"

@dataclass
class BankQuestion(ExamQuestion):
    """Extended question for bank storage"""
    id: str = field(default_factory=lambda: hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8])
    status: QuestionStatus = QuestionStatus.DRAFT
    usage_count: int = 0
    avg_score: float = 0.0
    times_used: int = 0
    last_used: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    variants: List[str] = field(default_factory=list)  # IDs of variant questions
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    source: str = ""  # e.g., "textbook", "previous_exam", "generated"

class QuestionBank:
    """
    Advanced question bank with intelligent retrieval and analytics
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize question bank
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Storage
        self.questions: Dict[str, BankQuestion] = {}
        self.indices = {
            'topic': defaultdict(list),
            'type': defaultdict(list),
            'difficulty': defaultdict(list),
            'bloom_level': defaultdict(list),
            'status': defaultdict(list),
            'tags': defaultdict(list)
        }
        
        # Statistics
        self.stats = {
            'total_questions': 0,
            'by_topic': defaultdict(int),
            'by_type': defaultdict(int),
            'by_difficulty': defaultdict(int),
            'avg_difficulty': 0.0,
            'usage_stats': defaultdict(int)
        }
        
        # Load existing bank if specified
        if 'bank_path' in self.config:
            self.load(self.config['bank_path'])
        
        self.logger = logging.getLogger(__name__)
    
    def add_question(self, question: Union[BankQuestion, Dict[str, Any]]) -> str:
        """
        Add a question to the bank
        
        Args:
            question: Question object or dictionary
            
        Returns:
            Question ID
        """
        if isinstance(question, dict):
            # Convert dict to BankQuestion
            question = BankQuestion(
                text=question.get('text', ''),
                type=question.get('type', QuestionType.SHORT_ANSWER),
                marks=question.get('marks', 1),
                topic=question.get('topic'),
                difficulty=question.get('difficulty', 0.5),
                bloom_level=question.get('bloom_level', 'remember'),
                expected_time=question.get('expected_time', 5),
                answer_key=question.get('answer_key'),
                hints=question.get('hints', []),
                tags=question.get('tags', []),
                source=question.get('source', 'manual')
            )
        
        # Generate ID if not present
        if not question.id:
            question.id = self._generate_id(question)
        
        # Store question
        self.questions[question.id] = question
        
        # Update indices
        self._update_indices(question)
        
        # Update stats
        self._update_stats(question, 'add')
        
        self.logger.info(f"Added question {question.id}")
        return question.id
    
    def add_questions(self, questions: List[Union[BankQuestion, Dict[str, Any]]]) -> List[str]:
        """Add multiple questions"""
        ids = []
        for q in questions:
            try:
                q_id = self.add_question(q)
                ids.append(q_id)
            except Exception as e:
                self.logger.error(f"Error adding question: {e}")
        return ids
    
    def get_question(self, question_id: str) -> Optional[BankQuestion]:
        """Get question by ID"""
        return self.questions.get(question_id)
    
    def get_questions(
        self,
        topic: Optional[str] = None,
        q_type: Optional[QuestionType] = None,
        difficulty: Optional[float] = None,
        difficulty_range: Optional[Tuple[float, float]] = None,
        bloom_level: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: QuestionStatus = QuestionStatus.APPROVED,
        limit: int = 100
    ) -> List[BankQuestion]:
        """
        Get questions matching criteria
        
        Args:
            topic: Filter by topic
            q_type: Filter by question type
            difficulty: Filter by exact difficulty
            difficulty_range: Filter by difficulty range (min, max)
            bloom_level: Filter by Bloom's level
            tags: Filter by tags (any match)
            status: Question status
            limit: Maximum number to return
            
        Returns:
            List of matching questions
        """
        # Start with all questions or filter by status
        candidates = list(self.questions.values())
        
        # Apply filters
        if topic:
            candidates = [q for q in candidates if q.topic == topic]
        
        if q_type:
            candidates = [q for q in candidates if q.type == q_type]
        
        if difficulty is not None:
            candidates = [q for q in candidates 
                         if abs(q.difficulty - difficulty) < 0.1]
        
        if difficulty_range:
            min_d, max_d = difficulty_range
            candidates = [q for q in candidates 
                         if min_d <= q.difficulty <= max_d]
        
        if bloom_level:
            candidates = [q for q in candidates if q.bloom_level == bloom_level]
        
        if tags:
            candidates = [q for q in candidates 
                         if any(tag in q.tags for tag in tags)]
        
        if status:
            candidates = [q for q in candidates if q.status == status]
        
        # Sort by usage count (least used first) for balanced selection
        candidates.sort(key=lambda q: (q.usage_count, -q.difficulty))
        
        return candidates[:limit]
    
    def get_random_questions(
        self,
        count: int,
        **filters
    ) -> List[BankQuestion]:
        """Get random questions matching filters"""
        candidates = self.get_questions(**filters)
        
        if not candidates:
            return []
        
        # Random selection
        selected = random.sample(
            candidates,
            min(count, len(candidates))
        )
        
        return selected
    
    def get_questions_for_exam(
        self,
        topic_weightage: Dict[str, float],
        type_distribution: Dict[str, int],
        difficulty_distribution: Dict[str, float],
        total_questions: int
    ) -> List[BankQuestion]:
        """
        Get questions for an exam based on specifications
        
        Args:
            topic_weightage: Topic -> weight mapping
            type_distribution: Question type -> count
            difficulty_distribution: Difficulty level -> proportion
            total_questions: Total questions needed
            
        Returns:
            List of selected questions
        """
        selected = []
        used_ids = set()
        
        # Calculate questions per topic
        questions_per_topic = {}
        for topic, weight in topic_weightage.items():
            questions_per_topic[topic] = max(1, int(total_questions * weight))
        
        # Select questions by type and topic
        for q_type, count in type_distribution.items():
            type_questions = []
            
            # Get questions of this type
            candidates = self.get_questions(
                q_type=QuestionType(q_type),
                status=QuestionStatus.APPROVED
            )
            
            if not candidates:
                continue
            
            # Group by topic
            by_topic = defaultdict(list)
            for q in candidates:
                if q.id not in used_ids:
                    by_topic[q.topic].append(q)
            
            # Select from each topic according to weightage
            for topic, needed in questions_per_topic.items():
                topic_qs = by_topic.get(topic, [])
                if topic_qs:
                    # Apply difficulty distribution
                    difficulty_filtered = self._filter_by_difficulty(
                        topic_qs,
                        difficulty_distribution
                    )
                    
                    # Take needed number
                    take = min(needed, len(difficulty_filtered))
                    selected_qs = random.sample(difficulty_filtered, take)
                    
                    type_questions.extend(selected_qs)
                    for q in selected_qs:
                        used_ids.add(q.id)
            
            # Add to final selection
            selected.extend(type_questions[:count])
        
        return selected[:total_questions]
    
    def update_question(
        self,
        question_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update question attributes"""
        if question_id not in self.questions:
            return False
        
        question = self.questions[question_id]
        
        # Remove from old indices before update
        self._remove_from_indices(question)
        
        # Update fields
        for key, value in updates.items():
            if hasattr(question, key):
                setattr(question, key, value)
        
        question.updated_at = datetime.now()
        
        # Add to new indices
        self._update_indices(question)
        
        return True
    
    def record_usage(
        self,
        question_id: str,
        score: Optional[float] = None
    ):
        """Record that a question was used in an exam"""
        if question_id not in self.questions:
            return
        
        q = self.questions[question_id]
        q.usage_count += 1
        q.last_used = datetime.now()
        
        if score is not None:
            # Update average score
            total = q.avg_score * q.times_used + score
            q.times_used += 1
            q.avg_score = total / q.times_used
        
        self.stats['usage_stats'][question_id] += 1
    
    def delete_question(self, question_id: str) -> bool:
        """Delete question from bank"""
        if question_id not in self.questions:
            return False
        
        # Remove from indices
        self._remove_from_indices(self.questions[question_id])
        
        # Delete
        del self.questions[question_id]
        
        return True
    
    def search_questions(
        self,
        query: str,
        **filters
    ) -> List[BankQuestion]:
        """Search questions by text"""
        query_lower = query.lower()
        
        candidates = self.get_questions(**filters)
        
        # Simple text search
        results = []
        for q in candidates:
            if query_lower in q.text.lower():
                results.append(q)
            elif q.answer_key and query_lower in q.answer_key.lower():
                results.append(q)
        
        return results
    
    def get_similar_questions(
        self,
        question_id: str,
        count: int = 5
    ) -> List[BankQuestion]:
        """Get questions similar to given question"""
        if question_id not in self.questions:
            return []
        
        target = self.questions[question_id]
        candidates = self.get_questions(
            topic=target.topic,
            status=QuestionStatus.APPROVED
        )
        
        # Remove target itself
        candidates = [q for q in candidates if q.id != question_id]
        
        # Calculate similarity scores
        scores = []
        for q in candidates:
            score = self._calculate_similarity(target, q)
            scores.append((score, q))
        
        # Sort by similarity
        scores.sort(reverse=True, key=lambda x: x[0])
        
        return [q for _, q in scores[:count]]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get question bank statistics"""
        return {
            'total_questions': len(self.questions),
            'by_topic': dict(self.stats['by_topic']),
            'by_type': {k.value: v for k, v in self.stats['by_type'].items()},
            'by_difficulty': dict(self.stats['by_difficulty']),
            'avg_difficulty': self.stats['avg_difficulty'],
            'most_used': self._get_most_used_questions(10),
            'least_used': self._get_least_used_questions(10),
            'questions_by_status': self._count_by_status(),
            'recently_added': self._get_recent_questions(10)
        }
    
    def export(
        self,
        format: str = 'json',
        include_metadata: bool = True
    ) -> Union[str, Dict]:
        """Export question bank"""
        if format == 'json':
            data = {
                'version': '1.0',
                'exported_at': datetime.now().isoformat(),
                'questions': []
            }
            
            for q in self.questions.values():
                q_dict = asdict(q)
                if not include_metadata:
                    # Remove internal fields
                    q_dict.pop('usage_count', None)
                    q_dict.pop('avg_score', None)
                    q_dict.pop('times_used', None)
                    q_dict.pop('variants', None)
                data['questions'].append(q_dict)
            
            return data
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def save(self, path: Union[str, Path]):
        """Save question bank to file"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.export('json', include_metadata=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        self.logger.info(f"Saved question bank to {path}")
    
    def load(self, path: Union[str, Path]):
        """Load question bank from file"""
        path = Path(path)
        
        if not path.exists():
            self.logger.warning(f"Question bank file not found: {path}")
            return
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Clear existing
        self.questions.clear()
        self.indices = {k: defaultdict(list) for k in self.indices}
        self.stats = {k: defaultdict(int) if isinstance(v, defaultdict) else v 
                     for k, v in self.stats.items()}
        
        # Load questions
        for q_data in data.get('questions', []):
            # Convert string enums back
            if 'type' in q_data:
                q_data['type'] = QuestionType(q_data['type'])
            if 'status' in q_data:
                q_data['status'] = QuestionStatus(q_data['status'])
            if 'last_used' in q_data and q_data['last_used']:
                q_data['last_used'] = datetime.fromisoformat(q_data['last_used'])
            if 'created_at' in q_data:
                q_data['created_at'] = datetime.fromisoformat(q_data['created_at'])
            if 'updated_at' in q_data:
                q_data['updated_at'] = datetime.fromisoformat(q_data['updated_at'])
            
            q = BankQuestion(**q_data)
            self.questions[q.id] = q
            self._update_indices(q)
        
        # Update stats
        self._recalculate_stats()
        
        self.logger.info(f"Loaded {len(self.questions)} questions from {path}")
    
    def _generate_id(self, question: BankQuestion) -> str:
        """Generate unique ID for question"""
        content = f"{question.text}{question.topic}{datetime.now()}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def _update_indices(self, question: BankQuestion):
        """Update search indices for question"""
        if question.topic:
            self.indices['topic'][question.topic].append(question.id)
        
        self.indices['type'][question.type.value].append(question.id)
        
        # Difficulty bucket
        diff_bucket = self._difficulty_to_bucket(question.difficulty)
        self.indices['difficulty'][diff_bucket].append(question.id)
        
        if question.bloom_level:
            self.indices['bloom_level'][question.bloom_level].append(question.id)
        
        self.indices['status'][question.status.value].append(question.id)
        
        for tag in question.tags:
            self.indices['tags'][tag].append(question.id)
    
    def _remove_from_indices(self, question: BankQuestion):
        """Remove question from indices"""
        if question.topic:
            if question.id in self.indices['topic'][question.topic]:
                self.indices['topic'][question.topic].remove(question.id)
        
        if question.id in self.indices['type'][question.type.value]:
            self.indices['type'][question.type.value].remove(question.id)
        
        diff_bucket = self._difficulty_to_bucket(question.difficulty)
        if question.id in self.indices['difficulty'][diff_bucket]:
            self.indices['difficulty'][diff_bucket].remove(question.id)
        
        if question.bloom_level:
            if question.id in self.indices['bloom_level'][question.bloom_level]:
                self.indices['bloom_level'][question.bloom_level].remove(question.id)
        
        if question.id in self.indices['status'][question.status.value]:
            self.indices['status'][question.status.value].remove(question.id)
        
        for tag in question.tags:
            if tag in self.indices['tags']:
                if question.id in self.indices['tags'][tag]:
                    self.indices['tags'][tag].remove(question.id)
    
    def _update_stats(self, question: BankQuestion, operation: str = 'add'):
        """Update statistics"""
        if operation == 'add':
            self.stats['total_questions'] += 1
            
            if question.topic:
                self.stats['by_topic'][question.topic] += 1
            
            self.stats['by_type'][question.type] += 1
            
            diff_level = self._difficulty_to_level(question.difficulty)
            self.stats['by_difficulty'][diff_level] += 1
            
            # Recalculate average difficulty
            total_diff = sum(q.difficulty for q in self.questions.values())
            self.stats['avg_difficulty'] = total_diff / len(self.questions)
    
    def _recalculate_stats(self):
        """Recalculate all statistics"""
        self.stats['total_questions'] = len(self.questions)
        self.stats['by_topic'].clear()
        self.stats['by_type'].clear()
        self.stats['by_difficulty'].clear()
        
        total_diff = 0
        
        for q in self.questions.values():
            if q.topic:
                self.stats['by_topic'][q.topic] += 1
            
            self.stats['by_type'][q.type] += 1
            
            diff_level = self._difficulty_to_level(q.difficulty)
            self.stats['by_difficulty'][diff_level] += 1
            
            total_diff += q.difficulty
        
        if self.stats['total_questions'] > 0:
            self.stats['avg_difficulty'] = total_diff / self.stats['total_questions']
    
    def _difficulty_to_bucket(self, difficulty: float) -> str:
        """Convert difficulty to bucket string"""
        if difficulty < 0.2:
            return 'very_easy'
        elif difficulty < 0.4:
            return 'easy'
        elif difficulty < 0.6:
            return 'medium'
        elif difficulty < 0.8:
            return 'hard'
        else:
            return 'very_hard'
    
    def _difficulty_to_level(self, difficulty: float) -> str:
        """Convert difficulty to level string"""
        return self._difficulty_to_bucket(difficulty)
    
    def _filter_by_difficulty(
        self,
        questions: List[BankQuestion],
        distribution: Dict[str, float]
    ) -> List[BankQuestion]:
        """Filter questions to match difficulty distribution"""
        if not distribution:
            return questions
        
        filtered = []
        
        # Group questions by difficulty level
        by_level = defaultdict(list)
        for q in questions:
            level = self._difficulty_to_level(q.difficulty)
            by_level[level].append(q)
        
        # Take appropriate number from each level
        for level, proportion in distribution.items():
            level_questions = by_level.get(level, [])
            needed = max(1, int(len(questions) * proportion))
            filtered.extend(level_questions[:needed])
        
        return filtered
    
    def _calculate_similarity(
        self,
        q1: BankQuestion,
        q2: BankQuestion
    ) -> float:
        """Calculate similarity between two questions"""
        score = 0.0
        
        # Same topic
        if q1.topic == q2.topic:
            score += 0.3
        
        # Same question type
        if q1.type == q2.type:
            score += 0.2
        
        # Similar difficulty
        difficulty_diff = abs(q1.difficulty - q2.difficulty)
        score += (1 - difficulty_diff) * 0.2
        
        # Same Bloom's level
        if q1.bloom_level == q2.bloom_level:
            score += 0.15
        
        # Shared tags
        shared_tags = set(q1.tags) & set(q2.tags)
        score += len(shared_tags) * 0.05
        
        return min(1.0, score)
    
    def _get_most_used_questions(self, n: int) -> List[Dict[str, Any]]:
        """Get most frequently used questions"""
        usage = [(q.usage_count, q.id, q) 
                 for q in self.questions.values()]
        usage.sort(reverse=True)
        
        return [{
            'id': q.id,
            'text': q.text[:100] + '...',
            'usage_count': q.usage_count,
            'topic': q.topic
        } for _, _, q in usage[:n]]
    
    def _get_least_used_questions(self, n: int) -> List[Dict[str, Any]]:
        """Get least frequently used questions"""
        usage = [(q.usage_count, q.id, q) 
                 for q in self.questions.values()]
        usage.sort()
        
        return [{
            'id': q.id,
            'text': q.text[:100] + '...',
            'usage_count': q.usage_count,
            'topic': q.topic
        } for _, _, q in usage[:n]]
    
    def _count_by_status(self) -> Dict[str, int]:
        """Count questions by status"""
        counts = defaultdict(int)
        for q in self.questions.values():
            counts[q.status.value] += 1
        return dict(counts)
    
    def _get_recent_questions(self, n: int) -> List[Dict[str, Any]]:
        """Get most recently added questions"""
        recent = [(q.created_at, q) for q in self.questions.values()]
        recent.sort(reverse=True)
        
        return [{
            'id': q.id,
            'text': q.text[:100] + '...',
            'topic': q.topic,
            'created_at': q.created_at.isoformat()
        } for _, q in recent[:n]]