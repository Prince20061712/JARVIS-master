# Flashcard & Academic Intelligence System v3.0
**The highly robust, AI-powered spaced repetition and viva exam module for JARVIS.**

Provides end-to-end capabilities from scanning raw user materials to generating adaptive flashcards, scheduling reviews via memory modeling, conducting realistic oral Viva exams with real-time feedback, and delivering comprehensive academic intelligence.

---

## 🛠 Tech Stack
The `flashcard_system` relies on modern Python libraries for speed, robustness, type safety, and artificial intelligence:

**Core & API**
- FastAPI, Uvicorn, WebSockets for REST APIs and real-time communication
- Pydantic V2 for data validation and serialization
- SQLAlchemy for ORM database operations

**AI & Learning**
- Ollama local LLM for intelligent flashcard generation
- Chroma DB for vector storage and semantic search
- Numpy, Scikit-learn for analytics and spaced repetition

**Vision & Processing**
- OpenCV, Pillow, Tesseract OCR for document and handwriting recognition
- Shapely for geometric shape detection in diagrams
- pdf2image for PDF processing

**Infrastructure**
- Asyncio and multithreading for concurrent operations
- Pytest for unit and integration testing
- SQLite for persistent data storage

---

## 📂 Architecture Overview v3.0

The v3.0 architecture provides a consolidated, scalable structure organized by concerns:

```
flashcard_system/
├── core/                    # Core flashcard & memory models
│   ├── generator.py         # LLM-driven card generation
│   ├── spaced_repetition.py # SM-2 algorithm implementation
│   └── models/              # Consolidated data models
├── api/                     # REST API controllers
│   ├── flashcard_controller.py
│   └── viva_controller.py
├── academic/                # Tutor & formatter engine
│   ├── response_formatter/  # Code, diagrams, marks allocation
│   ├── concept_explainer/   # Analogies, prerequisites, explanations
│   └── exam_simulator/      # Questions, answers, time management
├── vision/                  # Vision processing & OCR
│   ├── hand_drawing.py      # Handwriting recognition
│   ├── ocr_processor.py     # OCR and text extraction
│   └── diagram_detector.py  # Diagram analysis
├── viva/                    # Viva exam orchestration
│   ├── viva_session.py      # Session management
│   └── adaptive_questioner.py
├── websocket/               # Real-time communication
│   ├── events.py
│   ├── handlers.py
│   └── connection_manager.py
├── analytics/               # Learning analytics
│   ├── learning_patterns.py
│   └── api_routes.py
├── config/                  # Configuration management
│   ├── settings.py          # Application settings
│   └── logging_config.py    # Logging setup
├── storage/                 # Data persistence
│   ├── repository.py        # Repository pattern
│   └── cache_manager.py     # Caching layer
├── utils/                   # Utilities & helpers
│   ├── validators.py        # Pydantic validators
│   ├── helpers.py           # Helper functions
│   └── constants.py         # Shared constants
├── tests/                   # Test suite
│   ├── test_api/
│   ├── test_core/
│   └── test_academic/
└── docs/                    # Documentation
    ├── README.md
    ├── ARCHITECTURE_V2.md
    ├── MODULE_REFERENCE.md
    └── [other docs...]
```

### Module Breakdown

#### 1. **core/** - Flashcard Core
The heart of the system handling flashcard lifecycle and memory optimization.

- `generator.py` - LLM-driven generation from documents
- `spaced_repetition.py` - SM-2 algorithm (48KB) with `CardProgress`, `ReviewLog`
- `models/card_models.py` - Consolidated `Flashcard`, `CardProgress`, `ReviewLog` models

#### 2. **api/** - REST API Layer
HTTP endpoints for all flashcard operations.

- `flashcard_controller.py` (44KB) - 20+ CRUD endpoints
- `viva_controller.py` - Viva exam endpoints

#### 3. **academic/** - Academic Intelligence (Integrated from v2.0)
Comprehensive academic tutoring and exam simulation.

**response_formatter/** (5 files)
- Code formatting, diagram generation, derivation building
- Marks allocation with academic rubrics
- Numerical equation solving

**concept_explainer/** (4 files)
- Real-world analogy generation
- Prerequisite gap identification
- Step-by-step explanations
- Visualization recommendations

**exam_simulator/** (3 files)
- Exam-style question generation
- Answer evaluation with feedback
- Time management for exams

#### 4. **vision/** - Vision Processing (Integrated from v2.0)
Handwriting recognition and diagram analysis.

- `hand_drawing.py` (1600+ lines) - Comprehensive sketch recognition
- `ocr_processor.py` - Text extraction with confidence scoring
- `diagram_detector.py` - Geometric shape and diagram analysis

#### 5. **viva/** - Viva Exam Orchestration
Interactive oral examination engine.

- `viva_session.py` (36KB) - Session state management
- `adaptive_questioner.py` (36KB) - Difficulty-adaptive questions

#### 6. **websocket/** - Real-Time Communication
Event-driven WebSocket infrastructure.

- `events.py` - WebSocket event definitions
- `handlers.py` - Connection and message handling
- `connection_manager.py` - Connection lifecycle management

#### 7. **analytics/** - Learning Analytics
Progress tracking and performance analysis.

- `learning_patterns.py` (46KB) - Retention metrics and weakness analysis
- `api_routes.py` (17KB) - Analytics endpoints

#### 8. **config/** - Configuration Management (NEW in v3.0)
Centralized application configuration.

- `settings.py` - Pydantic settings with environment support
- `logging_config.py` - Logging configuration and setup

#### 9. **storage/** - Data Persistence (NEW in v3.0)
Unified data access and caching layer.

- `repository.py` - Repository pattern for CRUD operations
- `cache_manager.py` - File and memory-based caching

#### 10. **utils/** - Shared Utilities (NEW in v3.0)
Common helper functions and validators.

- `validators.py` - Pydantic validators for cards and reviews
- `helpers.py` - Utility functions (ID generation, datetime handling, SM-2 calculations)
- `constants.py` - Shared constants (SM-2 params, study limits, API constants)

---

## 🚀 Quick Usage Example

**Triggering an Adaptive Viva:**

```python
from flashcard_system.viva import VivaSession, SessionConfig, VivaMode

config = SessionConfig(
    mode=VivaMode.ADAPTIVE,
    duration_minutes=30
)
session = VivaSession(config=config)
question = await session.generate_next_question()
print(question.content)
```

**Creating Flashcards:**

```python
from flashcard_system.core import Flashcard
from flashcard_system.utils.validators import CardValidator

# Validate and create
validated = CardValidator(
    front="What is photosynthesis?",
    back="Process by which plants convert light to chemical energy",
    subject="Biology",
    tags=["biology", "plants"]
)

card = Flashcard(**validated.dict())
```

**Integrating with FastAPI:**

```python
from flashcard_system.api.flashcard_controller import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix="/flashcard")
```

**Accessing Configuration:**

```python
from flashcard_system.config import Settings

settings = Settings()  # Loads from environment
print(settings.ollama_host)  # http://localhost:11434
print(settings.sm2_ease_factor_min)  # 1.3
```

---

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[docs/ARCHITECTURE_V2.md](docs/ARCHITECTURE_V2.md)** - Detailed system architecture
- **[docs/MODULE_REFERENCE.md](docs/MODULE_REFERENCE.md)** - Complete API reference
- **[docs/STRUCTURE.md](docs/STRUCTURE.md)** - Directory structure guide
- **[docs/IMPORT_GUIDE.md](docs/IMPORT_GUIDE.md)** - Import examples
- **[docs/README.md](docs/README.md)** - Documentation index

---

## ⚙️ Configuration

Application settings are managed through:

- **Environment Variables**: Set in `.env` file
- **`config/settings.py`**: Pydantic BaseSettings with validation
- **`config/logging_config.py`**: Logging configuration defaults

Key settings:
```python
# LLM Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=neural-chat

# Database
DATABASE_URL=sqlite:///./jarvis_flashcards.db

# Vector Store
VECTOR_DB_PATH=./chroma_db

# Study Limits
DAILY_CARD_LIMIT=50
NEW_CARD_LIMIT=20
REVIEW_CARD_LIMIT=30
```

---

## 🧪 Testing

Test files are organized by module:

```
tests/
├── test_api/        # API endpoint tests
├── test_core/       # Core functionality tests
└── test_academic/   # Academic module tests
```

Run tests with:
```bash
pytest tests/ -v
```

---

## 📊 Version History

- **v3.0.0** - Production consolidation with integrated academic intelligence, new infrastructure modules (config, storage, utils)
- **v2.0.0** - Comprehensive integration of academic_qa and adaptive_learning
- **v1.0.0** - Initial unified flashcard_system structure

---

## 🤝 Contributing

When adding new modules:

1. Place code in appropriate directory (core/, api/, academic/, etc.)
2. Create proper `__init__.py` with exports
3. Add validators to `utils/validators.py` if needed
4. Update `config/settings.py` if new config needed
5. Add tests in `tests/` directory
6. Update `docs/ARCHITECTURE_V2.md` and `docs/MODULE_REFERENCE.md`

---

## 📝 License

Part of the JARVIS Intelligent Assistant System.

---
*Architecture Re-Structured and Robustness Hardened - March 2026*
