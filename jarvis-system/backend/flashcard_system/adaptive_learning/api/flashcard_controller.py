"""
Flashcard API controller handling CRUD operations, generation, and review management.
Integrates with generator and spaced repetition modules.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from fastapi import (
    APIRouter, 
    HTTPException, 
    Depends, 
    Query, 
    Path as PathParam,
    BackgroundTasks,
    UploadFile,
    File,
    Form,
    WebSocket,
    WebSocketDisconnect
)
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from pydantic import BaseModel, Field, field_validator, HttpUrl
import aiofiles
import magic

from ..flashcards.generator import (
    FlashcardGenerator,
    Flashcard,
    FlashcardSet,
    GenerationOptions,
    DifficultyLevel,
    CardType
)
from ..flashcards.spaced_repetition import (
    SpacedRepetition,
    ReviewQuality,
    CardProgress,
    ReviewLog
)
from ..scanner import SubjectScanner, MaterialProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/flashcards", tags=["flashcards"])

# Global instances (would be properly injected in production)
_flashcard_generator: Optional[FlashcardGenerator] = None
_spaced_repetition: Optional[SpacedRepetition] = None


# Dependency injection
async def get_flashcard_generator() -> FlashcardGenerator:
    """Dependency to get flashcard generator instance."""
    global _flashcard_generator
    if _flashcard_generator is None:
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "data" / "flashcards"
        _flashcard_generator = FlashcardGenerator(data_dir=data_dir)
    return _flashcard_generator


async def get_spaced_repetition() -> SpacedRepetition:
    """Dependency to get spaced repetition instance."""
    global _spaced_repetition
    if _spaced_repetition is None:
        project_root = Path(__file__).parent.parent.parent
        db_path = project_root / "data" / "spaced_repetition.db"
        _spaced_repetition = SpacedRepetition(db_path=db_path)
    return _spaced_repetition


# Pydantic models for request/response

class DifficultyLevelEnum(str, Enum):
    """Difficulty levels for API."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class CardTypeEnum(str, Enum):
    """Card types for API."""
    BASIC = "basic"
    CLOZE = "cloze"
    REVERSE = "reverse"
    MULTIPLE_CHOICE = "multiple_choice"
    DEFINITION = "definition"
    CODE_SNIPPET = "code_snippet"


class CreateFlashcardSetRequest(BaseModel):
    """Request model for creating a flashcard set."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    source_document: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class CreateSubjectRequest(BaseModel):
    """Request model for creating a new subject folder."""
    name: str = Field(..., min_length=1, max_length=100)
    difficulty: DifficultyLevelEnum = DifficultyLevelEnum.INTERMEDIATE
    card_types: List[CardTypeEnum] = Field(default=[CardTypeEnum.BASIC])
    auto_generate: bool = False
    
    @field_validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class GenerateFlashcardsRequest(BaseModel):
    """Request model for generating flashcards from text."""
    text: str = Field(..., min_length=10)
    set_name: str = Field(..., min_length=1, max_length=200)
    max_cards: int = Field(20, ge=1, le=200)
    difficulty: DifficultyLevelEnum = DifficultyLevelEnum.INTERMEDIATE
    include_examples: bool = True
    include_definitions: bool = True
    extract_concepts: bool = True
    model: str = "llama2"
    temperature: float = Field(0.7, ge=0.1, le=1.0)
    
    @field_validator('text')
    def validate_text(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Text must be at least 10 characters')
        return v.strip()


class FlashcardCreateRequest(BaseModel):
    """Request model for creating a single flashcard."""
    front: str = Field(..., min_length=1, max_length=500)
    back: str = Field(..., min_length=1, max_length=1000)
    hints: Optional[str] = Field(None, max_length=200)
    topic: Optional[str] = Field(None, max_length=100)
    subtopic: Optional[str] = Field(None, max_length=100)
    difficulty: DifficultyLevelEnum = DifficultyLevelEnum.INTERMEDIATE
    card_type: CardTypeEnum = CardTypeEnum.BASIC
    tags: List[str] = Field(default_factory=list)
    set_id: Optional[str] = None


class FlashcardUpdateRequest(BaseModel):
    """Request model for updating a flashcard."""
    front: Optional[str] = Field(None, min_length=1, max_length=500)
    back: Optional[str] = Field(None, min_length=1, max_length=1000)
    hints: Optional[str] = Field(None, max_length=200)
    topic: Optional[str] = Field(None, max_length=100)
    subtopic: Optional[str] = Field(None, max_length=100)
    difficulty: Optional[DifficultyLevelEnum] = None
    tags: Optional[List[str]] = None


class ReviewFlashcardRequest(BaseModel):
    """Request model for reviewing a flashcard."""
    card_id: str = Field(..., min_length=1)
    quality: int = Field(..., ge=0, le=5)
    response_time: float = Field(..., gt=0, le=3600)
    deck_name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('quality')
    def validate_quality(cls, v):
        if v not in [0, 1, 2, 3, 4, 5]:
            raise ValueError('Quality must be 0-5')
        return v


class BulkReviewRequest(BaseModel):
    """Request model for bulk reviews."""
    reviews: List[ReviewFlashcardRequest] = Field(..., max_items=100)


class ScanSubjectRequest(BaseModel):
    """Request model for scanning a subject folder."""
    subject_name: str = Field(..., min_length=1, max_length=100)
    auto_generate: bool = True
    difficulty: DifficultyLevelEnum = DifficultyLevelEnum.INTERMEDIATE
    max_cards: int = Field(20, ge=1, le=100)


class FlashcardSetResponse(BaseModel):
    """Response model for flashcard set."""
    id: str
    name: str
    description: Optional[str]
    source_document: Optional[str]
    card_count: int
    created_at: str
    updated_at: str
    tags: List[str]
    difficulty: str
    stats: Optional[Dict[str, Any]] = None


class FlashcardResponse(BaseModel):
    """Response model for flashcard."""
    id: str
    front: str
    back: str
    hints: Optional[str]
    topic: Optional[str]
    subtopic: Optional[str]
    difficulty: str
    card_type: str
    tags: List[str]
    confidence: float
    created_at: str
    updated_at: str
    set_id: Optional[str] = None


class CardProgressResponse(BaseModel):
    """Response model for card progress."""
    card_id: str
    interval: int
    ease_factor: float
    repetitions: int
    lapses: int
    due_date: str
    last_review: Optional[str]
    total_reviews: int
    average_response_time: float
    is_due: bool
    days_overdue: int


# API Endpoints

@router.post("/sets", response_model=FlashcardSetResponse)
async def create_flashcard_set(
    request: CreateFlashcardSetRequest,
    background_tasks: BackgroundTasks,
    generator: FlashcardGenerator = Depends(get_flashcard_generator)
) -> Dict[str, Any]:
    """
    Create a new flashcard set.
    
    Args:
        request: Flashcard set creation request
        background_tasks: FastAPI background tasks
        generator: Flashcard generator instance
        
    Returns:
        Created flashcard set
    """
    try:
        # Create empty set
        flashcard_set = FlashcardSet(
            name=request.name,
            description=request.description,
            source_document=request.source_document,
            tags=request.tags
        )
        
        # Auto-generate if requested
        if request.auto_generate and request.source_document:
            # This would trigger background generation
            background_tasks.add_task(
                generate_flashcards_background,
                flashcard_set.id,
                request.source_document,
                request.difficulty,
                generator
            )
        
        # Save set
        await generator._save_flashcard_set(flashcard_set)
        
        return FlashcardSetResponse(
            id=flashcard_set.id,
            name=flashcard_set.name,
            description=flashcard_set.description,
            source_document=flashcard_set.source_document,
            card_count=len(flashcard_set.flashcards),
            created_at=flashcard_set.created_at.isoformat(),
            updated_at=flashcard_set.updated_at.isoformat(),
            tags=flashcard_set.tags,
            difficulty=request.difficulty.value,
            stats=flashcard_set.get_stats()
        )
        
    except Exception as e:
        logger.error(f"Error creating flashcard set: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=FlashcardSetResponse)
async def generate_flashcards(
    request: GenerateFlashcardsRequest,
    generator: FlashcardGenerator = Depends(get_flashcard_generator)
) -> Dict[str, Any]:
    """
    Generate flashcards from text.
    
    Args:
        request: Generation request
        generator: Flashcard generator instance
        
    Returns:
        Generated flashcard set
    """
    try:
        # Configure generation options
        options = GenerationOptions(
            max_cards_per_chunk=min(request.max_cards, 20),
            difficulty=DifficultyLevel(request.difficulty.value),
            include_examples=request.include_examples,
            include_definitions=request.include_definitions,
            extract_key_concepts=request.extract_concepts,
            model=request.model,
            temperature=request.temperature
        )
        
        # Generate flashcards
        flashcard_set = await generator.generate_from_text(
            text=request.text,
            set_name=request.set_name,
            options=options
        )
        
        return FlashcardSetResponse(
            id=flashcard_set.id,
            name=flashcard_set.name,
            description=flashcard_set.description,
            source_document=flashcard_set.source_document,
            card_count=len(flashcard_set.flashcards),
            created_at=flashcard_set.created_at.isoformat(),
            updated_at=flashcard_set.updated_at.isoformat(),
            tags=flashcard_set.tags,
            difficulty=request.difficulty.value,
            stats=flashcard_set.get_stats()
        )
        
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    set_name: str = Form(...),
    auto_generate: bool = Form(True),
    difficulty: str = Form("intermediate"),
    background_tasks: BackgroundTasks = None,
    generator: FlashcardGenerator = Depends(get_flashcard_generator)
) -> Dict[str, Any]:
    """
    Upload a document and optionally generate flashcards.
    
    Args:
        file: Uploaded file
        set_name: Name for the flashcard set
        auto_generate: Whether to auto-generate flashcards
        difficulty: Difficulty level
        background_tasks: FastAPI background tasks
        generator: Flashcard generator instance
        
    Returns:
        Upload status
    """
    try:
        # Validate file type
        content = await file.read(2048)
        file_type = magic.from_buffer(content, mime=True)
        
        if not file_type.startswith(('text/', 'application/pdf')):
            raise HTTPException(
                status_code=400,
                detail="Only text files and PDFs are supported"
            )
        
        # Reset file position
        await file.seek(0)
        
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8', errors='ignore')
        
        # Create set
        flashcard_set = FlashcardSet(
            name=set_name,
            source_document=file.filename,
            tags=[difficulty]
        )
        
        await generator._save_flashcard_set(flashcard_set)
        
        # Generate flashcards in background if requested
        if auto_generate:
            background_tasks.add_task(
                generate_from_document_background,
                flashcard_set.id,
                text_content,
                difficulty,
                generator
            )
        
        return {
            "status": "success",
            "message": f"File {file.filename} uploaded successfully",
            "set_id": flashcard_set.id,
            "set_name": set_name,
            "file_name": file.filename,
            "file_size": len(content),
            "auto_generate": auto_generate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan-subject", response_model=Dict[str, Any])
async def scan_subject_folder(
    request: ScanSubjectRequest,
    background_tasks: BackgroundTasks,
    generator: FlashcardGenerator = Depends(get_flashcard_generator)
) -> Dict[str, Any]:
    """
    Scan a subject folder for materials and optionally generate flashcards.
    
    Args:
        request: Scan subject request
        background_tasks: FastAPI background tasks
        generator: Flashcard generator instance
        
    Returns:
        Scanning status and detected files
    """
    try:
        scanner = SubjectScanner()
        subjects = scanner.scan_all_subjects()
        
        if request.subject_name not in subjects:
            # Try to list available subjects to help the user
            available = list(subjects.keys())
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": f"Subject folder '{request.subject_name}' not found",
                    "available_subjects": available
                }
            )
        
        files = subjects[request.subject_name]
        
        if request.auto_generate:
            background_tasks.add_task(
                generate_from_subject_background,
                request.subject_name,
                request.difficulty,
                request.max_cards,
                generator
            )
            
        return {
            "status": "success",
            "subject": request.subject_name,
            "file_count": len(files),
            "files": [f.name for f in files],
            "auto_generation_triggered": request.auto_generate,
            "message": f"Found {len(files)} files. Generation started." if request.auto_generate else f"Found {len(files)} files."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning subject: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subjects", response_model=Dict[str, Any])
async def create_subject_folder(
    request: CreateSubjectRequest
) -> Dict[str, Any]:
    """
    Physically create a new subject folder in the data/subjects directory.
    
    Args:
        request: Create subject request
        
    Returns:
        Status and folder path
    """
    try:
        scanner = SubjectScanner()
        # Ensure root_dir exists (constructor should do this but safety first)
        if not scanner.root_dir.exists():
            scanner.root_dir.mkdir(parents=True, exist_ok=True)
            
        subject_path = scanner.root_dir / request.name
        
        if subject_path.exists():
            return {
                "status": "already_exists",
                "message": f"Subject folder '{request.name}' already exists.",
                "path": str(subject_path)
            }
            
        subject_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created new subject folder at {subject_path}")
        
        return {
            "status": "success",
            "message": f"Subject folder '{request.name}' created successfully.",
            "path": str(subject_path)
        }
        
    except Exception as e:
        logger.error(f"Error creating subject folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sets", response_model=List[FlashcardSetResponse])
async def list_flashcard_sets(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    tag: Optional[str] = Query(None),
    generator: FlashcardGenerator = Depends(get_flashcard_generator)
) -> List[Dict[str, Any]]:
    """
    List all flashcard sets.
    
    Args:
        limit: Maximum number of sets
        offset: Pagination offset
        tag: Filter by tag
        generator: Flashcard generator instance
        
    Returns:
        List of flashcard sets
    """
    try:
        sets = await generator.list_flashcard_sets()
        
        # Apply filters
        if tag:
            sets = [s for s in sets if tag in s.get('tags', [])]
        
        # Apply pagination
        paginated = sets[offset:offset + limit]
        
        return [
            FlashcardSetResponse(
                id=s['id'],
                name=s['name'],
                description=s.get('description'),
                source_document=s.get('source_document'),
                card_count=s['card_count'],
                created_at=s['created_at'],
                updated_at=s.get('updated_at', s['created_at']),
                tags=s.get('tags', []),
                difficulty=s.get('tags', ['intermediate'])[0] if s.get('tags') else 'intermediate'
            )
            for s in paginated
        ]
        
    except Exception as e:
        logger.error(f"Error listing flashcard sets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sets/{set_id}", response_model=FlashcardSetResponse)
async def get_flashcard_set(
    set_id: str = PathParam(..., min_length=1),
    generator: FlashcardGenerator = Depends(get_flashcard_generator)
) -> Dict[str, Any]:
    """
    Get a specific flashcard set.
    
    Args:
        set_id: Flashcard set ID
        generator: Flashcard generator instance
        
    Returns:
        Flashcard set details
    """
    try:
        flashcard_set = await generator.load_flashcard_set(set_id)
        
        if not flashcard_set:
            raise HTTPException(status_code=404, detail="Flashcard set not found")
        
        return FlashcardSetResponse(
            id=flashcard_set.id,
            name=flashcard_set.name,
            description=flashcard_set.description,
            source_document=flashcard_set.source_document,
            card_count=len(flashcard_set.flashcards),
            created_at=flashcard_set.created_at.isoformat(),
            updated_at=flashcard_set.updated_at.isoformat(),
            tags=flashcard_set.tags,
            difficulty=flashcard_set.tags[0] if flashcard_set.tags else 'intermediate',
            stats=flashcard_set.get_stats()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flashcard set: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sets/{set_id}")
async def delete_flashcard_set(
    set_id: str = PathParam(..., min_length=1),
    generator: FlashcardGenerator = Depends(get_flashcard_generator)
) -> Dict[str, str]:
    """
    Delete a flashcard set.
    
    Args:
        set_id: Flashcard set ID
        generator: Flashcard generator instance
        
    Returns:
        Deletion confirmation
    """
    try:
        file_path = generator.data_dir / f"{set_id}.json"
        
        if file_path.exists():
            file_path.unlink()
            return {"status": "success", "message": f"Set {set_id} deleted"}
        else:
            raise HTTPException(status_code=404, detail="Flashcard set not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting flashcard set: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sets/{set_id}/cards", response_model=FlashcardResponse)
async def add_flashcard(
    set_id: str = PathParam(..., min_length=1),
    request: FlashcardCreateRequest = None,
    generator: FlashcardGenerator = Depends(get_flashcard_generator)
) -> Dict[str, Any]:
    """
    Add a flashcard to a set.
    
    Args:
        set_id: Flashcard set ID
        request: Flashcard creation request
        generator: Flashcard generator instance
        
    Returns:
        Created flashcard
    """
    try:
        flashcard_set = await generator.load_flashcard_set(set_id)
        
        if not flashcard_set:
            raise HTTPException(status_code=404, detail="Flashcard set not found")
        
        # Create flashcard
        flashcard = Flashcard(
            front=request.front,
            back=request.back,
            hints=request.hints,
            topic=request.topic,
            subtopic=request.subtopic,
            difficulty=DifficultyLevel(request.difficulty.value),
            card_type=CardType(request.card_type.value),
            tags=request.tags,
            confidence=1.0  # Manual cards start with full confidence
        )
        
        flashcard_set.add_flashcard(flashcard)
        await generator._save_flashcard_set(flashcard_set)
        
        return FlashcardResponse(
            id=flashcard.id,
            front=flashcard.front,
            back=flashcard.back,
            hints=flashcard.hints,
            topic=flashcard.topic,
            subtopic=flashcard.subtopic,
            difficulty=flashcard.difficulty.value,
            card_type=flashcard.card_type.value,
            tags=flashcard.tags,
            confidence=flashcard.confidence,
            created_at=flashcard.created_at.isoformat(),
            updated_at=flashcard.updated_at.isoformat(),
            set_id=set_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding flashcard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sets/{set_id}/cards", response_model=List[FlashcardResponse])
async def list_flashcards(
    set_id: str = PathParam(..., min_length=1),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    generator: FlashcardGenerator = Depends(get_flashcard_generator)
) -> List[Dict[str, Any]]:
    """
    List flashcards in a set.
    
    Args:
        set_id: Flashcard set ID
        limit: Maximum number of cards
        offset: Pagination offset
        generator: Flashcard generator instance
        
    Returns:
        List of flashcards
    """
    try:
        flashcard_set = await generator.load_flashcard_set(set_id)
        
        if not flashcard_set:
            raise HTTPException(status_code=404, detail="Flashcard set not found")
        
        # Apply pagination
        cards = flashcard_set.flashcards[offset:offset + limit]
        
        return [
            FlashcardResponse(
                id=card.id,
                front=card.front,
                back=card.back,
                hints=card.hints,
                topic=card.topic,
                subtopic=card.subtopic,
                difficulty=card.difficulty.value,
                card_type=card.card_type.value,
                tags=card.tags,
                confidence=card.confidence,
                created_at=card.created_at.isoformat(),
                updated_at=card.updated_at.isoformat(),
                set_id=set_id
            )
            for card in cards
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing flashcards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/{card_id}", response_model=FlashcardResponse)
async def get_flashcard(
    card_id: str = PathParam(..., min_length=1),
    generator: FlashcardGenerator = Depends(get_flashcard_generator)
) -> Dict[str, Any]:
    """
    Get a specific flashcard.
    
    Args:
        card_id: Flashcard ID
        generator: Flashcard generator instance
        
    Returns:
        Flashcard details
    """
    try:
        # Search through all sets
        sets = await generator.list_flashcard_sets()
        
        for set_info in sets:
            flashcard_set = await generator.load_flashcard_set(set_info['id'])
            if flashcard_set:
                for card in flashcard_set.flashcards:
                    if card.id == card_id:
                        return FlashcardResponse(
                            id=card.id,
                            front=card.front,
                            back=card.back,
                            hints=card.hints,
                            topic=card.topic,
                            subtopic=card.subtopic,
                            difficulty=card.difficulty.value,
                            card_type=card.card_type.value,
                            tags=card.tags,
                            confidence=card.confidence,
                            created_at=card.created_at.isoformat(),
                            updated_at=card.updated_at.isoformat(),
                            set_id=set_info['id']
                        )
        
        raise HTTPException(status_code=404, detail="Flashcard not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flashcard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cards/{card_id}")
async def update_flashcard(
    card_id: str = PathParam(..., min_length=1),
    request: FlashcardUpdateRequest = None,
    generator: FlashcardGenerator = Depends(get_flashcard_generator)
) -> Dict[str, str]:
    """
    Update a flashcard.
    
    Args:
        card_id: Flashcard ID
        request: Update request
        generator: Flashcard generator instance
        
    Returns:
        Update confirmation
    """
    try:
        # Search through all sets
        sets = await generator.list_flashcard_sets()
        
        for set_info in sets:
            flashcard_set = await generator.load_flashcard_set(set_info['id'])
            if flashcard_set:
                for i, card in enumerate(flashcard_set.flashcards):
                    if card.id == card_id:
                        # Update fields
                        if request.front:
                            card.front = request.front
                        if request.back:
                            card.back = request.back
                        if request.hints is not None:
                            card.hints = request.hints
                        if request.topic is not None:
                            card.topic = request.topic
                        if request.subtopic is not None:
                            card.subtopic = request.subtopic
                        if request.difficulty:
                            card.difficulty = DifficultyLevel(request.difficulty.value)
                        if request.tags is not None:
                            card.tags = request.tags
                        
                        card.updated_at = datetime.now()
                        
                        # Save set
                        await generator._save_flashcard_set(flashcard_set)
                        
                        return {"status": "success", "message": "Flashcard updated"}
        
        raise HTTPException(status_code=404, detail="Flashcard not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating flashcard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cards/{card_id}")
async def delete_flashcard(
    card_id: str = PathParam(..., min_length=1),
    generator: FlashcardGenerator = Depends(get_flashcard_generator)
) -> Dict[str, str]:
    """
    Delete a flashcard.
    
    Args:
        card_id: Flashcard ID
        generator: Flashcard generator instance
        
    Returns:
        Deletion confirmation
    """
    try:
        # Search through all sets
        sets = await generator.list_flashcard_sets()
        
        for set_info in sets:
            flashcard_set = await generator.load_flashcard_set(set_info['id'])
            if flashcard_set:
                if flashcard_set.remove_flashcard(card_id):
                    await generator._save_flashcard_set(flashcard_set)
                    return {"status": "success", "message": "Flashcard deleted"}
        
        raise HTTPException(status_code=404, detail="Flashcard not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting flashcard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review")
async def review_flashcard(
    request: ReviewFlashcardRequest,
    user_id: str = Query(..., min_length=1),
    sr: SpacedRepetition = Depends(get_spaced_repetition)
) -> Dict[str, Any]:
    """
    Process a flashcard review.
    
    Args:
        request: Review request
        user_id: User identifier
        sr: Spaced repetition instance
        
    Returns:
        Updated card progress
    """
    try:
        progress = sr.process_review(
            card_id=request.card_id,
            user_id=user_id,
            quality=request.quality,
            response_time=request.response_time,
            deck_name=request.deck_name,
            metadata=request.metadata
        )
        
        return {
            "status": "success",
            "card_id": request.card_id,
            "next_review": progress.due_date.isoformat(),
            "interval_days": progress.interval,
            "ease_factor": progress.ease_factor,
            "repetitions": progress.repetitions,
            "lapses": progress.lapses,
            "is_due": progress.is_due(),
            "days_overdue": progress.days_overdue()
        }
        
    except Exception as e:
        logger.error(f"Error processing review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/bulk")
async def bulk_review(
    request: BulkReviewRequest,
    user_id: str = Query(..., min_length=1),
    sr: SpacedRepetition = Depends(get_spaced_repetition)
) -> List[Dict[str, Any]]:
    """
    Process multiple flashcard reviews in bulk.
    
    Args:
        request: Bulk review request
        user_id: User identifier
        sr: Spaced repetition instance
        
    Returns:
        List of updated card progress
    """
    try:
        results = []
        for review in request.reviews:
            progress = sr.process_review(
                card_id=review.card_id,
                user_id=user_id,
                quality=review.quality,
                response_time=review.response_time,
                deck_name=review.deck_name,
                metadata=review.metadata
            )
            
            results.append({
                "card_id": review.card_id,
                "next_review": progress.due_date.isoformat(),
                "interval_days": progress.interval,
                "status": "success"
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing bulk reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/due")
async def get_due_cards(
    user_id: str = Query(..., min_length=1),
    deck_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    sr: SpacedRepetition = Depends(get_spaced_repetition)
) -> List[Dict[str, Any]]:
    """
    Get cards due for review.
    
    Args:
        user_id: User identifier
        deck_name: Optional deck filter
        limit: Maximum number of cards
        sr: Spaced repetition instance
        
    Returns:
        List of due cards
    """
    try:
        due_cards = sr.get_due_cards(
            user_id=user_id,
            deck_name=deck_name,
            limit=limit
        )
        
        return due_cards
        
    except Exception as e:
        logger.error(f"Error getting due cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/{card_id}")
async def get_card_progress(
    card_id: str = PathParam(..., min_length=1),
    user_id: str = Query(..., min_length=1),
    sr: SpacedRepetition = Depends(get_spaced_repetition)
) -> CardProgressResponse:
    """
    Get progress for a specific card.
    
    Args:
        card_id: Card identifier
        user_id: User identifier
        sr: Spaced repetition instance
        
    Returns:
        Card progress details
    """
    try:
        progress = sr.get_card_progress(card_id, user_id)
        
        if not progress:
            # Return default progress for new cards
            return CardProgressResponse(
                card_id=card_id,
                interval=0,
                ease_factor=2.5,
                repetitions=0,
                lapses=0,
                due_date=datetime.now().isoformat(),
                last_review=None,
                total_reviews=0,
                average_response_time=0,
                is_due=True,
                days_overdue=0
            )
        
        return CardProgressResponse(
            card_id=progress.card_id,
            interval=progress.interval,
            ease_factor=progress.ease_factor,
            repetitions=progress.repetitions,
            lapses=progress.lapses,
            due_date=progress.due_date.isoformat(),
            last_review=progress.last_review.isoformat() if progress.last_review else None,
            total_reviews=progress.total_reviews,
            average_response_time=progress.average_response_time,
            is_due=progress.is_due(),
            days_overdue=progress.days_overdue()
        )
        
    except Exception as e:
        logger.error(f"Error getting card progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_review_stats(
    user_id: str = Query(..., min_length=1),
    deck_name: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    sr: SpacedRepetition = Depends(get_spaced_repetition)
) -> Dict[str, Any]:
    """
    Get review statistics.
    
    Args:
        user_id: User identifier
        deck_name: Optional deck filter
        days: Number of days to analyze
        sr: Spaced repetition instance
        
    Returns:
        Review statistics
    """
    try:
        stats = sr.get_review_stats(
            user_id=user_id,
            deck_name=deck_name,
            days=days
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting review stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/{card_id}")
async def predict_next_review(
    card_id: str = PathParam(..., min_length=1),
    user_id: str = Query(..., min_length=1),
    quality: Optional[int] = Query(None, ge=0, le=5),
    sr: SpacedRepetition = Depends(get_spaced_repetition)
) -> Dict[str, Any]:
    """
    Predict when a card will be due next.
    
    Args:
        card_id: Card identifier
        user_id: User identifier
        quality: Optional quality for prediction
        sr: Spaced repetition instance
        
    Returns:
        Prediction results
    """
    try:
        quality_enum = ReviewQuality(quality) if quality is not None else None
        prediction = sr.predict_next_review(
            card_id=card_id,
            user_id=user_id,
            quality=quality_enum
        )
        
        return prediction
        
    except Exception as e:
        logger.error(f"Error predicting next review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset/{card_id}")
async def reset_card(
    card_id: str = PathParam(..., min_length=1),
    user_id: str = Query(..., min_length=1),
    sr: SpacedRepetition = Depends(get_spaced_repetition)
) -> Dict[str, str]:
    """
    Reset a card's progress.
    
    Args:
        card_id: Card identifier
        user_id: User identifier
        sr: Spaced repetition instance
        
    Returns:
        Reset confirmation
    """
    try:
        success = sr.reset_card(card_id, user_id)
        
        if success:
            return {"status": "success", "message": f"Card {card_id} reset"}
        else:
            raise HTTPException(status_code=404, detail="Card not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting card: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{user_id}")
async def flashcards_websocket(
    websocket: WebSocket,
    user_id: str,
    sr: SpacedRepetition = Depends(get_spaced_repetition)
):
    """
    WebSocket endpoint for real-time flashcard updates.
    
    Args:
        websocket: WebSocket connection
        user_id: User identifier
        sr: Spaced repetition instance
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for user {user_id}")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            command = data.get('command')
            
            if command == 'get_due':
                # Get due cards
                limit = data.get('limit', 10)
                due_cards = sr.get_due_cards(user_id, limit=limit)
                await websocket.send_json({
                    'type': 'due_cards',
                    'data': due_cards
                })
                
            elif command == 'review':
                # Process review
                review_data = data.get('review', {})
                progress = sr.process_review(
                    card_id=review_data['card_id'],
                    user_id=user_id,
                    quality=review_data['quality'],
                    response_time=review_data['response_time']
                )
                await websocket.send_json({
                    'type': 'review_result',
                    'data': {
                        'card_id': review_data['card_id'],
                        'next_review': progress.due_date.isoformat(),
                        'interval': progress.interval
                    }
                })
                
            elif command == 'stats':
                # Get statistics
                stats = sr.get_review_stats(user_id)
                await websocket.send_json({
                    'type': 'stats',
                    'data': stats
                })
                
            elif command == 'subscribe':
                # Subscribe to updates for specific cards
                card_ids = data.get('card_ids', [])
                # Implementation would store subscriptions
                await websocket.send_json({
                    'type': 'subscribed',
                    'data': {'card_ids': card_ids}
                })
                
            elif command == 'ping':
                await websocket.send_json({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                })
                
            else:
                await websocket.send_json({
                    'type': 'error',
                    'message': f'Unknown command: {command}'
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        await websocket.close()


# Background tasks

async def generate_flashcards_background(
    set_id: str,
    source: str,
    difficulty: str,
    generator: FlashcardGenerator
):
    """
    Background task for flashcard generation.
    
    Args:
        set_id: Flashcard set ID
        source: Source text or document path
        difficulty: Difficulty level
        generator: Flashcard generator instance
    """
    try:
        logger.info(f"Starting background generation for set {set_id}")
        
        # Load the set
        flashcard_set = await generator.load_flashcard_set(set_id)
        if not flashcard_set:
            logger.error(f"Set {set_id} not found")
            return
        
        # Generate flashcards
        options = GenerationOptions(
            difficulty=DifficultyLevel(difficulty),
            max_cards_per_chunk=10
        )
        
        new_set = await generator.generate_from_text(
            text=source,
            set_name=flashcard_set.name,
            options=options
        )
        
        # Update original set with new cards
        flashcard_set.flashcards.extend(new_set.flashcards)
        flashcard_set.updated_at = datetime.now()
        
        # Save
        await generator._save_flashcard_set(flashcard_set)
        
        logger.info(f"Background generation completed for set {set_id}")
        
    except Exception as e:
        logger.error(f"Background generation failed for set {set_id}: {e}")


async def generate_from_document_background(
    set_id: str,
    content: str,
    difficulty: str,
    generator: FlashcardGenerator
):
    """
    Background task for generating flashcards from document.
    
    Args:
        set_id: Flashcard set ID
        content: Document content
        difficulty: Difficulty level
        generator: Flashcard generator instance
    """
    await generate_flashcards_background(set_id, content, difficulty, generator)


async def generate_from_subject_background(
    subject_name: str,
    difficulty: DifficultyLevelEnum,
    max_cards: int,
    generator: FlashcardGenerator
):
    """
    Background task for generating flashcards from a scanned subject folder.
    """
    try:
        scanner = SubjectScanner()
        content = scanner.get_subject_content(subject_name)
        
        if not content:
            logger.warning(f"No text content extracted for subject: {subject_name}")
            return
            
        options = GenerationOptions(
            difficulty=DifficultyLevel(difficulty.value),
            max_cards_per_chunk=min(max_cards, 15),
            extract_key_concepts=True
        )
        
        async with generator:
            await generator.generate_from_text(
                text=content,
                set_name=f"Subject: {subject_name}",
                options=options
            )
            
        logger.info(f"Successfully generated flashcards for subject: {subject_name}")
            
    except Exception as e:
        logger.error(f"Background subject generation error for {subject_name}: {e}")


# Health check endpoint

@router.get("/health")
async def health_check(
    generator: FlashcardGenerator = Depends(get_flashcard_generator),
    sr: SpacedRepetition = Depends(get_spaced_repetition)
) -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Args:
        generator: Flashcard generator instance
        sr: Spaced repetition instance
        
    Returns:
        Health status
    """
    try:
        # Check generator
        generator_health = await generator.health_check()
        
        # Check spaced repetition
        sr_health = {
            "status": "healthy",
            "db_path": str(sr.db_path),
            "db_exists": sr.db_path.exists()
        }
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "modules": {
                "generator": generator_health,
                "spaced_repetition": sr_health
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }