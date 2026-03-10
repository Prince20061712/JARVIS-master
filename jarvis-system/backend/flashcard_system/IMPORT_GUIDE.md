# Import Update Guide

This guide shows how to update imports across the codebase to use the new centralized `flashcard_system` folder.

## Summary of Changes

All flashcard-related imports should be updated to use the new unified structure:

```
OLD: from adaptive_learning.flashcards.generator import FlashcardGenerator
NEW: from flashcard_system.core import FlashcardGenerator

OLD: from adaptive_learning.api.flashcard_controller import router
NEW: from flashcard_system.api import router

OLD: from adaptive_learning.scanner.subject_scanner import SubjectScanner
NEW: from flashcard_system.scanner import SubjectScanner

OLD: from adaptive_learning.analytics.learning_patterns import LearningPatterns
NEW: from flashcard_system.analytics import LearningPatterns

OLD: from adaptive_learning.viva_engine.viva_session import VivaSession
NEW: from flashcard_system.viva import VivaSession
```

---

## Files That Need Import Updates

### 1. `main.py` - Main Application

**Current imports:**
```python
from adaptive_learning.api.flashcard_controller import router as flashcard_router
```

**Update to:**
```python
from flashcard_system.api import router as flashcard_router
```

**Lines to update:** Search for:
- `from adaptive_learning.api.flashcard_controller`
- `from adaptive_learning.flashcards`
- `from adaptive_learning.scanner`
- `from adaptive_learning.viva_engine`
- `from adaptive_learning.analytics`

---

### 2. `brain/ai_brain.py` - AI Brain Initialization

**Current imports:**
```python
from adaptive_learning.flashcards.generator import FlashcardGenerator
from adaptive_learning.flashcards.spaced_repetition import SpacedRepetition
```

**Update to:**
```python
from flashcard_system.core import FlashcardGenerator, SpacedRepetition
```

---

### 3. `managers/` - Screen Manager & Others

**Search and replace pattern:**
```python
# OLD
from adaptive_learning.scanner import SubjectScanner

# NEW
from flashcard_system.scanner import SubjectScanner
```

---

### 4. `services/` - Service Modules

**If any service imports flashcard modules:**
```python
# Replace all occurrences of:
# - adaptive_learning.flashcards
# - adaptive_learning.analytics
# - adaptive_learning.viva_engine
# With:
# - flashcard_system.core
# - flashcard_system.analytics
# - flashcard_system.viva
```

---

### 5. `frontend/src/` - Frontend Code

**If frontend imports backend modules (unlikely but check):**
```typescript
// OLD
import { flashcardService } from '../../api/services/flashcard_service'

// NEW (path adjustment)
import { flashcardService } from '../../..api/services/flashcard_service'
```

---

## Step-by-Step Update Process

### Step 1: Update main.py
```bash
# Find all flashcard imports
cd /backend
grep -n "from adaptive_learning\.\(flashcards\|api\|scanner\|analytics\|viva_engine\)" main.py
```

### Step 2: Update ai_brain.py
```bash
grep -n "from adaptive_learning" brain/ai_brain.py | grep -E "(flashcards|scanner|analytics|viva)"
```

### Step 3: Check all Python files
```bash
grep -r "from adaptive_learning" --include="*.py" | grep -E "(flashcards|scanner|analytics|viva_engine|api)"
```

### Step 4: Verify imports work
```bash
cd /backend
python3 -c "from flashcard_system.core import FlashcardGenerator; print('✅ Import successful')"
python3 -c "from flashcard_system.api import router; print('✅ Import successful')"
python3 -c "from flashcard_system.viva import VivaSession; print('✅ Import successful')"
```

---

## Common Import Patterns

### Pattern 1: Core Generation
```python
# OLD
from adaptive_learning.flashcards.generator import (
    FlashcardGenerator,
    Flashcard,
    FlashcardSet,
    TextProcessor
)

# NEW
from flashcard_system.core import (
    FlashcardGenerator,
    Flashcard,
    FlashcardSet,
    TextProcessor
)
```

### Pattern 2: API Router
```python
# OLD
from adaptive_learning.api.flashcard_controller import router

# NEW
from flashcard_system.api import router
```

### Pattern 3: Spaced Repetition
```python
# OLD
from adaptive_learning.flashcards.spaced_repetition import (
    SpacedRepetition,
    CardProgress,
    ReviewLog
)

# NEW
from flashcard_system.core import (
    SpacedRepetition,
    CardProgress,
    ReviewLog
)
```

### Pattern 4: Analytics
```python
# OLD
from adaptive_learning.analytics.learning_patterns import LearningPatterns

# NEW
from flashcard_system.analytics import LearningPatterns
```

### Pattern 5: Viva Sessions
```python
# OLD
from adaptive_learning.viva_engine.viva_session import VivaSession
from adaptive_learning.viva_engine.adaptive_questioner import AdaptiveQuestioner

# NEW
from flashcard_system.viva import VivaSession, AdaptiveQuestioner
```

### Pattern 6: Scanner
```python
# OLD
from adaptive_learning.scanner.subject_scanner import SubjectScanner

# NEW
from flashcard_system.scanner import SubjectScanner
```

---

## Testing Imports

After updating, test that imports work:

```python
#!/usr/bin/env python3
"""Test all flashcard system imports"""

from flashcard_system.core import (
    FlashcardGenerator,
    Flashcard,
    FlashcardSet,
    SpacedRepetition,
    CardProgress
)

from flashcard_system.api import router

from flashcard_system.scanner import SubjectScanner, MaterialProcessor

from flashcard_system.analytics import (
    LearningPatterns,
    RetentionCurve,
    WeaknessAnalysis
)

from flashcard_system.viva import (
    VivaSession,
    AdaptiveQuestioner,
    SessionConfig
)

from flashcard_system.formatters import CodeFormatter

print("✅ All imports successful!")
```

---

## Files to Update (Checklist)

- [ ] `main.py` - API router imports
- [ ] `brain/ai_brain.py` - Core component imports
- [ ] `config/__init__.py` - Configuration imports
- [ ] `tests/` - Test file imports
- [ ] `managers/*.py` - Any scanner usage
- [ ] `services/*.py` - Any service imports
- [ ] `pipeline/*.py` - Pipeline component imports
- [ ] Documentation files - Update code examples

---

## Backward Compatibility (Temporary)

If you want to maintain backward compatibility temporarily, you can create facade imports in the old locations:

```python
# In adaptive_learning/flashcards/__init__.py (if keeping for compatibility)
from flashcard_system.core import *

# In adaptive_learning/api/__init__.py (if keeping for compatibility)
from flashcard_system.api import *

# etc.
```

However, it's recommended to fully migrate to the new imports.

---

## Verification Checklist

After updating all imports:

✅ Run syntax check on all Python files
✅ Test imports with Python REPL
✅ Run FastAPI app and verify endpoints work
✅ Check that no modules import from old locations
✅ Verify AI brain initializes correctly
✅ Test flashcard generation
✅ Test viva session startup
✅ Test file uploads and scanner

---

## Quick Commands

### Find all old imports
```bash
cd /Users/princegupta09372gmail.com/Downloads/JARVIS-master-main/jarvis-system/backend
grep -r "from adaptive_learning" --include="*.py" | grep -E "(flashcards|scanner|analytics|viva_engine|api)" | grep -v flashcard_system
```

### Replace pattern (use with caution)
```bash
# Replace flashcards imports
find . -name "*.py" -exec sed -i '' 's/from adaptive_learning.flashcards/from flashcard_system.core/g' {} \;

# Replace api imports
find . -name "*.py" -exec sed -i '' 's/from adaptive_learning.api.flashcard_controller/from flashcard_system.api/g' {} \;

# Replace scanner imports
find . -name "*.py" -exec sed -i '' 's/from adaptive_learning.scanner/from flashcard_system.scanner/g' {} \;

# Replace analytics imports
find . -name "*.py" -exec sed -i '' 's/from adaptive_learning.analytics/from flashcard_system.analytics/g' {} \;

# Replace viva imports
find . -name "*.py" -exec sed -i '' 's/from adaptive_learning.viva_engine/from flashcard_system.viva/g' {} \;
```

---

*Generated: March 8, 2026*
