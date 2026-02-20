"""
Exam pattern analysis and prediction for educational content
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import defaultdict
import logging

class QuestionType(Enum):
    """Types of exam questions"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    ESSAY = "essay"
    NUMERICAL = "numerical"
    DERIVATION = "derivation"
    PROOF = "proof"
    DIAGRAM = "diagram"
    MATCHING = "matching"
    ASSERTION_REASON = "assertion_reason"

@dataclass
class ExamQuestion:
    """Represents an exam question"""
    text: str
    type: QuestionType
    marks: int
    topic: Optional[str] = None
    difficulty: float = 0.5
    bloom_level: str = "remember"
    expected_time: int = 5  # minutes
    answer_key: Optional[str] = None
    hints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExamPattern:
    """Represents an exam pattern"""
    name: str
    subject: str
    total_marks: int
    duration: int  # minutes
    sections: List[Dict[str, Any]] = field(default_factory=list)
    question_distribution: Dict[str, int] = field(default_factory=dict)
    topic_weightage: Dict[str, float] = field(default_factory=dict)
    difficulty_distribution: Dict[str, float] = field(default_factory=dict)
    marking_scheme: Dict[str, Any] = field(default_factory=dict)
    sample_questions: List[ExamQuestion] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class ExamPatterns:
    """
    Advanced exam pattern analysis and generation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize exam patterns analyzer
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Load common exam patterns
        self.common_patterns = self._load_common_patterns()
        
        # Question type patterns
        self.question_patterns = self._compile_question_patterns()
        
        # Bloom's taxonomy levels
        self.bloom_levels = [
            'remember', 'understand', 'apply', 'analyze', 'evaluate', 'create'
        ]
        
        self.logger = logging.getLogger(__name__)
    
    def analyze_exam_pattern(
        self,
        questions: List[Dict[str, Any]],
        **kwargs
    ) -> ExamPattern:
        """
        Analyze exam pattern from question set
        
        Args:
            questions: List of question dictionaries
            **kwargs: Additional arguments
            
        Returns:
            ExamPattern object
        """
        # Convert to ExamQuestion objects
        exam_questions = []
        for q in questions:
            if isinstance(q, dict):
                exam_q = ExamQuestion(
                    text=q.get('text', ''),
                    type=self._detect_question_type(q.get('text', '')),
                    marks=q.get('marks', 1),
                    topic=q.get('topic'),
                    difficulty=q.get('difficulty', 0.5),
                    bloom_level=q.get('bloom_level', 'remember'),
                    expected_time=q.get('expected_time', 5),
                    answer_key=q.get('answer_key'),
                    hints=q.get('hints', [])
                )
                exam_questions.append(exam_q)
        
        # Calculate statistics
        total_marks = sum(q.marks for q in exam_questions)
        
        # Question type distribution
        type_dist = defaultdict(int)
        for q in exam_questions:
            type_dist[q.type.value] += q.marks
        
        # Topic weightage
        topic_weight = defaultdict(float)
        for q in exam_questions:
            if q.topic:
                topic_weight[q.topic] += q.marks
        total = sum(topic_weight.values())
        if total > 0:
            topic_weight = {k: v/total for k, v in topic_weight.items()}
        
        # Difficulty distribution
        difficulty_dist = defaultdict(int)
        for q in exam_questions:
            level = self._difficulty_to_level(q.difficulty)
            difficulty_dist[level] += q.marks
        
        # Create exam pattern
        pattern = ExamPattern(
            name=kwargs.get('name', 'Analyzed Exam'),
            subject=kwargs.get('subject', 'Unknown'),
            total_marks=total_marks,
            duration=kwargs.get('duration', 180),
            question_distribution=dict(type_dist),
            topic_weightage=dict(topic_weight),
            difficulty_distribution=dict(difficulty_dist),
            marking_scheme=self._infer_marking_scheme(exam_questions),
            sample_questions=exam_questions[:10]  # Keep first 10 as samples
        )
        
        return pattern
    
    def generate_exam_pattern(
        self,
        subject: str,
        topics: List[str],
        total_marks: int,
        duration: int,
        pattern_type: str = 'standard',
        **kwargs
    ) -> ExamPattern:
        """
        Generate an exam pattern based on parameters
        
        Args:
            subject: Subject name
            topics: List of topics
            total_marks: Total marks
            duration: Duration in minutes
            pattern_type: Type of pattern (standard, competitive, etc.)
            **kwargs: Additional arguments
            
        Returns:
            Generated ExamPattern
        """
        # Get base pattern
        base_pattern = self.common_patterns.get(
            pattern_type,
            self.common_patterns['standard']
        )
        
        # Calculate question distribution
        question_dist = self._calculate_question_distribution(
            total_marks,
            base_pattern
        )
        
        # Calculate topic weightage
        topic_weightage = self._calculate_topic_weightage(
            topics,
            **kwargs
        )
        
        # Set difficulty distribution
        difficulty_dist = base_pattern['difficulty_distribution']
        
        # Generate sections
        sections = self._generate_sections(
            question_dist,
            topic_weightage,
            difficulty_dist
        )
        
        # Create pattern
        pattern = ExamPattern(
            name=f"{subject} - {pattern_type.title()} Exam",
            subject=subject,
            total_marks=total_marks,
            duration=duration,
            sections=sections,
            question_distribution=question_dist,
            topic_weightage=topic_weightage,
            difficulty_distribution=difficulty_dist,
            marking_scheme=self._create_marking_scheme(question_dist)
        )
        
        return pattern
    
    def predict_questions(
        self,
        syllabus_topics: List[str],
        historical_patterns: List[ExamPattern],
        num_questions: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Predict likely questions based on historical patterns
        
        Args:
            syllabus_topics: List of syllabus topics
            historical_patterns: List of previous exam patterns
            num_questions: Number of questions to predict
            
        Returns:
            List of predicted questions
        """
        if not historical_patterns:
            return []
        
        # Analyze historical trends
        topic_frequency = defaultdict(int)
        type_frequency = defaultdict(int)
        difficulty_avg = []
        
        for pattern in historical_patterns:
            for q in pattern.sample_questions:
                if q.topic in syllabus_topics:
                    topic_frequency[q.topic] += 1
                    type_frequency[q.type.value] += 1
                    difficulty_avg.append(q.difficulty)
        
        # Calculate probabilities
        total_questions = sum(topic_frequency.values())
        if total_questions == 0:
            return []
        
        topic_probs = {k: v/total_questions for k, v in topic_frequency.items()}
        type_probs = {k: v/total_questions for k, v in type_frequency.items()}
        avg_difficulty = np.mean(difficulty_avg) if difficulty_avg else 0.5
        
        # Generate predicted questions
        predicted = []
        topics_list = list(topic_probs.keys())
        probs_list = list(topic_probs.values())
        
        for _ in range(num_questions):
            # Select topic based on probability
            if topics_list:
                topic = np.random.choice(topics_list, p=probs_list)
                
                # Select question type
                q_type = max(type_probs.items(), key=lambda x: x[1])[0]
                
                predicted.append({
                    'topic': topic,
                    'type': q_type,
                    'difficulty': avg_difficulty,
                    'confidence': topic_probs[topic]
                })
        
        return predicted
    
    def _detect_question_type(self, question_text: str) -> QuestionType:
        """Detect question type from text"""
        text_lower = question_text.lower()
        
        # Check patterns
        for q_type, patterns in self.question_patterns.items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    return q_type
        
        # Default based on question length
        word_count = len(text_lower.split())
        if word_count < 10:
            return QuestionType.SHORT_ANSWER
        elif word_count < 50:
            return QuestionType.LONG_ANSWER
        else:
            return QuestionType.ESSAY
    
    def _difficulty_to_level(self, difficulty: float) -> str:
        """Convert numeric difficulty to level"""
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
    
    def _infer_marking_scheme(
        self,
        questions: List[ExamQuestion]
    ) -> Dict[str, Any]:
        """Infer marking scheme from questions"""
        scheme = {
            'negative_marking': False,
            'partial_marks': False,
            'marks_per_question': defaultdict(list)
        }
        
        # Group marks by question type
        for q in questions:
            scheme['marks_per_question'][q.type.value].append(q.marks)
        
        # Check for negative marking indicators
        negative_indicators = ['negative', 'deduction', 'penalty']
        for q in questions:
            if any(ind in q.text.lower() for ind in negative_indicators):
                scheme['negative_marking'] = True
                break
        
        return scheme
    
    def _calculate_question_distribution(
        self,
        total_marks: int,
        base_pattern: Dict[str, Any]
    ) -> Dict[str, int]:
        """Calculate distribution of marks by question type"""
        distribution = {}
        remaining_marks = total_marks
        
        # Apply base pattern percentages
        for q_type, percentage in base_pattern['type_percentages'].items():
            marks = int(total_marks * percentage / 100)
            marks = min(marks, remaining_marks)
            if marks > 0:
                distribution[q_type] = marks
                remaining_marks -= marks
        
        # Add remaining marks to largest category
        if remaining_marks > 0 and distribution:
            largest_type = max(distribution.items(), key=lambda x: x[1])[0]
            distribution[largest_type] += remaining_marks
        
        return distribution
    
    def _calculate_topic_weightage(
        self,
        topics: List[str],
        **kwargs
    ) -> Dict[str, float]:
        """Calculate weightage for each topic"""
        num_topics = len(topics)
        if num_topics == 0:
            return {}
        
        # Check for emphasis topics
        emphasis_topics = kwargs.get('emphasis_topics', [])
        emphasis_weight = kwargs.get('emphasis_weight', 1.5)
        
        # Base weight
        base_weight = 1.0 / num_topics
        
        weightage = {}
        total_weight = 0
        
        for topic in topics:
            weight = base_weight
            if topic in emphasis_topics:
                weight *= emphasis_weight
            weightage[topic] = weight
            total_weight += weight
        
        # Normalize
        for topic in weightage:
            weightage[topic] /= total_weight
        
        return weightage
    
    def _generate_sections(
        self,
        question_dist: Dict[str, int],
        topic_weightage: Dict[str, float],
        difficulty_dist: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate exam sections"""
        sections = []
        
        # Create sections based on question types
        for q_type, marks in question_dist.items():
            section = {
                'type': q_type,
                'total_marks': marks,
                'num_questions': marks // 5,  # Assume 5 marks per question
                'questions_per_topic': self._allocate_questions_to_topics(
                    marks // 5,
                    topic_weightage
                ),
                'difficulty_breakdown': difficulty_dist
            }
            sections.append(section)
        
        return sections
    
    def _allocate_questions_to_topics(
        self,
        num_questions: int,
        topic_weightage: Dict[str, float]
    ) -> Dict[str, int]:
        """Allocate questions to topics based on weightage"""
        if not topic_weightage:
            return {}
        
        allocation = {}
        remaining = num_questions
        
        # Sort topics by weightage
        sorted_topics = sorted(
            topic_weightage.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for topic, weight in sorted_topics:
            questions = int(num_questions * weight)
            questions = min(questions, remaining)
            if questions > 0:
                allocation[topic] = questions
                remaining -= questions
        
        # Add remaining to top topic
        if remaining > 0 and sorted_topics:
            top_topic = sorted_topics[0][0]
            allocation[top_topic] = allocation.get(top_topic, 0) + remaining
        
        return allocation
    
    def _create_marking_scheme(
        self,
        question_dist: Dict[str, int]
    ) -> Dict[str, Any]:
        """Create marking scheme from question distribution"""
        scheme = {
            'total_marks': sum(question_dist.values()),
            'section_wise': {},
            'negative_marking': False,
            'partial_marks': True
        }
        
        for q_type, marks in question_dist.items():
            scheme['section_wise'][q_type] = {
                'marks_per_question': 5,  # Default
                'num_questions': marks // 5
            }
        
        return scheme
    
    def _load_common_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load common exam patterns"""
        return {
            'standard': {
                'type_percentages': {
                    'multiple_choice': 20,
                    'short_answer': 30,
                    'long_answer': 40,
                    'numerical': 10
                },
                'difficulty_distribution': {
                    'easy': 0.3,
                    'medium': 0.5,
                    'hard': 0.2
                }
            },
            'competitive': {
                'type_percentages': {
                    'multiple_choice': 60,
                    'numerical': 30,
                    'assertion_reason': 10
                },
                'difficulty_distribution': {
                    'easy': 0.2,
                    'medium': 0.5,
                    'hard': 0.3
                }
            },
            'essay_based': {
                'type_percentages': {
                    'essay': 60,
                    'long_answer': 40
                },
                'difficulty_distribution': {
                    'medium': 0.6,
                    'hard': 0.4
                }
            }
        }
    
    def _compile_question_patterns(self) -> Dict[QuestionType, List[re.Pattern]]:
        """Compile regex patterns for question type detection"""
        return {
            QuestionType.MULTIPLE_CHOICE: [
                re.compile(r'which\s+of\s+the\s+following', re.I),
                re.compile(r'choose\s+the\s+correct', re.I),
                re.compile(r'select\s+the', re.I)
            ],
            QuestionType.TRUE_FALSE: [
                re.compile(r'true\s+or\s+false', re.I),
                re.compile(r'state\s+whether', re.I)
            ],
            QuestionType.FILL_BLANK: [
                re.compile(r'fill\s+in\s+the\s+blank', re.I),
                re.compile(r'complete\s+the\s+following', re.I)
            ],
            QuestionType.NUMERICAL: [
                re.compile(r'calculate', re.I),
                re.compile(r'compute', re.I),
                re.compile(r'evaluate', re.I),
                re.compile(r'\d+\s*[+\-*/]\s*\d+')
            ],
            QuestionType.DERIVATION: [
                re.compile(r'derive', re.I),
                re.compile(r'prove', re.I),
                re.compile(r'show\s+that', re.I)
            ],
            QuestionType.ASSERTION_REASON: [
                re.compile(r'assertion.*reason', re.I),
                re.compile(r'statement.*reason', re.I)
            ]
        }