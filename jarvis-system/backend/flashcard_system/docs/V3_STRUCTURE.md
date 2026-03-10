# v3.0 System Structure

## Directory Tree

```
flashcard_system/
│
├── __init__.py (v3.0 exports)
├── README.md (Updated for v3.0)
│
├── core/                           # Core flashcard & spaced repetition
│   ├── __init__.py
│   ├── generator.py               # LLM-driven card generation
│   ├── spaced_repetition.py       # SM-2 algorithm (48KB, 800+ lines)
│   └── models/                    # NEW: Consolidated data models
│       └── __init__.py
│
├── api/                           # REST API layer
│   ├── __init__.py
│   ├── flashcard_controller.py    # 20+ CRUD endpoints
│   ├── viva_controller.py         # Viva exam endpoints
│   └── rest/                      # Additional REST handlers
│       └── __init__.py
│
├── academic/                      # INTEGRATED: Comprehensive academic suite
│   ├── __init__.py
│   ├── response_formatter/        # Response structuring & formatting
│   │   ├── __init__.py
│   │   ├── code_formatter.py      # Code block formatting
│   │   ├── diagram_generator.py   # Visual diagram generation
│   │   ├── derivation_builder.py  # Math/physics derivations
│   │   ├── marks_allocator.py     # Grading rubrics
│   │   └── numerical_solver.py    # Mathematical solutions
│   ├── concept_explainer/         # Educational explanations
│   │   ├── __init__.py
│   │   ├── analogy_generator.py   # Real-world analogies
│   │   ├── prerequisite_check.py  # Knowledge gap analysis
│   │   ├── step_by_step.py        # Incremental explanations
│   │   └── visualization.py       # Multimedia recommendations
│   └── exam_simulator/            # Examination environment
│       ├── __init__.py
│       ├── question_generator.py  # Exam-style questions
│       ├── answer_evaluator.py    # Answer grading
│       └── time_manager.py        # Exam timing
│
├── vision/                        # ENHANCED: Vision processing
│   ├── __init__.py (v3.0 exports)
│   ├── hand_drawing.py            # Handwriting recognition (1600+ lines)
│   ├── ocr_processor.py           # NEW: OCR with confidence scoring
│   └── diagram_detector.py        # NEW: Shape & diagram analysis
│
├── viva/                          # Adaptive exam orchestration
│   ├── __init__.py
│   ├── viva_session.py            # Session management (36KB)
│   └── adaptive_questioner.py     # Difficulty-adaptive questions
│
├── websocket/                     # ENHANCED: Real-time communication
│   ├── __init__.py (v3.0 exports)
│   ├── events.py                  # WebSocket event definitions
│   ├── handlers.py                # Connection & message handling
│   └── connection_manager.py      # NEW: Centralized connection management
│
├── analytics/                     # Learning analytics & tracking
│   ├── __init__.py
│   ├── learning_patterns.py       # Retention & weakness analysis (46KB)
│   └── api_routes.py              # Analytics endpoints
│
├── config/                        # NEW: Configuration management
│   ├── __init__.py (v3.0 exports)
│   ├── settings.py                # NEW: Pydantic settings with env support
│   └── logging_config.py          # NEW: Centralized logging setup
│
├── storage/                       # NEW: Data persistence layer
│   ├── __init__.py (v3.0 exports)
│   ├── repository.py              # NEW: Repository pattern for CRUD
│   └── cache_manager.py           # NEW: File & memory caching
│
├── utils/                         # NEW: Helper utilities & constants
│   ├── __init__.py (v3.0 exports)
│   ├── validators.py              # NEW: Pydantic validators
│   ├── helpers.py                 # NEW: Utility functions
│   └── constants.py               # NEW: Shared constants
│
├── tests/                         # ENHANCED: Full test structure
│   ├── __init__.py
│   ├── conftest.py                # NEW: Pytest configuration & fixtures
│   ├── test_api/                  # API tests
│   │   └── __init__.py
│   ├── test_core/                 # Core logic tests
│   │   └── __init__.py
│   └── test_academic/             # Academic module tests
│       └── __init__.py
│
└── docs/                          # NEW: Organized documentation
    ├── README.md                  # NEW: Documentation index
    ├── V3_MIGRATION_GUIDE.md      # NEW: v2.0 → v3.0 migration
    ├── V3_STRUCTURE.md            # This file
    ├── ARCHITECTURE_V2.md         # Moved from root
    ├── MODULE_REFERENCE.md        # Moved from root
    ├── STRUCTURE.md               # Moved from root
    ├── IMPORTS_V2.md              # Moved from root
    ├── IMPORT_GUIDE.md            # Moved from root
    ├── INTEGRATION_COMPLETE.md    # Moved from root
    └── V2_SUMMARY.md              # Moved from root
```

## Key Statistics

### Code Organization
- **Total Modules**: 25+
- **Total Submodules**: 50+
- **Core Files**: 7 (generator, spaced_repetition, 5 models)
- **Vision Files**: 3 (NEW architecture with dedicated processors)
- **Academic Files**: 12 (response_formatter, concept_explainer, exam_simulator)
- **Utility Files**: 3 (validators, helpers, constants)
- **Configuration Files**: 2 (settings, logging)
- **Storage Files**: 2 (repository, cache)
- **Test Directories**: 4 (main + 3 specialized)

### File Sizes (Approximate)
- `core/spaced_repetition.py`: 48 KB, 800+ lines
- `vision/hand_drawing.py`: 50+ KB, 1600+ lines
- `viva/viva_session.py`: 36 KB, custom session management
- `viva/adaptive_questioner.py`: 36 KB, question generation
- `analytics/learning_patterns.py`: 46 KB, analytics engine
- `academic/response_formatter/`: 5 files, 80+ KB
- `academic/concept_explainer/`: 4 files, 70+ KB
- `academic/exam_simulator/`: 3 files, 60+ KB

### Documentation
- **Total Doc Files**: 10
- **Main README**: Updated for v3.0
- **Architecture Guides**: 2 (ARCHITECTURE_V2, V3_MIGRATION_GUIDE)
- **API Reference**: MODULE_REFERENCE.md
- **Import Guides**: 2 (IMPORTS_V2, IMPORT_GUIDE)
- **Migration Guides**: 2 (V3_MIGRATION_GUIDE, implicit in STRUCTURE)

## Module Imports Overview

### Core Imports
```python
from flashcard_system import (
    FlashcardGenerator, Flashcard,
    SpacedRepetition, CardProgress,
    Settings, setup_logging,
    Repository, CacheManager,
    CardValidator, ReviewValidator,
    generate_id, calculate_interval,
    SM2_CONSTANTS, STUDY_CONSTANTS
)
```

### Academic Imports
```python
from flashcard_system.academic import (
    CodeFormatter, DiagramGenerator,
    AnalogyGenerator, PrerequisiteCheck,
    QuestionGenerator, AnswerEvaluator
)
```

### Vision Imports
```python
from flashcard_system.vision import (
    HandDrawingRecognizer,
    OCRProcessor,      # NEW in v3.0
    DiagramAnalyzer    # NEW in v3.0
)
```

### Infrastructure Imports
```python
from flashcard_system.config import Settings, setup_logging
from flashcard_system.storage import Repository, CacheManager
from flashcard_system.websocket import ConnectionManager
from flashcard_system.utils import (
    CardValidator, ReviewValidator,
    generate_id, format_datetime,
    SM2_CONSTANTS, STUDY_CONSTANTS
)
```

## API Endpoints

### Flashcard Management
- `POST /api/flashcard/create` - Create new flashcard
- `GET /api/flashcard/{card_id}` - Get card details
- `PUT /api/flashcard/{card_id}` - Update card
- `DELETE /api/flashcard/{card_id}` - Delete card
- `GET /api/flashcard/list` - List cards with pagination
- `POST /api/flashcard/generate` - Generate from text

### Spaced Repetition
- `POST /api/flashcard/review` - Record review
- `GET /api/flashcard/next-review` - Get next card for review
- `GET /api/flashcard/stats` - Get learning statistics

### Viva Exams
- `POST /api/viva/start` - Start viva session
- `POST /api/viva/answer` - Submit answer
- `GET /api/viva/{session_id}` - Get session status
- `POST /api/viva/end` - End viva session

### Analytics
- `GET /api/analytics/progress` - Learning progress
- `GET /api/analytics/patterns` - Learning patterns
- `GET /api/analytics/weakness` - Weakness areas

## Configuration Options

```python
# Settings from environment or .env file
class Settings:
    api_title: str = "JARVIS Flashcard System"
    api_version: str = "3.0.0"
    debug: bool = False
    
    # Database
    db_url: str = "sqlite:///./jarvis_flashcards.db"
    
    # LLM
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "neural-chat"
    
    # Vector Store
    vector_db_path: str = "./chroma_db"
    
    # Caching
    cache_dir: str = "./cache"
    embeddings_cache_dir: str = "./cache/embeddings"
    
    # Logging
    log_level: str = "INFO"
    log_dir: str = "./logs"
    
    # Study Limits
    daily_card_limit: int = 50
    new_card_limit: int = 20
    review_card_limit: int = 30
```

## Dependencies (Key)

### Core
- FastAPI 0.95+
- Pydantic V2
- SQLAlchemy 2.0
- Uvicorn

### AI/ML
- Ollama (local LLM)
- Chroma (vector DB)
- NumPy, SciPy

### Vision
- OpenCV
- Pillow
- pytesseract
- Shapely

### Async/Concurrency
- asyncio
- WebSocket support

### Testing
- pytest
- pytest-asyncio (for async tests)

## Database Schema

### Core Tables
- `flashcards` - Card definitions
- `card_progress` - SM-2 tracking per user/card
- `review_logs` - Historical reviews
- `viva_sessions` - Exam sessions
- `analytics_data` - Learning metrics

## WebSocket Events

### Supported Events
- `question_generated` - New exam question
- `answer_evaluated` - Answer graded
- `session_started` - Exam begins
- `session_ended` - Exam ends
- `progress_updated` - Learning updated
- `message` - Real-time messages

## Testing Framework

### Test Organization
```
tests/
├── test_api/
│   ├── test_flashcard_controller.py
│   └── test_viva_controller.py
├── test_core/
│   ├── test_generator.py
│   ├── test_spaced_repetition.py
│   └── test_validators.py
└── test_academic/
    ├── test_response_formatter.py
    ├── test_concept_explainer.py
    └── test_exam_simulator.py
```

### Test Fixtures (conftest.py)
- `settings` - Test configuration
- `test_db_session` - Database session
- `test_cache_dir` - Temporary cache directory
- `event_loop` - Async event loop
- `setup_test_logging` - Test logging

## Environment Setup

### .env File Template
```
# API
DEBUG=False
API_TITLE=JARVIS Flashcard System
API_VERSION=3.0.0

# Database
DATABASE_URL=sqlite:///./jarvis_flashcards.db

# LLM
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=neural-chat

# Vector Store
VECTOR_DB_PATH=./chroma_db

# Cache
CACHE_DIR=./cache
EMBEDDINGS_CACHE_DIR=./cache/embeddings

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs

# Study
DAILY_CARD_LIMIT=50
NEW_CARD_LIMIT=20
REVIEW_CARD_LIMIT=30
```

## Deployment Considerations

### Requirements Met
- ✅ Configuration management (environment-aware)
- ✅ Logging infrastructure (centralized)
- ✅ Database abstraction (repository pattern)
- ✅ Caching layer (file + memory)
- ✅ Input validation (Pydantic)
- ✅ Error handling (standardized)
- ✅ Test structure (organized by module)
- ✅ Documentation (comprehensive)

### Production Checklist
- [ ] Set `DEBUG=False` in production
- [ ] Update `DATABASE_URL` to production database
- [ ] Configure `OLLAMA_HOST` for production LLM
- [ ] Set `LOG_LEVEL=WARNING` in production
- [ ] Use environment-specific `.env` files
- [ ] Run all tests before deployment
- [ ] Verify database migrations
- [ ] Configure backup strategy
- [ ] Set up monitoring and alerting

## Version Information

- **Current Version**: 3.0.0
- **Type**: Production consolidation
- **Date**: 2024
- **Python**: 3.8+
- **Status**: Stable for production use

## Related Documentation

- `docs/README.md` - Documentation index
- `docs/V3_MIGRATION_GUIDE.md` - Migration from v2.0
- `docs/ARCHITECTURE_V2.md` - System architecture
- `docs/MODULE_REFERENCE.md` - Complete API reference
- `README.md` - Quick start guide
