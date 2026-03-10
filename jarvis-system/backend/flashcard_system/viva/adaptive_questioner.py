"""
Adaptive Questioner module for generating and adapting questions based on
student performance and emotional state.
"""

import asyncio
import json
import random
import logging
import re
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple, Set
import numpy as np
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from pydantic import BaseModel, Field, field_validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuestionDifficulty(Enum):
    """Difficulty levels for questions."""
    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"
    EXPERT = "expert"


class QuestionType(Enum):
    """Types of questions."""
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"
    CODE_WRITING = "code_writing"
    CODE_REVIEW = "code_review"
    DIAGRAM = "diagram"
    CONCEPT_EXPLANATION = "concept_explanation"
    PROBLEM_SOLVING = "problem_solving"
    CASE_STUDY = "case_study"
    DEFINITION = "definition"
    COMPARISON = "comparison"



class EmotionalState(Enum):
    """Emotional states that can be detected."""
    CONFIDENT = "confident"
    HESITANT = "hesitant"
    FRUSTRATED = "frustrated"
    ANXIOUS = "anxious"
    BORED = "bored"
    ENGAGED = "engaged"
    CONFUSED = "confused"
    STRESSED = "stressed"
    NEUTRAL = "neutral"


class AnswerEvaluation(Enum):
    """Evaluation of an answer."""
    CORRECT = "correct"
    PARTIALLY_CORRECT = "partially_correct"
    INCORRECT = "incorrect"
    NEEDS_CLARIFICATION = "needs_clarification"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


@dataclass
class QuestionTemplate:
    """Template for generating questions."""
    id: str
    topic: str
    subtopic: Optional[str]
    difficulty: QuestionDifficulty
    question_type: QuestionType
    template_text: str
    answer_template: str
    explanation_template: str
    hints: List[str] = field(default_factory=list)
    resources: List[Dict[str, str]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    usage_count: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    
    def generate_question(self, context: Dict[str, Any]) -> 'Question':
        """Generate a question from this template."""
        # Fill template with context
        question_text = self._fill_template(self.template_text, context)
        answer_text = self._fill_template(self.answer_template, context)
        explanation = self._fill_template(self.explanation_template, context)
        
        return Question(
            id=f"{self.id}_{datetime.now().timestamp()}",
            topic=self.topic,
            subtopic=self.subtopic,
            difficulty=self.difficulty,
            question_type=self.question_type,
            question_text=question_text,
            answer=answer_text,
            explanation=explanation,
            hints=self.hints,
            resources=self.resources,
            metadata={
                'template_id': self.id,
                'tags': self.tags
            }
        )
    
    def _fill_template(self, template: str, context: Dict[str, Any]) -> str:
        """Fill template placeholders with context values."""
        # Simple placeholder replacement
        # In production, use a proper templating engine
        result = template
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        return result


@dataclass
class Question:
    """A question in the viva system."""
    id: str
    topic: str
    subtopic: Optional[str]
    difficulty: QuestionDifficulty
    question_type: QuestionType
    question_text: str
    answer: str
    explanation: str
    hints: List[str] = field(default_factory=list)
    resources: List[Dict[str, str]] = field(default_factory=list)
    options: Optional[List[str]] = None  # For multiple choice
    code_snippet: Optional[str] = None
    diagram_url: Optional[str] = None
    expected_keywords: List[str] = field(default_factory=list)
    time_estimate_seconds: int = 60
    points: int = 10
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'topic': self.topic,
            'subtopic': self.subtopic,
            'difficulty': self.difficulty.value,
            'question_type': self.question_type.value,
            'question_text': self.question_text,
            'answer': self.answer,
            'explanation': self.explanation,
            'hints': self.hints,
            'resources': self.resources,
            'options': self.options,
            'code_snippet': self.code_snippet,
            'diagram_url': self.diagram_url,
            'expected_keywords': self.expected_keywords,
            'time_estimate_seconds': self.time_estimate_seconds,
            'points': self.points,
            'metadata': self.metadata
        }


class QuestionBank:
    """Repository of question templates."""
    
    def __init__(self):
        """Initialize question bank."""
        self.templates: Dict[str, List[QuestionTemplate]] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default question templates."""
        # Computer Science templates
        self._add_template(QuestionTemplate(
            id="cs_ds_arrays_001",
            topic="Data Structures",
            subtopic="Arrays",
            difficulty=QuestionDifficulty.EASY,
            question_type=QuestionType.DEFINITION,
            template_text="What is an array in programming?",
            answer_template="An array is a data structure that stores a collection of elements of the same type in contiguous memory locations, accessed by an index.",
            explanation_template="Arrays provide O(1) access time when the index is known, making them efficient for random access. However, insertion and deletion operations can be costly as they may require shifting elements.",
            hints=["Think about a list of items", "Each item has a position number"],
            tags=["arrays", "data-structures"]
        ))
        
        self._add_template(QuestionTemplate(
            id="cs_ds_linkedlist_001",
            topic="Data Structures",
            subtopic="Linked Lists",
            difficulty=QuestionDifficulty.MEDIUM,
            question_type=QuestionType.COMPARISON,
            template_text="Compare and contrast arrays and linked lists.",
            answer_template="Arrays provide O(1) random access but O(n) insertion/deletion, while linked lists provide O(1) insertion/deletion at known positions but O(n) access. Arrays have better cache locality but fixed size, while linked lists can grow dynamically.",
            explanation_template="The choice between arrays and linked lists depends on the specific use case. Arrays are better for frequent access, while linked lists are better for frequent insertions/deletions.",
            hints=["Think about memory layout", "Consider access patterns", "Consider insertion/deletion operations"],
            tags=["arrays", "linked-lists", "comparison"]
        ))
        
        self._add_template(QuestionTemplate(
            id="cs_algo_sorting_001",
            topic="Algorithms",
            subtopic="Sorting",
            difficulty=QuestionDifficulty.HARD,
            question_type=QuestionType.CODE_WRITING,
            template_text="Implement quicksort algorithm in your preferred programming language.",
            answer_template="def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)",
            explanation_template="Quicksort uses divide-and-conquer strategy, selecting a pivot and partitioning the array around it.",
            hints=["Choose a pivot element", "Partition the array", "Recursively sort subarrays"],
            expected_keywords=["pivot", "partition", "recursive", "divide and conquer"],
            tags=["sorting", "algorithms", "quicksort"]
        ))
        
        # Database templates
        self._add_template(QuestionTemplate(
            id="db_sql_001",
            topic="Databases",
            subtopic="SQL",
            difficulty=QuestionDifficulty.EASY,
            question_type=QuestionType.CODE_WRITING,
            template_text="Write a SQL query to select all employees with salary greater than 50000 from an 'employees' table.",
            answer_template="SELECT * FROM employees WHERE salary > 50000;",
            explanation_template="The WHERE clause filters records based on a condition.",
            hints=["Use SELECT", "Specify the table", "Add a condition"],
            tags=["sql", "databases", "query"]
        ))
        
        # Operating Systems templates
        self._add_template(QuestionTemplate(
            id="os_process_001",
            topic="Operating Systems",
            subtopic="Process Management",
            difficulty=QuestionDifficulty.MEDIUM,
            question_type=QuestionType.CONCEPT_EXPLANATION,
            template_text="Explain the concept of process scheduling in operating systems.",
            answer_template="Process scheduling is the activity of the process manager that handles the removal of the running process from the CPU and selection of another process based on a particular strategy. Common scheduling algorithms include FCFS, SJF, Round Robin, and Priority Scheduling.",
            explanation_template="Scheduling is crucial for multitasking and fair resource allocation.",
            hints=["Think about CPU allocation", "Consider different algorithms", "Think about fairness vs efficiency"],
            tags=["os", "processes", "scheduling"]
        ))
        
        # Networking templates
        self._add_template(QuestionTemplate(
            id="net_osi_001",
            topic="Computer Networks",
            subtopic="OSI Model",
            difficulty=QuestionDifficulty.MEDIUM,
            question_type=QuestionType.SHORT_ANSWER,
            template_text="List the 7 layers of the OSI model from bottom to top.",
            answer_template="1. Physical\n2. Data Link\n3. Network\n4. Transport\n5. Session\n6. Presentation\n7. Application",
            explanation_template="The OSI model is a conceptual framework for understanding network communication.",
            hints=["Physical layer is at the bottom", "Application layer is at the top", "Remember: Please Do Not Throw Sausage Pizza Away"],
            tags=["networking", "osi", "protocols"]
        ))
    
    def _add_template(self, template: QuestionTemplate):
        """Add a template to the bank."""
        if template.topic not in self.templates:
            self.templates[template.topic] = []
        self.templates[template.topic].append(template)
    
    def get_templates(
        self,
        topic: str,
        difficulty: Optional[QuestionDifficulty] = None,
        question_type: Optional[QuestionType] = None,
        subtopic: Optional[str] = None,
        limit: int = 10
    ) -> List[QuestionTemplate]:
        """Get templates matching criteria."""
        if topic not in self.templates:
            return []
        
        templates = self.templates[topic]
        
        if difficulty:
            templates = [t for t in templates if t.difficulty == difficulty]
        
        if question_type:
            templates = [t for t in templates if t.question_type == question_type]
        
        if subtopic:
            templates = [t for t in templates if t.subtopic == subtopic]
        
        # Sort by usage count (prefer less used templates)
        templates.sort(key=lambda t: t.usage_count)
        
        return templates[:limit]
    
    def update_template_stats(
        self,
        template_id: str,
        success: bool,
        response_time: float
    ):
        """Update template statistics based on usage."""
        for templates in self.templates.values():
            for template in templates:
                if template.id == template_id:
                    template.usage_count += 1
                    # Update success rate (moving average)
                    current = template.success_rate
                    template.success_rate = (current * (template.usage_count - 1) + (100 if success else 0)) / template.usage_count
                    # Update average response time
                    template.avg_response_time = (template.avg_response_time * (template.usage_count - 1) + response_time) / template.usage_count
                    return


class AdaptationStrategy(Enum):
    """Strategies for adapting questions."""
    MAINTAIN = "maintain"  # Keep current difficulty
    INCREASE_DIFFICULTY = "increase"  # Make harder
    DECREASE_DIFFICULTY = "decrease"  # Make easier
    CHANGE_TOPIC = "change_topic"  # Switch topic
    ADD_HINTS = "add_hints"  # Provide more hints
    SIMPLIFY = "simplify"  # Simplify the question
    ENCOURAGE = "encourage"  # Provide encouragement
    CHALLENGE = "challenge"  # Provide challenge


class QuestionPromptTemplates:
    """Prompt templates for generating viva questions from text."""
    
    VIVA_GENERATION = """You are an expert examiner conducting a viva voce (oral exam). 
Based on the following educational material, generate {num_questions} high-quality viva questions.

Material:
{text}

Requirements for each question:
1. Question: Clear, provocative, and tests deep understanding rather than just recall.
2. Expected Answer: A comprehensive answer that a top-performing student would provide.
3. Explanation: Why this concept is important and any nuances.
4. Keywords: List 3-5 essential technical keywords that MUST be in the answer.
5. Difficulty: Level from [very_easy, easy, medium, hard, very_hard, expert].
6. Type: One of [concept_explanation, problem_solving, definition, comparison, diagram].

Format your response as a JSON array of objects with these keys:
- question_text (string)
- answer (string)
- explanation (string)
- expected_keywords (array of strings)
- difficulty (string)
- question_type (string)

Ensure the questions are suitable for an oral examination setting.
"""


class AdaptiveQuestioner:
    """
    Generates and adapts questions based on student performance and emotional state.
    """
    
    def __init__(
        self, 
        question_bank: Optional[QuestionBank] = None,
        ollama_url: str = "http://localhost:11434",
        model: str = "llama3"
    ):
        """
        Initialize adaptive questioner.
        
        Args:
            question_bank: Question bank instance
            ollama_url: URL for Ollama API
            model: Model to use for dynamic generation
        """
        self.question_bank = question_bank or QuestionBank()
        self.ollama_url = ollama_url.rstrip('/')
        self.model = model
        self._session: Optional[aiohttp.ClientSession] = None
        
        self.difficulty_weights = self._init_difficulty_weights()
        self.emotional_adaptations = self._init_emotional_adaptations()
        
        logger.info(f"AdaptiveQuestioner initialized with model: {model}")

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),
                headers={"Content-Type": "application/json"}
            )
        return self._session

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def _call_ollama(self, prompt: str) -> str:
        session = await self._get_session()
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7}
        }
        async with session.post(f"{self.ollama_url}/api/generate", json=payload) as response:
            if response.status != 200:
                raise Exception(f"Ollama error: {response.status}")
            result = await response.json()
            return result.get('response', '')

    async def generate_from_text(
        self,
        text: str,
        topic: str,
        num_questions: int = 5,
        target_difficulty: Optional[QuestionDifficulty] = None
    ) -> List[Question]:
        """
        Dynamically generate questions from text content using LLM.
        
        Args:
            text: Source text to generate questions from
            topic: Topic name for categorization
            num_questions: Number of questions to generate
            target_difficulty: Optional specific difficulty to target
            
        Returns:
            List of generated Question objects
        """
        logger.info(f"Generating {num_questions} dynamic questions for topic: {topic}")
        
        prompt = QuestionPromptTemplates.VIVA_GENERATION.format(
            num_questions=num_questions,
            text=text[:4000] # Limit context
        )
        
        try:
            response_text = await self._call_ollama(prompt)
            # Find JSON array in response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                logger.error("No JSON found in Ollama response")
                return []
                
            questions_data = json.loads(json_match.group())
            generated_questions = []
            
            for q_data in questions_data:
                try:
                    # Map strings to enums
                    diff_str = q_data.get('difficulty', 'medium').lower()
                    type_str = q_data.get('question_type', 'concept_explanation').lower()
                    
                    # Safe enum mapping
                    try:
                        diff = QuestionDifficulty(diff_str)
                    except ValueError:
                        diff = QuestionDifficulty.MEDIUM
                        
                    try:
                        q_type = QuestionType(type_str)
                    except ValueError:
                        q_type = QuestionType.CONCEPT_EXPLANATION

                    question = Question(
                        id=f"dyn_{hashlib.md5(q_data['question_text'].encode()).hexdigest()[:8]}",
                        topic=topic,
                        subtopic=q_data.get('subtopic'),
                        difficulty=diff,
                        question_type=q_type,
                        question_text=q_data['question_text'],
                        answer=q_data['answer'],
                        explanation=q_data['explanation'],
                        expected_keywords=q_data.get('expected_keywords', []),
                        metadata={'source': 'dynamic_generation', 'timestamp': datetime.now().isoformat()}
                    )
                    generated_questions.append(question)
                    
                    # Also add to question bank for future use
                    self.question_bank._add_template(QuestionTemplate(
                        id=f"temp_{question.id}",
                        topic=topic,
                        subtopic=question.subtopic,
                        difficulty=question.difficulty,
                        question_type=question.question_type,
                        template_text=question.question_text,
                        answer_template=question.answer,
                        explanation_template=question.explanation,
                        tags=[topic] + question.expected_keywords
                    ))
                    
                except Exception as e:
                    logger.warning(f"Failed to parse individual question data: {e}")
                    continue
            
            return generated_questions
            
        except Exception as e:
            logger.error(f"Error in dynamic question generation: {e}")
            return []
    
    def _init_difficulty_weights(self) -> Dict[QuestionDifficulty, float]:
        """Initialize difficulty transition weights."""
        return {
            QuestionDifficulty.VERY_EASY: 1.0,
            QuestionDifficulty.EASY: 1.2,
            QuestionDifficulty.MEDIUM: 1.5,
            QuestionDifficulty.HARD: 2.0,
            QuestionDifficulty.VERY_HARD: 2.5,
            QuestionDifficulty.EXPERT: 3.0
        }
    
    def _init_emotional_adaptations(self) -> Dict[EmotionalState, AdaptationStrategy]:
        """Initialize emotional state to adaptation strategy mapping."""
        return {
            EmotionalState.CONFIDENT: AdaptationStrategy.INCREASE_DIFFICULTY,
            EmotionalState.HESITANT: AdaptationStrategy.MAINTAIN,
            EmotionalState.FRUSTRATED: AdaptationStrategy.DECREASE_DIFFICULTY,
            EmotionalState.ANXIOUS: AdaptationStrategy.SIMPLIFY,
            EmotionalState.BORED: AdaptationStrategy.INCREASE_DIFFICULTY,
            EmotionalState.ENGAGED: AdaptationStrategy.MAINTAIN,
            EmotionalState.CONFUSED: AdaptationStrategy.ADD_HINTS,
            EmotionalState.STRESSED: AdaptationStrategy.ENCOURAGE,
            EmotionalState.NEUTRAL: AdaptationStrategy.MAINTAIN
        }
    
    async def generate_question(
        self,
        topic: str,
        difficulty: QuestionDifficulty,
        context: Dict[str, Any],
        exclude_ids: Optional[List[str]] = None
    ) -> Optional[Question]:
        """
        Generate a question based on context.
        
        Args:
            topic: Topic for the question
            difficulty: Desired difficulty
            context: Context information
            exclude_ids: Question IDs to exclude
            
        Returns:
            Generated question or None
        """
        # Get templates for this topic and difficulty
        templates = self.question_bank.get_templates(
            topic=topic,
            difficulty=difficulty,
            limit=5
        )
        
        if not templates:
            logger.warning(f"No templates found for topic {topic} at difficulty {difficulty.value}")
            return None
        
        # Select template based on performance history
        selected = self._select_template(templates, context)
        
        if not selected:
            selected = random.choice(templates)
        
        # Generate question
        question = selected.generate_question(context)
        
        # Apply adaptations based on emotional state
        if 'emotional_state' in context:
            question = await self._adapt_to_emotion(question, context['emotional_state'])
        
        logger.debug(f"Generated question {question.id} for topic {topic}")
        return question
    
    def _select_template(
        self,
        templates: List[QuestionTemplate],
        context: Dict[str, Any]
    ) -> Optional[QuestionTemplate]:
        """
        Select the best template based on context.
        
        Args:
            templates: Available templates
            context: Context information
            
        Returns:
            Selected template or None
        """
        if not templates:
            return None
        
        # Score each template
        scores = []
        for template in templates:
            score = 1.0
            
            # Prefer templates with higher success rate
            if template.success_rate > 0:
                score *= (template.success_rate / 100)
            
            # Prefer less used templates
            if template.usage_count > 0:
                score *= (1.0 / (template.usage_count + 1))
            
            # Boost score if template tags match recent weaknesses
            if 'weak_topics' in context:
                weak_topics = context.get('weak_topics', [])
                if any(tag in weak_topics for tag in template.tags):
                    score *= 1.5
            
            scores.append(score)
        
        # Normalize scores
        total = sum(scores)
        if total == 0:
            return random.choice(templates)
        
        probabilities = [s / total for s in scores]
        
        # Select based on probabilities
        return np.random.choice(templates, p=probabilities)
    
    async def _adapt_to_emotion(
        self,
        question: Question,
        emotional_state: Dict[str, Any]
    ) -> Question:
        """
        Adapt question based on emotional state.
        
        Args:
            question: Original question
            emotional_state: Detected emotional state
            
        Returns:
            Adapted question
        """
        primary = emotional_state.get('primary_emotion', 'neutral')
        intensity = emotional_state.get('intensity', 0.5)
        
        try:
            emotion = EmotionalState(primary)
            strategy = self.emotional_adaptations.get(emotion, AdaptationStrategy.MAINTAIN)
            
            if strategy == AdaptationStrategy.INCREASE_DIFFICULTY and intensity > 0.7:
                # Challenge the confident student
                question.hints = []  # Remove hints for challenge
                question.explanation = "Challenge yourself with this question!"
                
            elif strategy == AdaptationStrategy.DECREASE_DIFFICULTY:
                # Simplify for frustrated student
                if intensity > 0.5:
                    # Add more hints
                    question.hints.extend([
                        "Take your time with this",
                        "Break it down step by step",
                        "You've got this!"
                    ])
                    
            elif strategy == AdaptationStrategy.ADD_HINTS:
                # Add hints for confused student
                question.hints.extend([
                    "Let's think about this carefully",
                    "What do we know about this topic?",
                    "Try to recall similar problems"
                ])
                
            elif strategy == AdaptationStrategy.ENCOURAGE:
                # Add encouragement for stressed student
                question.question_text = "Let's try this: " + question.question_text
                question.hints.append("Remember, it's okay to take your time")
                
        except ValueError:
            # Unknown emotion, ignore
            pass
        
        return question
    
    async def evaluate_answer(
        self,
        question: Question,
        answer_text: str,
        expected_answer: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a student's answer.
        
        Args:
            question: The question being answered
            answer_text: Student's answer
            expected_answer: Expected correct answer
            context: Evaluation context
            
        Returns:
            Evaluation results
        """
        # Simple evaluation based on keyword matching
        # In production, use NLP or more sophisticated methods
        
        answer_lower = answer_text.lower()
        expected_lower = expected_answer.lower()
        
        # Extract keywords from expected answer
        keywords = question.expected_keywords
        if not keywords:
            # Simple keyword extraction
            words = re.findall(r'\b\w+\b', expected_lower)
            keywords = [w for w in words if len(w) > 3][:5]  # Take longer words
        
        # Check for keywords
        found_keywords = []
        missing_keywords = []
        
        for keyword in keywords:
            if keyword.lower() in answer_lower:
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        # Calculate score based on keywords
        if keywords:
            score = (len(found_keywords) / len(keywords)) * 100
        else:
            # Fallback to simple similarity
            score = self._calculate_similarity(answer_lower, expected_lower)
        
        # Determine evaluation
        if score >= 80:
            evaluation = AnswerEvaluation.CORRECT
        elif score >= 50:
            evaluation = AnswerEvaluation.PARTIALLY_CORRECT
        else:
            evaluation = AnswerEvaluation.INCORRECT
        
        # Generate feedback
        feedback = {
            'evaluation': evaluation,
            'score': score,
            'found_keywords': found_keywords,
            'missing_keywords': missing_keywords,
            'explanation': self._generate_explanation(question, evaluation, score),
            'strengths': self._identify_strengths(found_keywords, question),
            'weaknesses': self._identify_weaknesses(missing_keywords, question),
            'suggested_review': self._suggest_review(missing_keywords, question),
            'hints': question.hints if score < 70 else None,
            'resources': question.resources
        }
        
        # Update template statistics
        if question.metadata and 'template_id' in question.metadata:
            self.question_bank.update_template_stats(
                template_id=question.metadata['template_id'],
                success=(score >= 70),
                response_time=context.get('time_taken', 0)
            )
        
        return feedback
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity."""
        # Simple word overlap similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return (len(intersection) / len(union)) * 100
    
    def _generate_explanation(
        self,
        question: Question,
        evaluation: AnswerEvaluation,
        score: float
    ) -> str:
        """Generate explanation for the evaluation."""
        if evaluation == AnswerEvaluation.CORRECT:
            return f"Excellent! Your answer correctly addresses the key points. {question.explanation}"
        elif evaluation == AnswerEvaluation.PARTIALLY_CORRECT:
            return f"Good attempt! You're on the right track but missing some key points. {question.explanation}"
        else:
            return f"Let's review this concept. {question.explanation}"
    
    def _identify_strengths(
        self,
        found_keywords: List[str],
        question: Question
    ) -> List[str]:
        """Identify strengths based on answer."""
        strengths = []
        
        if found_keywords:
            strengths.append(f"Correctly identified: {', '.join(found_keywords[:3])}")
        
        return strengths
    
    def _identify_weaknesses(
        self,
        missing_keywords: List[str],
        question: Question
    ) -> List[str]:
        """Identify weaknesses based on answer."""
        weaknesses = []
        
        if missing_keywords:
            weaknesses.append(f"Missing concepts: {', '.join(missing_keywords[:3])}")
        
        return weaknesses
    
    def _suggest_review(
        self,
        missing_keywords: List[str],
        question: Question
    ) -> Optional[str]:
        """Suggest topics to review based on missing keywords."""
        if not missing_keywords:
            return None
        
        return f"Review concepts related to: {', '.join(missing_keywords[:3])}"
    
    def get_difficulty_adjustment(
        self,
        current_difficulty: QuestionDifficulty,
        performance_history: List[float],
        emotional_state: Optional[EmotionalState] = None
    ) -> QuestionDifficulty:
        """
        Get adjusted difficulty based on performance and emotion.
        
        Args:
            current_difficulty: Current difficulty level
            performance_history: Recent performance scores
            emotional_state: Current emotional state
            
        Returns:
            Adjusted difficulty
        """
        if not performance_history:
            return current_difficulty
        
        # Calculate recent average performance
        recent_avg = np.mean(performance_history[-3:]) if len(performance_history) >= 3 else np.mean(performance_history)
        
        difficulty_levels = list(QuestionDifficulty)
        current_idx = difficulty_levels.index(current_difficulty)
        
        # Adjust based on performance
        if recent_avg >= 85:
            # Excellent performance, increase difficulty
            new_idx = min(current_idx + 1, len(difficulty_levels) - 1)
        elif recent_avg <= 50:
            # Poor performance, decrease difficulty
            new_idx = max(current_idx - 1, 0)
        else:
            new_idx = current_idx
        
        # Adjust based on emotional state
        if emotional_state:
            if emotional_state in [EmotionalState.CONFIDENT, EmotionalState.ENGAGED]:
                # Can handle challenge
                new_idx = min(new_idx + 1, len(difficulty_levels) - 1)
            elif emotional_state in [EmotionalState.FRUSTRATED, EmotionalState.STRESSED]:
                # Needs easier questions
                new_idx = max(new_idx - 1, 0)
        
        return difficulty_levels[new_idx]
    
    async def generate_follow_up(
        self,
        previous_question: Question,
        answer_evaluation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Question]:
        """
        Generate a follow-up question based on previous answer.
        
        Args:
            previous_question: Previous question
            answer_evaluation: Evaluation of previous answer
            context: Context information
            
        Returns:
            Follow-up question or None
        """
        # Determine if follow-up is needed
        score = answer_evaluation.get('score', 0)
        
        if score >= 80:
            # Student did well, maybe ask a harder follow-up
            difficulty = self.get_difficulty_adjustment(
                previous_question.difficulty,
                [score],
                context.get('emotional_state')
            )
            
            return await self.generate_question(
                topic=previous_question.topic,
                difficulty=difficulty,
                context={**context, 'follow_up': True}
            )
            
        elif score >= 50:
            # Partially correct, ask a similar but simpler question
            difficulty = QuestionDifficulty(
                max(
                    list(QuestionDifficulty).index(QuestionDifficulty.EASY),
                    list(QuestionDifficulty).index(previous_question.difficulty) - 1
                )
            )
            
            return await self.generate_question(
                topic=previous_question.topic,
                difficulty=difficulty,
                context={**context, 'reinforcement': True}
            )
        
        # Poor performance, no follow-up, suggest review
        return None
    
    async def get_hint(
        self,
        question: Question,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get a hint for the current question.
        
        Args:
            question: Current question
            context: Context information
            
        Returns:
            Hint string or None
        """
        if not question.hints:
            return None
        
        # Select hint based on context
        hint_index = min(len(question.hints) - 1, context.get('hint_level', 0))
        
        return question.hints[hint_index]