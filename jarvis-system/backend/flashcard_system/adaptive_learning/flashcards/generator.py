"""
Flashcard generator module that uses AI to create high-quality flashcards from text content.
Integrates with Ollama for local LLM-based generation with multiple strategies.
"""

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Set, Union
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import threading

import aiohttp
import numpy as np
from pydantic import BaseModel, Field, field_validator
import tiktoken
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DifficultyLevel(Enum):
    """Difficulty levels for flashcards."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class GenerationQuality(Enum):
    """Quality assessment for generated flashcards."""
    EXCELLENT = "excellent"
    GOOD = "good" 
    FAIR = "fair"
    POOR = "poor"
    FAILED = "failed"


class CardType(Enum):
    """Types of flashcards that can be generated."""
    BASIC = "basic"  # Front/Back
    CLOZE = "cloze"  # Fill in the blank
    REVERSE = "reverse"  # Bidirectional
    MULTIPLE_CHOICE = "multiple_choice"
    DEFINITION = "definition"
    CONCEPT = "concept"
    CODE_SNIPPET = "code_snippet"
    FORMULA = "formula"


@dataclass
class GenerationOptions:
    """Options for flashcard generation."""
    max_cards_per_chunk: int = 10
    min_confidence: float = 0.7
    include_examples: bool = True
    include_definitions: bool = True
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    card_types: List[CardType] = field(default_factory=lambda: [CardType.BASIC, CardType.CLOZE])
    language: str = "en"
    max_tokens_per_card: int = 200
    temperature: float = 0.7
    model: str = "llama2"  # Ollama model
    timeout_seconds: int = 30
    retry_attempts: int = 3
    enable_validation: bool = True
    extract_key_concepts: bool = True
    generate_hints: bool = False
    contextualize: bool = True
    
    @field_validator('max_cards_per_chunk')
    def validate_card_count(cls, v):
        if v < 1 or v > 50:
            raise ValueError("max_cards_per_chunk must be between 1 and 50")
        return v
    
    @field_validator('min_confidence')
    def validate_confidence(cls, v):
        if v < 0 or v > 1:
            raise ValueError("min_confidence must be between 0 and 1")
        return v


class Flashcard(BaseModel):
    """Represents a single flashcard with metadata."""
    id: str = Field(default_factory=lambda: hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:16])
    front: str
    back: str
    hints: Optional[str] = None
    source_text: Optional[str] = None
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    card_type: CardType = CardType.BASIC
    tags: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    quality_score: GenerationQuality = GenerationQuality.GOOD
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    source_page: Optional[int] = None
    source_paragraph: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    @field_validator('confidence')
    def validate_confidence(cls, v):
        if v < 0 or v > 1:
            raise ValueError("confidence must be between 0 and 1")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            DifficultyLevel: lambda v: v.value,
            CardType: lambda v: v.value,
            GenerationQuality: lambda v: v.value
        }
    
    def dict(self, *args, **kwargs):
        """Override dict to handle enum serialization."""
        d = super().dict(*args, **kwargs)
        d['difficulty'] = self.difficulty.value
        d['card_type'] = self.card_type.value
        d['quality_score'] = self.quality_score.value
        d['created_at'] = self.created_at.isoformat()
        d['updated_at'] = self.updated_at.isoformat()
        return d


class FlashcardSet(BaseModel):
    """A set of flashcards with metadata."""
    id: str = Field(default_factory=lambda: hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:16])
    name: str
    description: Optional[str] = None
    source_document: Optional[str] = None
    source_document_hash: Optional[str] = None
    flashcards: List[Flashcard] = Field(default_factory=list)
    total_pages: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    generation_options: Optional[GenerationOptions] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_flashcard(self, flashcard: Flashcard):
        """Add a flashcard to the set."""
        self.flashcards.append(flashcard)
        self.updated_at = datetime.now()
    
    def remove_flashcard(self, flashcard_id: str) -> bool:
        """Remove a flashcard by ID."""
        initial_len = len(self.flashcards)
        self.flashcards = [f for f in self.flashcards if f.id != flashcard_id]
        self.updated_at = datetime.now()
        return len(self.flashcards) < initial_len
    
    def get_by_topic(self, topic: str) -> List[Flashcard]:
        """Get flashcards by topic."""
        return [f for f in self.flashcards if f.topic == topic]
    
    def get_by_difficulty(self, difficulty: DifficultyLevel) -> List[Flashcard]:
        """Get flashcards by difficulty level."""
        return [f for f in self.flashcards if f.difficulty == difficulty]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the flashcard set."""
        if not self.flashcards:
            return {"total": 0}
        
        difficulties = {}
        types = {}
        confidences = []
        
        for card in self.flashcards:
            diff = card.difficulty.value
            difficulties[diff] = difficulties.get(diff, 0) + 1
            
            ctype = card.card_type.value
            types[ctype] = types.get(ctype, 0) + 1
            
            confidences.append(card.confidence)
        
        return {
            "total": len(self.flashcards),
            "difficulties": difficulties,
            "types": types,
            "avg_confidence": np.mean(confidences) if confidences else 0,
            "min_confidence": min(confidences) if confidences else 0,
            "max_confidence": max(confidences) if confidences else 0,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class TextProcessor:
    """Handles text preprocessing and chunking for flashcard generation."""
    
    def __init__(self, max_chunk_size: int = 2000, overlap: int = 200):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.encoder = tiktoken.get_encoding("cl100k_base")
        
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks for processing.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks with metadata
        """
        # Clean text
        text = self._clean_text(text)
        
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        
        for para in paragraphs:
            para_tokens = len(self.encoder.encode(para))
            
            if current_size + para_tokens > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'index': chunk_index,
                    'tokens': current_size,
                    'paragraphs': len(current_chunk),
                    'start_idx': chunk_index * self.max_chunk_size
                })
                chunk_index += 1
                
                # Keep overlap
                overlap_paras = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk
                current_chunk = overlap_paras
                current_size = sum(len(self.encoder.encode(p)) for p in current_chunk)
            
            current_chunk.append(para)
            current_size += para_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'index': chunk_index,
                'tokens': current_size,
                'paragraphs': len(current_chunk)
            })
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def extract_key_concepts(self, text: str) -> List[str]:
        """
        Extract key concepts from text using NLP techniques.
        
        Args:
            text: Input text
            
        Returns:
            List of key concepts
        """
        # Simple extraction based on capitalization and frequency
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Count frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Filter and sort
        concepts = [w for w, f in word_freq.items() if f >= 2 and len(w.split()) <= 3]
        concepts = list(set(concepts))  # Remove duplicates
        
        return concepts[:20]  # Return top 20
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        text = re.sub(r'[|]', 'I', text)
        text = re.sub(r'[0O]', '0', text)
        
        # Remove special characters but keep sentence structure
        text = re.sub(r'[^\w\s.,;:!?-]', '', text)
        
        return text.strip()


class PromptTemplates:
    """Collection of prompt templates for flashcard generation."""
    
    BASIC_CARD = """You are an expert educator creating high-quality flashcards. Based on the following text, create {num_cards} flashcards that capture the most important concepts.

Text: {text}

Requirements:
- Create {card_types} type flashcards
- Difficulty level: {difficulty}
- Include {include_examples} examples
- Include {include_definitions} definitions
- Language: {language}

Each flashcard must have:
1. Front: Clear, concise question or prompt
2. Back: Comprehensive but focused answer
3. Hints: Optional helpful clues
4. Topic: Main subject area
5. Subtopic: Specific area within topic
6. Confidence: Rate your confidence (0.0-1.0)

Format your response as a JSON array with objects containing:
- front: string
- back: string 
- hints: string (optional)
- topic: string
- subtopic: string
- confidence: float (0.0-1.0)

Ensure:
- Questions are specific and unambiguous
- Answers are accurate and complete
- Concepts are properly explained
- Difficulty matches the specified level
"""

    CLOZE_CARD = """Create {num_cards} cloze deletion (fill-in-the-blank) flashcards from this text:

Text: {text}

Requirements:
- Each card should test key terminology or concepts
- Use {{c1::text}} notation for cloze deletions
- Include context around the blank
- Difficulty level: {difficulty}

Format as JSON array with:
- front: string with {{c1::}} notation
- back: string explaining the answer
- hints: optional context clues
- topic: string
- subtopic: string
"""

    CODE_CARD = """Create programming flashcards from this code or technical text:

Text: {text}

Create flashcards testing:
- Code syntax and structure
- Function purposes
- Algorithm understanding
- Best practices

Format as JSON array with:
- front: string (question/prompt)
- back: string (answer with code if relevant)
- code_snippet: string (optional)
- language: string (programming language)
- topic: string
- confidence: float
"""


class FlashcardGenerator:
    """
    Main flashcard generator class that interfaces with Ollama for AI-powered generation.
    """
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "llama2",
        data_dir: Optional[Path] = None,
        max_workers: int = 4
    ):
        """
        Initialize the flashcard generator.
        
        Args:
            ollama_url: URL for Ollama API
            model: Default model to use
            data_dir: Directory for storing generated flashcards
            max_workers: Maximum number of concurrent workers
        """
        self.ollama_url = ollama_url.rstrip('/')
        self.default_model = model
        self.data_dir = data_dir or Path.home() / '.jarvis' / 'flashcards'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.text_processor = TextProcessor()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = threading.Lock()
        
        # Cache for generated cards
        self._cache: Dict[str, List[Flashcard]] = {}
        
        logger.info(f"FlashcardGenerator initialized with model: {model}, data_dir: {self.data_dir}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),
                headers={"Content-Type": "application/json"}
            )
        return self._session
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._get_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session and not self._session.closed:
            await self._session.close()
        self.executor.shutdown(wait=False)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _call_ollama(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[GenerationOptions] = None
    ) -> Dict[str, Any]:
        """
        Call Ollama API with retry logic.
        
        Args:
            prompt: Prompt to send
            model: Model to use (overrides default)
            options: Generation options
            
        Returns:
            Ollama API response
        """
        session = await self._get_session()
        model_name = model or self.default_model
        
        # Prepare request payload
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": options.temperature if options else 0.7,
                "num_predict": 2048
            }
        }
        
        # Add timeout
        timeout = options.timeout_seconds if options else 30
        
        try:
            async with asyncio.timeout(timeout):
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise aiohttp.ClientError(f"Ollama API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    
                    if 'response' not in result:
                        raise ValueError("Invalid response from Ollama")
                    
                    return result
                    
        except asyncio.TimeoutError:
            logger.error(f"Ollama request timed out after {timeout}s")
            raise
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            raise
    
    def _parse_json_response(self, response: str) -> List[Dict]:
        """
        Parse JSON from Ollama response, handling various formats.
        
        Args:
            response: Raw response string
            
        Returns:
            Parsed JSON data
        """
        # Try to extract JSON from response
        json_pattern = r'\[[\s\S]*\]|\{[\s\S]*\}'
        matches = re.findall(json_pattern, response)
        
        for match in matches:
            try:
                # Clean up the JSON string
                cleaned = match.strip()
                # Remove markdown code blocks if present
                cleaned = re.sub(r'^```json\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)
                
                data = json.loads(cleaned)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return [data]
            except json.JSONDecodeError:
                continue
        
        # If no JSON found, try to parse line by line
        cards = []
        lines = response.strip().split('\n')
        current_card = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key in ['front', 'back', 'hints', 'topic', 'subtopic']:
                    current_card[key] = value
                elif key == 'confidence':
                    try:
                        current_card['confidence'] = float(value)
                    except ValueError:
                        current_card['confidence'] = 0.7
                
                # If we have at least front and back, save the card
                if 'front' in current_card and 'back' in current_card:
                    if 'confidence' not in current_card:
                        current_card['confidence'] = 0.7
                    cards.append(current_card)
                    current_card = {}
        
        return cards
    
    def _validate_flashcard(self, card_data: Dict, options: GenerationOptions) -> Optional[Flashcard]:
        """
        Validate and clean flashcard data.
        
        Args:
            card_data: Raw card data
            options: Generation options
            
        Returns:
            Validated Flashcard or None if invalid
        """
        try:
            # Ensure required fields
            if 'front' not in card_data or 'back' not in card_data:
                return None
            
            front = str(card_data['front']).strip()
            back = str(card_data['back']).strip()
            
            # Validate length
            if len(front) < 5 or len(back) < 5:
                return None
            
            if len(front) > 500 or len(back) > 1000:
                return None
            
            # Check confidence
            confidence = float(card_data.get('confidence', 0.7))
            if confidence < options.min_confidence:
                return None
            
            # Determine quality score
            if confidence >= 0.9:
                quality = GenerationQuality.EXCELLENT
            elif confidence >= 0.8:
                quality = GenerationQuality.GOOD
            elif confidence >= 0.7:
                quality = GenerationQuality.FAIR
            else:
                quality = GenerationQuality.POOR
            
            # Create flashcard
            return Flashcard(
                front=front,
                back=back,
                hints=card_data.get('hints'),
                topic=card_data.get('topic', 'general'),
                subtopic=card_data.get('subtopic'),
                difficulty=options.difficulty,
                card_type=CardType.BASIC,  # Default, can be enhanced
                tags=[options.difficulty.value],
                confidence=confidence,
                quality_score=quality,
                metadata={
                    'generation_model': options.model,
                    'generation_temperature': options.temperature
                }
            )
            
        except Exception as e:
            logger.debug(f"Card validation failed: {e}")
            return None
    
    async def generate_from_text(
        self,
        text: str,
        set_name: str,
        options: Optional[GenerationOptions] = None
    ) -> FlashcardSet:
        """
        Generate flashcards from text.
        
        Args:
            text: Source text
            set_name: Name for the flashcard set
            options: Generation options
            
        Returns:
            FlashcardSet containing generated cards
        """
        options = options or GenerationOptions()
        
        # Check cache
        cache_key = hashlib.sha256(f"{text[:100]}{set_name}".encode()).hexdigest()
        if cache_key in self._cache:
            logger.info(f"Returning cached flashcards for {set_name}")
            cards = self._cache[cache_key]
            return FlashcardSet(
                name=set_name,
                flashcards=cards,
                generation_options=options
            )
        
        # Preprocess text
        chunks = self.text_processor.chunk_text(text)
        
        # Extract key concepts if requested
        key_concepts = []
        if options.extract_key_concepts:
            key_concepts = self.text_processor.extract_key_concepts(text)
            logger.info(f"Extracted {len(key_concepts)} key concepts")
        
        # Generate cards from chunks
        all_cards = []
        tasks = []
        
        for i, chunk in enumerate(chunks):
            task = self._generate_from_chunk(chunk, options, i, len(chunks))
            tasks.append(task)
        
        # Gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Chunk generation failed: {result}")
                continue
            all_cards.extend(result)
        
        # Deduplicate cards
        all_cards = self._deduplicate_cards(all_cards)
        
        # Add key concepts as additional cards if needed
        if key_concepts and len(all_cards) < options.max_cards_per_chunk:
            concept_cards = await self._generate_concept_cards(key_concepts, options)
            all_cards.extend(concept_cards)
        
        # Create flashcard set
        flashcard_set = FlashcardSet(
            name=set_name,
            source_document=set_name,
            source_document_hash=hashlib.sha256(text.encode()).hexdigest(),
            flashcards=all_cards,
            generation_options=options,
            tags=[options.difficulty.value],
            metadata={
                'total_chunks': len(chunks),
                'key_concepts': key_concepts,
                'generation_time': datetime.now().isoformat()
            }
        )
        
        # Cache results
        self._cache[cache_key] = all_cards
        
        # Save to disk
        await self._save_flashcard_set(flashcard_set)
        
        logger.info(f"Generated {len(all_cards)} flashcards for {set_name}")
        return flashcard_set
    
    async def _generate_from_chunk(
        self,
        chunk: Dict,
        options: GenerationOptions,
        chunk_index: int,
        total_chunks: int
    ) -> List[Flashcard]:
        """
        Generate flashcards from a single text chunk.
        
        Args:
            chunk: Text chunk with metadata
            options: Generation options
            chunk_index: Index of current chunk
            total_chunks: Total number of chunks
            
        Returns:
            List of generated flashcards
        """
        # Select prompt template
        if CardType.CLOZE in options.card_types and chunk_index % 3 == 0:
            prompt_template = PromptTemplates.CLOZE_CARD
        elif CardType.CODE_SNIPPET in options.card_types and any(
            lang in chunk['text'].lower() for lang in ['python', 'java', 'c++', 'javascript']
        ):
            prompt_template = PromptTemplates.CODE_CARD
        else:
            prompt_template = PromptTemplates.BASIC_CARD
        
        # Format prompt
        card_types_str = ', '.join([ct.value for ct in options.card_types[:3]])
        prompt = prompt_template.format(
            num_cards=min(options.max_cards_per_chunk, 5),  # Limit per chunk
            text=chunk['text'][:2000],  # Limit text length
            card_types=card_types_str,
            difficulty=options.difficulty.value,
            include_examples='yes' if options.include_examples else 'no',
            include_definitions='yes' if options.include_definitions else 'no',
            language=options.language
        )
        
        try:
            # Call Ollama
            response = await self._call_ollama(prompt, options=options)
            
            # Parse response
            raw_cards = self._parse_json_response(response.get('response', ''))
            
            # Validate and create flashcards
            cards = []
            for raw_card in raw_cards:
                card = self._validate_flashcard(raw_card, options)
                if card:
                    # Add chunk metadata
                    card.source_text = chunk['text'][:500]  # Store preview
                    card.source_page = chunk.get('start_idx')
                    card.metadata['chunk_index'] = chunk_index
                    cards.append(card)
                    
                    if len(cards) >= options.max_cards_per_chunk:
                        break
            
            logger.info(f"Generated {len(cards)} cards from chunk {chunk_index + 1}/{total_chunks}")
            return cards
            
        except Exception as e:
            logger.error(f"Failed to generate from chunk {chunk_index}: {e}")
            return []
    
    async def _generate_concept_cards(
        self,
        concepts: List[str],
        options: GenerationOptions
    ) -> List[Flashcard]:
        """
        Generate definition cards for key concepts.
        
        Args:
            concepts: List of key concepts
            options: Generation options
            
        Returns:
            List of concept definition cards
        """
        cards = []
        
        for concept in concepts[:5]:  # Limit to 5 concept cards
            prompt = f"""Create a definition flashcard for the concept: "{concept}"

The flashcard should:
- Front: Clearly ask for the definition of {concept}
- Back: Provide a comprehensive but concise definition
- Include an example if relevant
- Confidence rating based on how well-defined this concept is

Format as JSON with: front, back, hints (optional), confidence
"""
            
            try:
                response = await self._call_ollama(prompt, options=options)
                raw_cards = self._parse_json_response(response.get('response', ''))
                
                for raw_card in raw_cards:
                    card = self._validate_flashcard(raw_card, options)
                    if card:
                        card.topic = "key_concepts"
                        card.card_type = CardType.DEFINITION
                        card.tags.append("definition")
                        cards.append(card)
                        
            except Exception as e:
                logger.error(f"Failed to generate concept card for {concept}: {e}")
                continue
        
        return cards
    
    def _deduplicate_cards(self, cards: List[Flashcard]) -> List[Flashcard]:
        """
        Remove duplicate or very similar flashcards.
        
        Args:
            cards: List of flashcards
            
        Returns:
            Deduplicated list
        """
        unique_cards = []
        seen_questions = set()
        
        for card in cards:
            # Create a normalized version of the question for comparison
            normalized = re.sub(r'\s+', ' ', card.front.lower().strip())
            normalized = re.sub(r'[^\w\s]', '', normalized)
            
            if normalized not in seen_questions:
                seen_questions.add(normalized)
                unique_cards.append(card)
        
        logger.info(f"Deduplicated {len(cards) - len(unique_cards)} cards")
        return unique_cards
    
    async def _save_flashcard_set(self, flashcard_set: FlashcardSet):
        """
        Save flashcard set to disk.
        
        Args:
            flashcard_set: FlashcardSet to save
        """
        try:
            file_path = self.data_dir / f"{flashcard_set.id}.json"
            
            with open(file_path, 'w') as f:
                json.dump(flashcard_set.model_dump(), f, indent=2)
            
            logger.info(f"Saved flashcard set to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save flashcard set: {e}")
    
    async def load_flashcard_set(self, set_id: str) -> Optional[FlashcardSet]:
        """
        Load flashcard set from disk.
        
        Args:
            set_id: ID of the flashcard set
            
        Returns:
            FlashcardSet if found, None otherwise
        """
        try:
            file_path = self.data_dir / f"{set_id}.json"
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert dictionaries back to objects
            flashcards = []
            for card_data in data.get('flashcards', []):
                card = Flashcard(**card_data)
                flashcards.append(card)
            
            data['flashcards'] = flashcards
            return FlashcardSet(**data)
            
        except Exception as e:
            logger.error(f"Failed to load flashcard set {set_id}: {e}")
            return None
    
    async def list_flashcard_sets(self) -> List[Dict[str, Any]]:
        """
        List all available flashcard sets.
        
        Returns:
            List of flashcard set metadata
        """
        sets = []
        
        try:
            for file_path in self.data_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    sets.append({
                        'id': data.get('id'),
                        'name': data.get('name'),
                        'card_count': len(data.get('flashcards', [])),
                        'created_at': data.get('created_at'),
                        'tags': data.get('tags', [])
                    })
                except Exception as e:
                    logger.error(f"Failed to read {file_path}: {e}")
                    continue
            
            # Sort by creation date
            sets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list flashcard sets: {e}")
        
        return sets
    
    async def generate_batch(
        self,
        texts: List[str],
        set_names: List[str],
        options: Optional[GenerationOptions] = None
    ) -> List[FlashcardSet]:
        """
        Generate flashcards from multiple texts in batch.
        
        Args:
            texts: List of source texts
            set_names: List of set names
            options: Generation options
            
        Returns:
            List of generated flashcard sets
        """
        if len(texts) != len(set_names):
            raise ValueError("Number of texts must match number of set names")
        
        tasks = []
        for text, name in zip(texts, set_names):
            task = self.generate_from_text(text, name, options)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_sets = []
        for result in results:
            if isinstance(result, FlashcardSet):
                valid_sets.append(result)
            else:
                logger.error(f"Batch generation failed: {result}")
        
        return valid_sets
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if Ollama is available and responsive.
        
        Returns:
            Health status information
        """
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.ollama_url}/api/tags") as response:
                if response.status == 200:
                    models = await response.json()
                    
                    # Check if default model is available
                    model_available = any(
                        m.get('name') == self.default_model
                        for m in models.get('models', [])
                    )
                    
                    return {
                        'status': 'healthy',
                        'ollama_url': self.ollama_url,
                        'default_model': self.default_model,
                        'model_available': model_available,
                        'available_models': [m.get('name') for m in models.get('models', [])]
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'error': f'Ollama returned status {response.status}'
                    }
                    
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'ollama_url': self.ollama_url
            }