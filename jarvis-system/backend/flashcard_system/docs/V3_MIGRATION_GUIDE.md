# v3.0 Migration Guide

## Overview

The v3.0 reorganization consolidates the Flashcard System into a production-ready, enterprise-grade architecture with clear separation of concerns and optimized module organization.

**Key Changes:**
- Created new infrastructure modules (`config/`, `storage/`, `utils/`)
- Added new helper modules (OCR processor, diagram analyzer, connection manager)
- Moved all documentation to organized `docs/` directory
- Created comprehensive test structure
- Updated all imports and module exports for v3.0

---

## What's New in v3.0

### 1. Configuration Management (`config/`)
**New Module for centralized application settings**

```python
from flashcard_system.config import Settings, setup_logging

# Load settings from environment
settings = Settings()
print(settings.ollama_model)  # "neural-chat"

# Configure logging
logger = setup_logging(log_level="INFO", log_dir="./logs")
```

**Files:**
- `settings.py` - Pydantic BaseSettings with environment variable support
- `logging_config.py` - Centralized logging configuration

**Benefits:**
- All settings in one place with environment variable support
- Type-safe configuration with Pydantic validation
- Easy to extend for new settings
- Supports `.env` files for local development

### 2. Storage & Persistence Layer (`storage/`)
**New abstraction for data access**

```python
from flashcard_system.storage import Repository, CacheManager
from sqlalchemy.orm import Session

# Use repository pattern
repo = Repository(session)
user_cards = repo.read_all(Flashcard, skip=0, limit=10)

# Use cache manager
cache = CacheManager(cache_dir="./cache")
cached_value = cache.get("key")
cache.set("key", value)
```

**Files:**
- `repository.py` - Repository pattern for database operations
- `cache_manager.py` - File-based and in-memory caching

**Benefits:**
- Unified data access interface
- Separation of database logic
- Built-in caching for embeddings and frequently accessed data
- Easy to test with mock repositories

### 3. Utilities & Helpers (`utils/`)
**Consolidated helper functions and constants**

```python
from flashcard_system.utils import (
    generate_id,
    generate_id,
    calculate_interval,
    CardValidator,
    Constants,
)

# Helper functions
user_id = generate_id()  # UUID
now_str = format_datetime(datetime.now())
next_interval = calculate_interval(current=1, ease=2.5, reps=2)

# Validators
validated_card = CardValidator(
    front="Question?",
    back="Answer",
    subject="Biology"
)

# Constants
from flashcard_system.utils import SM2_CONSTANTS
print(SM2_CONSTANTS["EASE_FACTOR_MIN"])  # 1.3
```

**Files:**
- `validators.py` - Pydantic validators for cards and reviews
- `helpers.py` - Common utility functions
- `constants.py` - Shared constants (SM-2 params, study limits, API constants)

**Benefits:**
- No more scattered utility functions
- Validated input across the system
- Centralized constants for easy configuration
- Type-safe with Pydantic validators

### 4. Enhanced Vision Module (`vision/`)
**New specialized processors for vision tasks**

```python
from flashcard_system.vision import OCRProcessor, DiagramAnalyzer

# OCR for text extraction
ocr = OCRProcessor()
text = ocr.extract_text("image.png")
structured = ocr.extract_structured_text("image.png")  # With positions

# Diagram analysis
analyzer = DiagramAnalyzer()
shapes = analyzer.detect_shapes("diagram.png")
equations = analyzer.detect_equation_structure("y = 2x + 5")
```

**New Classes:**
- `OCRProcessor` - Text extraction from images with confidence scoring
- `DiagramAnalyzer` - Geometric shape and diagram analysis

**Benefits:**
- Extracted from monolithic hand_drawing.py
- Focused, testable processors
- Reusable across different modules

### 5. WebSocket Connection Manager (`websocket/`)
**Centralized connection management**

```python
from flashcard_system.websocket import ConnectionManager

manager = ConnectionManager(max_connections=100)

async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket, user_id="user123")
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast({"msg": data}, user_id="user123")
    finally:
        manager.disconnect(websocket, "user123")
```

**Features:**
- Connection lifecycle management
- Broadcasting capabilities
- Connection statistics and monitoring
- Configurable limits and heartbeat intervals

---

## Structural Changes

### Before (v2.0)
```
flashcard_system/
├── core/
├── api/
├── academic/
├── vision/
├── viva/
├── websocket/          # Empty __init__.py
├── analytics/
├── scanner/
├── formatters/
├── data_models/
├── storage/            # Empty placeholder
├── utils/              # Empty placeholder
├── tests/              # Limited structure
├── ARCHITECTURE_V2.md  # Root level docs
├── README.md
└── [5 other .md files]
```

### After (v3.0)
```
flashcard_system/
├── core/
│   ├── models/         # NEW: Consolidated data models
│   ├── generator.py
│   └── spaced_repetition.py
├── api/
├── academic/
│   ├── response_formatter/
│   ├── concept_explainer/
│   └── exam_simulator/
├── vision/
│   ├── hand_drawing.py
│   ├── ocr_processor.py      # NEW: Specialized OCR
│   └── diagram_detector.py   # NEW: Diagram analysis
├── viva/
├── websocket/
│   ├── events.py
│   ├── handlers.py
│   └── connection_manager.py # NEW: Centralized management
├── analytics/
├── config/                   # NEW: Configuration
│   ├── settings.py          # NEW: Application settings
│   └── logging_config.py    # NEW: Logging setup
├── storage/                 # ENHANCED: Now fully implemented
│   ├── repository.py        # NEW: Repository pattern
│   └── cache_manager.py     # NEW: Caching layer
├── utils/                   # ENHANCED: Now fully implemented
│   ├── validators.py        # NEW: Pydantic validators
│   ├── helpers.py           # NEW: Helper functions
│   └── constants.py         # NEW: Shared constants
├── tests/                   # ENHANCED: Full test structure
│   ├── test_api/
│   ├── test_core/
│   └── test_academic/
├── docs/                    # NEW: Organized documentation
│   ├── README.md
│   ├── ARCHITECTURE_V2.md
│   ├── MODULE_REFERENCE.md
│   └── [other docs...]
└── README.md               # UPDATED: v3.0 architecture
```

---

## Import Changes

### Before (v2.0)
```python
# Settings scattered across modules
# No centralized config management

# Utilities scattered
from flashcard_system.utils import helpers  # Not organized

# Storage layer minimal
# Cache management ad-hoc
```

### After (v3.0)
```python
# Configuration
from flashcard_system.config import Settings, setup_logging

# Storage & Persistence
from flashcard_system.storage import Repository, CacheManager

# Utilities organized
from flashcard_system.utils import (
    CardValidator, ReviewValidator,
    generate_id, format_datetime,
    SM2_CONSTANTS, STUDY_CONSTANTS
)

# Vision processing
from flashcard_system.vision import (
    HandDrawingRecognizer,
    OCRProcessor,          # NEW
    DiagramAnalyzer        # NEW
)

# WebSocket
from flashcard_system.websocket import (
    ConnectionManager,     # NEW: Proper implementation
    WebSocketEvent,
    EventType
)
```

---

## Migration Checklist

If upgrading from v2.0 to v3.0:

### Configuration
- [ ] Create `.env` file with environment variables
- [ ] Import `Settings` instead of hardcoded config
- [ ] Update logging initialization with `setup_logging()`

### Data Access
- [ ] Replace direct database operations with `Repository`
- [ ] Use `CacheManager` for caching embeddings
- [ ] Implement proper session management

### Utilities
- [ ] Replace custom validators with `CardValidator`, `ReviewValidator`
- [ ] Use unified constants from `utils/constants.py`
- [ ] Use helper functions from `utils/helpers.py`

### Vision Processing
- [ ] Use `OCRProcessor` for text extraction
- [ ] Use `DiagramAnalyzer` for shape/diagram analysis
- [ ] Keep `HandDrawingRecognizer` for sketch recognition

### WebSocket
- [ ] Use `ConnectionManager` for connection handling
- [ ] Ensure proper connection lifecycle with try/finally

### Testing
- [ ] Create test files in `tests/test_api/`, `tests/test_core/`, `tests/test_academic/`
- [ ] Add unit tests for new modules
- [ ] Use `Repository` in tests with mocked sessions

### Documentation
- [ ] Update internal documentation links
- [ ] Refer to `docs/` for architecture details
- [ ] Use `docs/MODULE_REFERENCE.md` for API reference

---

## Breaking Changes

### Module Structure
- Empty `utils/` and `storage/` directories are now fully implemented
- `websocket/__init__.py` now properly exports modules (was empty)
- New required modules: `config/`, new vision helpers

### Imports
- Configuration now through `Settings` class (environment-aware)
- Logging through centralized `setup_logging()` function
- Database operations through `Repository` pattern

### API
- `CardValidator` and `ReviewValidator` now required for validation
- Constants moved to `utils/constants.py`
- Helper functions organized in `utils/helpers.py`

### WebSocket
- Must use `ConnectionManager` for proper connection handling
- Connection manager replaces ad-hoc connection tracking

---

## Performance Improvements

### v3.0 Optimizations
1. **Caching Layer** - `CacheManager` with file + memory caching
2. **Repository Pattern** - Reduced boilerplate, easier optimization
3. **Configuration** - Single settings source, reduced repeated lookups
4. **Logging** - Centralized, efficient logging configuration
5. **modularization** - Better separation of concerns enables optimization

### Profiling Recommendations
```python
import time
from flashcard_system.config import settings
from flashcard_system.storage import CacheManager

# Cache expensive operations
cache = CacheManager()
start = time.time()
# ... operation ...
if not cache.get("key"):
    # Do expensive operation
    cache.set("key", result)
```

---

## Testing Updated System

### Run All Tests
```bash
pytest tests/ -v
```

### Test Specific Module
```bash
pytest tests/test_core/ -v
pytest tests/test_api/ -v
pytest tests/test_academic/ -v
```

### Example Test with New Structure
```python
import pytest
from flashcard_system.config import Settings
from flashcard_system.storage import Repository, CacheManager
from flashcard_system.utils import CardValidator

@pytest.fixture
def settings():
    return Settings()

@pytest.fixture
def cache_manager():
    return CacheManager()

def test_card_validator(settings, cache_manager):
    validated = CardValidator(
        front="Q?",
        back="A"
    )
    assert validated.front == "Q?"

@pytest.mark.asyncio
async def test_connection_manager():
    from flashcard_system.websocket import ConnectionManager
    manager = ConnectionManager()
    assert manager.get_connection_count() == 0
```

---

## FAQ

**Q: Do I need to update my code immediately?**
A: v3.0 is backward compatible for core functionality. Update gradually:
1. Import new configuration management
2. Add validators to input handling
3. Migrate database access to Repository pattern
4. Update tests with new structure

**Q: Can I still use the old import paths?**
A: Main classes are still exported from `flashcard_system/__init__.py`. It's recommended to use specific imports for clarity.

**Q: How do I configure the system?**
A: Use environment variables or create a `.env` file:
```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=neural-chat
LOG_LEVEL=INFO
```

**Q: Where do I write tests?**
A: Use the organized structure:
- API tests → `tests/test_api/`
- Core logic → `tests/test_core/`
- Academic features → `tests/test_academic/`

**Q: Is there a migration script?**
A: Manual migration is straightforward. Follow the Migration Checklist above. For large deployments, create custom migration scripts for your data access layer.

---

## Support

For detailed information:
- Architecture: See `docs/ARCHITECTURE_V2.md`
- API Reference: See `docs/MODULE_REFERENCE.md`
- Import Guide: See `docs/IMPORT_GUIDE.md`
- Main Documentation: See `docs/README.md`
