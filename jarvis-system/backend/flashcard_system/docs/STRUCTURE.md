# Flashcard System - Unified Architecture

## Overview

The Flashcard System is now centrally organized in `/backend/flashcard_system/` with all components organized by functionality rather than scattered across multiple folders.

## Directory Structure

```
flashcard_system/
├── core/                       # Core generation & scheduling
│   ├── generator.py           # FlashcardGenerator, TextProcessor
│   ├── spaced_repetition.py   # SM-2 algorithm implementation
│   └── __init__.py            # Module exports
│
├── api/                        # REST API endpoints
│   ├── flashcard_controller.py # Main API router (20+ endpoints)
│   └── __init__.py            # API exports
│
├── scanner/                    # Document/material processing
│   ├── subject_scanner.py     # Scans folders for materials
│   └── __init__.py            # Scanner exports
│
├── analytics/                  # Learning analytics
│   ├── learning_patterns.py   # Retention curves, weakness analysis
│   ├── api_routes.py          # Analytics endpoints
│   └── __init__.py            # Analytics exports
│
├── viva/                       # Exam sessions
│   ├── viva_session.py        # Session management & state
│   ├── adaptive_questioner.py # Dynamic question generation
│   └── __init__.py            # Viva exports
│
├── formatters/                 # Response formatting
│   ├── code_formatter.py      # Code snippet formatting
│   └── __init__.py            # Formatter exports
│
├── data_models/                # Centralized data models (expandable)
│   └── __init__.py            # Models exports
│
├── storage/                    # Persistence layer (expandable)
│   └── __init__.py            # Storage exports
│
├── utils/                      # Helper utilities (expandable)
│   └── __init__.py            # Utils exports
│
├── __init__.py                # Main package entry point
├── STRUCTURE.md               # This file
├── API.md                     # API documentation
└── ARCHITECTURE.md            # Detailed architecture guide
```

## Component Details

### `core/` - Flashcard Generation & Scheduling
**Purpose:** Core business logic for creating and scheduling flashcards

**Files:**
- **generator.py**
  - `FlashcardGenerator`: Main class for generating flashcards from text/documents
  - `Flashcard`: Individual card model with metadata
  - `FlashcardSet`: Collection of cards
  - `TextProcessor`: Chunks and processes text input
  - Enums: `CardType`, `DifficultyLevel`, `GenerationQuality`

- **spaced_repetition.py**
  - `SpacedRepetition`: Implements SM-2 algorithm for scheduling
  - `CardProgress`: Tracks card performance and next review date
  - `ReviewLog`: Records each review session
  - Dataclass: `SM2Parameters` - Algorithm configuration

**Usage:**
```python
from flashcard_system.core import FlashcardGenerator, SpacedRepetition

# Generate cards
generator = FlashcardGenerator(config)
cards = generator.generate_from_text("text content")

# Schedule reviews
sr = SpacedRepetition()
next_date = sr.calculate_next_review(card_id, quality_response)
```

---

### `api/` - REST API Endpoints
**Purpose:** Expose flashcard functionality via HTTP endpoints

**Files:**
- **flashcard_controller.py**
  - 20+ endpoints for CRUD, generation, review, and analytics
  - Dependency injection for services
  - Request/response models using Pydantic

**Main Endpoints:**
```
POST   /api/flashcards/sets              # Create set
GET    /api/flashcards/sets              # List sets
GET    /api/flashcards/sets/{id}         # Get set
DELETE /api/flashcards/sets/{id}         # Delete set

POST   /api/flashcards/generate          # Generate from text
POST   /api/flashcards/upload            # Upload + auto-generate
POST   /api/flashcards/scan-subject      # Scan materials

POST   /api/flashcards/review            # Submit review
GET    /api/flashcards/due               # Get due cards
GET    /api/flashcards/stats             # Get statistics
```

---

### `scanner/` - Document Processing
**Purpose:** Scan and process educational materials

**Files:**
- **subject_scanner.py**
  - `SubjectScanner`: Scans folders for materials
  - `MaterialProcessor`: Extracts text from PDF, DOCX, TXT, MD, PPT

**Usage:**
```python
from flashcard_system.scanner import SubjectScanner, MaterialProcessor

scanner = SubjectScanner("data/subjects")
materials = scanner.scan_subject("operating system")

processor = MaterialProcessor()
text = processor.extract_text("file.pdf")
```

---

### `analytics/` - Learning Analytics
**Purpose:** Analyze learning patterns and performance

**Files:**
- **learning_patterns.py**
  - `LearningPatterns`: Main analyzer
  - `RetentionCurve`: Forgetting curve analysis
  - `WeaknessAnalysis`: Identifies difficult topics
  - `PerformanceMetrics`: Review and mastery stats

- **api_routes.py**
  - Routes for analytics endpoints

**Usage:**
```python
from flashcard_system.analytics import LearningPatterns

analyzer = LearningPatterns()
patterns = analyzer.analyze_user_progress(user_id)
weaknesses = analyzer.identify_weaknesses(user_id)
```

---

### `viva/` - Exam Sessions
**Purpose:** Manage oral examination sessions

**Files:**
- **viva_session.py**
  - `VivaSession`: Manages exam state and flow
  - `SessionConfig`: Configuration for session modes
  - `VivaMode`: PRACTICE, TIMED, ADAPTIVE, MOCK, RESEARCH
  - `VivaState`: Session lifecycle states

- **adaptive_questioner.py**
  - `AdaptiveQuestioner`: Generates questions adaptively
  - `Question`, `Answer`: Models for Q&A
  - `QuestionDifficulty`: Difficulty scaling
  - `QuestionType`: Multiple choice, code, essay, etc.
  - `EmotionalState`: Emotion-aware adaptation

**Usage:**
```python
from flashcard_system.viva import VivaSession, SessionConfig

config = SessionConfig(
    mode=VivaMode.ADAPTIVE,
    duration_minutes=30,
    initial_difficulty=QuestionDifficulty.MEDIUM
)
session = VivaSession(config=config)
```

---

### `formatters/` - Response Formatting
**Purpose:** Format and style output content

**Files:**
- **code_formatter.py**
  - `CodeFormatter`: Formats code snippets
  - `SyntaxHighlighter`: Add syntax highlighting
  - `CodeLanguage`: Supported languages

**Usage:**
```python
from flashcard_system.formatters import CodeFormatter

formatter = CodeFormatter()
formatted = formatter.format_code(code, language="python")
```

---

## Data Flow

### Creating & Reviewing Flashcards

```
User Input
    ↓
[API: flashcard_controller.py]
    ↓
    ├─→ [core: generator.py] Generate cards
    ├─→ [core: spaced_repetition.py] Schedule reviews
    └─→ Save to storage
    ↓
Database/Files
```

### Uploading Materials

```
Upload Document
    ↓
[API: upload endpoint]
    ↓
[scanner: subject_scanner.py] Process material
    ↓
[core: generator.py] Generate flashcards
    ↓
Vector DB + Storage
```

### Reviewing & Analytics

```
User Reviews Card
    ↓
[API: review endpoint]
    ↓
[core: spaced_repetition.py] Calculate schedule
    ↓
[analytics: learning_patterns.py] Update patterns
    ↓
Storage + Display insights
```

### Viva Sessions

```
Start Viva
    ↓
[viva: viva_session.py] Initialize session
    ↓
[viva: adaptive_questioner.py] Generate question
    ↓
User Responds
    ↓
[viva: adaptive_questioner.py] Evaluate answer
    ↓
[viva: viva_session.py] Adapt difficulty
    ↓
Repeat or End
```

---

## Import Examples

### From Main Application

```python
# Core functionality
from flashcard_system.core import (
    FlashcardGenerator,
    Flashcard,
    SpacedRepetition
)

# API integration
from flashcard_system.api import router as flashcard_router

# Analytics
from flashcard_system.analytics import LearningPatterns

# Viva exam
from flashcard_system.viva import VivaSession, SessionConfig

# Scanner
from flashcard_system.scanner import SubjectScanner
```

### From FastAPI Application

```python
from fastapi import FastAPI
from flashcard_system.api import router

app = FastAPI()
app.include_router(router, prefix="/api/flashcards")
```

---

## Configuration

Each module supports configuration objects:

```python
# Generator config
generator_config = {
    'model': 'ollama',
    'temperature': 0.7,
    'max_cards': 20
}

# Spaced Repetition config
sr_config = {
    'initial_ease_factor': 2.5,
    'easy_bonus': 1.3,
    'hard_penalty': 0.6
}

# Viva Session config
viva_config = SessionConfig(
    mode=VivaMode.ADAPTIVE,
    duration_minutes=45,
    passing_score=70.0
)
```

---

## Original Locations (for Reference)

These folders still exist but are now superseded:

| Original | New Location |
|----------|--------------|
| `adaptive_learning/flashcards/` | `flashcard_system/core/` |
| `adaptive_learning/api/flashcard_controller.py` | `flashcard_system/api/` |
| `adaptive_learning/scanner/` | `flashcard_system/scanner/` |
| `adaptive_learning/analytics/` | `flashcard_system/analytics/` |
| `adaptive_learning/viva_engine/` | `flashcard_system/viva/` |
| `adaptive_learning/formatters/` | `flashcard_system/formatters/` |

**Next Steps:** Update imports in main application to use new paths.

---

## Adding New Features

### Adding a new formatter component:
```python
# flashcard_system/formatters/latex_formatter.py
class LatexFormatter:
    def format_equation(self, equation: str) -> str:
        pass
```

Then update `formatters/__init__.py`:
```python
from .latex_formatter import LatexFormatter
__all__ = [..., 'LatexFormatter']
```

### Adding a storage implementation:
```python
# flashcard_system/storage/mongodb_storage.py
class MongoDBStorage:
    async def save_card(self, card: Flashcard) -> str:
        pass
```

---

## Benefits of This Organization

✅ **Single Location**: All flashcard code in one folder
✅ **Clear Separation**: Core logic, API, Analytics separated
✅ **Easy Navigation**: Logical folder structure by feature
✅ **Scalable**: Easy to add new modules (storage, data_models, utils)
✅ **Maintainable**: Group related code together
✅ **Documented**: Each module has clear purpose
✅ **Testable**: Easy to write unit tests per module
✅ **Reusable**: Can import from other parts of app easily

---

## Next Steps

1. Update imports in `main.py` to use new paths
2. Update imports in `ai_brain.py` and other dependent modules
3. Remove old import paths from `adaptive_learning/`
4. Create tests in `flashcard_system/tests/`
5. Update frontend imports if needed
6. Document API changes in documentation

---

*Last Updated: March 8, 2026*
