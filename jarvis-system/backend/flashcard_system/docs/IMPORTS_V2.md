# Updated Imports Guide - v2.0

With the integration of academic_qa and vision modules, here's how to import everything:

## Quick Reference - All Imports

```python
# ============ CORE FLASHCARD SYSTEM ============
from flashcard_system.core import (
    FlashcardGenerator,
    Flashcard,
    FlashcardSet,
    SpacedRepetition,
    CardProgress,
    ReviewLog,
)

# ============ ACADEMIC INTELLIGENCE ============
# Response Formatting
from flashcard_system.academic.response_formatter import (
    CodeFormatter,
    DiagramGenerator,
    DerivationBuilder,
    MarksAllocator,
    NumericalSolver,
)

# Concept Explanation
from flashcard_system.academic.concept_explainer import (
    AnalogyGenerator,
    PrerequisiteCheck,
    StepByStepExplainer,
    Visualization,
)

# Exam Simulation
from flashcard_system.academic.exam_simulator import (
    AnswerEvaluator,
    QuestionGenerator,
    TimeManager,
)

# ============ VISION & HANDWRITING ============
from flashcard_system.vision import (
    HandwritingRecognizer,
    HandwritingAnalyzer,
)

# ============ VIVA SESSIONS ============
from flashcard_system.viva import (
    VivaSession,
    AdaptiveQuestioner,
    SessionConfig,
    VivaMode,
)

# ============ ANALYTICS ============
from flashcard_system.analytics import (
    LearningPatterns,
    RetentionCurve,
    WeaknessAnalysis,
)

# ============ MATERIAL SCANNING ============
from flashcard_system.scanner import (
    SubjectScanner,
    MaterialProcessor,
)

# ============ REAL-TIME COMMUNICATION ============
from flashcard_system.websocket import (
    WSEvent,
    EventType,
    ConnectionManager,
)

# ============ API ROUTERS ============
from flashcard_system.api import router as flashcard_router
```

---

## Old vs New Import Paths

### Core Components

```python
# OLD
from adaptive_learning.flashcards.generator import FlashcardGenerator
from adaptive_learning.flashcards.spaced_repetition import SpacedRepetition

# NEW
from flashcard_system.core import FlashcardGenerator, SpacedRepetition
```

### Academic Components (PREVIOUSLY SCATTERED)

```python
# OLD (multiple locations)
from academic_qa.response_formatter.code_formatter import CodeFormatter
from academic_qa.concept_explainer.analogy_generator import AnalogyGenerator
from academic_qa.exam_simulator.question_generator import QuestionGenerator

# NEW (unified)
from flashcard_system.academic import (
    CodeFormatter,
    AnalogyGenerator,
    QuestionGenerator,
)

# OR with submodules
from flashcard_system.academic.response_formatter import CodeFormatter
from flashcard_system.academic.concept_explainer import AnalogyGenerator
from flashcard_system.academic.exam_simulator import QuestionGenerator
```

### Vision Components

```python
# OLD
from adaptive_learning.vision.hand_drawing import HandwritingRecognizer

# NEW
from flashcard_system.vision import HandwritingRecognizer
```

### Viva & Exams

```python
# OLD
from adaptive_learning.viva_engine.viva_session import VivaSession
from adaptive_learning.viva_engine.adaptive_questioner import AdaptiveQuestioner

# NEW
from flashcard_system.viva import VivaSession, AdaptiveQuestioner
```

### Analytics

```python
# OLD
from adaptive_learning.analytics.learning_patterns import LearningPatterns

# NEW
from flashcard_system.analytics import LearningPatterns
```

### Scanner

```python
# OLD
from adaptive_learning.scanner.subject_scanner import SubjectScanner

# NEW
from flashcard_system.scanner import SubjectScanner
```

### WebSocket

```python
# OLD
from api.websocket.handlers import ConnectionManager
from api.websocket.events import WSEvent

# NEW
from flashcard_system.websocket import WSEvent, ConnectionManager
```

---

## Unified Import Examples

### Example 1: Complete Study System

```python
from flashcard_system import (
    FlashcardGenerator,
    SpacedRepetition,
    LearningPatterns,
    VivaSession,
    SessionConfig,
)

# Generate flashcards
generator = FlashcardGenerator()
cards = generator.generate_from_text(material)

# Track progress
sr = SpacedRepetition()
next_date = sr.calculate_next_review(card_id, quality)

# Analyze learning
analyzer = LearningPatterns()
patterns = analyzer.analyze_user_progress(user_id)

# Conduct viva
config = SessionConfig(mode=VivaMode.ADAPTIVE)
viva = VivaSession(config=config)
```

### Example 2: Academic Intelligence

```python
from flashcard_system.academic import (
    CodeFormatter,
    AnalogyGenerator,
    AnswerEvaluator,
    QuestionGenerator,
)

# Format code
formatter = CodeFormatter()
formatted = formatter.format_code(code)

# Explain concepts
analogy_gen = AnalogyGenerator()
analogy = analogy_gen.generate_analogy(concept)

# Generate questions
q_gen = QuestionGenerator()
questions = q_gen.generate_questions(topic)

# Evaluate answers
evaluator = AnswerEvaluator()
result = evaluator.evaluate(question, answer)
```

### Example 3: Vision & Handwriting

```python
from flashcard_system.vision import HandwritingRecognizer
from flashcard_system.academic import AnswerEvaluator

# Recognize handwritten answer
recognizer = HandwritingRecognizer()
answer_text = recognizer.recognize_from_image("answer.jpg")

# Evaluate it
evaluator = AnswerEvaluator()
evaluation = evaluator.evaluate(question, answer_text)
```

### Example 4: FastAPI Integration

```python
from fastapi import FastAPI
from flashcard_system.api import router as flashcard_router
from flashcard_system.analytics.api_routes import router as analytics_router
from flashcard_system.websocket import websocket_endpoint

app = FastAPI()

# Include routers
app.include_router(flashcard_router, prefix="/api/flashcards")
app.include_router(analytics_router, prefix="/api/analytics")

# WebSocket
@app.websocket("/ws/{client_id}")
async def websocket_handler(websocket, client_id):
    await websocket_endpoint(websocket, client_id)
```

---

## Grouping by Use Case

### For Flashcard Management

```python
from flashcard_system.core import (
    FlashcardGenerator,
    SpacedRepetition,
    CardProgress,
)

from flashcard_system.scanner import SubjectScanner
```

### For Teaching & Explanation

```python
from flashcard_system.academic.concept_explainer import (
    AnalogyGenerator,
    PrerequisiteCheck,
    StepByStepExplainer,
    Visualization,
)
```

### For Exam & Assessment

```python
from flashcard_system.academic.exam_simulator import (
    QuestionGenerator,
    AnswerEvaluator,
    TimeManager,
)

from flashcard_system.viva import VivaSession
```

### For Student Work Analysis

```python
from flashcard_system.vision import HandwritingRecognizer

from flashcard_system.academic.response_formatter import (
    CodeFormatter,
    MarksAllocator,
)
```

### For Learning Analytics

```python
from flashcard_system.analytics import (
    LearningPatterns,
    RetentionCurve,
    WeaknessAnalysis,
)
```

### For Real-time Features

```python
from flashcard_system.websocket import (
    WSEvent,
    EventType,
    ConnectionManager,
)
```

---

## Files to Update in Your Codebase

### Priority 1: Immediate

- [x] `main.py` - Update all API router imports
- [x] `brain/ai_brain.py` - Update core component imports

### Priority 2: High

- [ ] Any files importing from `adaptive_learning.flashcards`
- [ ] Any files importing from `academic_qa` directly
- [ ] Any files using `adaptive_learning.api`

### Priority 3: Medium

- [ ] Test files
- [ ] Utility modules
- [ ] Dashboard/UI imports (if any)

### Priority 4: Low

- [ ] Documentation examples
- [ ] Notebook files
- [ ] Configuration files

---

## Bulk Find & Replace

### Find old imports

```bash
cd /backend
grep -r "from adaptive_learning" --include="*.py" | grep -v flashcard_system
grep -r "from academic_qa" --include="*.py" | grep -v flashcard_system
grep -r "from api.websocket" --include="*.py" | grep -v flashcard_system
```

### Safe replacements

```bash
# Flashcards -> Core
find . -name "*.py" -exec sed -i '' \
  's/from adaptive_learning\.flashcards/from flashcard_system.core/g' {} \;

# Academic_qa -> Academic
find . -name "*.py" -exec sed -i '' \
  's/from academic_qa/from flashcard_system.academic/g' {} \;

# Vision
find . -name "*.py" -exec sed -i '' \
  's/from adaptive_learning\.vision/from flashcard_system.vision/g' {} \;

# Viva
find . -name "*.py" -exec sed -i '' \
  's/from adaptive_learning\.viva_engine/from flashcard_system.viva/g' {} \;

# Analytics
find . -name "*.py" -exec sed -i '' \
  's/from adaptive_learning\.analytics/from flashcard_system.analytics/g' {} \;

# Scanner
find . -name "*.py" -exec sed -i '' \
  's/from adaptive_learning\.scanner/from flashcard_system.scanner/g' {} \;

# WebSocket
find . -name "*.py" -exec sed -i '' \
  's/from api\.websocket/from flashcard_system.websocket/g' {} \;
```

---

## Validation Script

Run this to verify all imports work:

```python
#!/usr/bin/env python3
"""Validate all flashcard system imports"""

try:
    print("Testing core imports...")
    from flashcard_system.core import FlashcardGenerator, SpacedRepetition
    
    print("Testing academic imports...")
    from flashcard_system.academic import (
        CodeFormatter, AnalogyGenerator, QuestionGenerator
    )
    
    print("Testing vision imports...")
    from flashcard_system.vision import HandwritingRecognizer
    
    print("Testing viva imports...")
    from flashcard_system.viva import VivaSession
    
    print("Testing analytics imports...")
    from flashcard_system.analytics import LearningPatterns
    
    print("Testing scanner imports...")
    from flashcard_system.scanner import SubjectScanner
    
    print("Testing websocket imports...")
    from flashcard_system.websocket import WSEvent
    
    print("Testing API imports...")
    from flashcard_system.api import router
    
    print("\n✅ All imports successful!")
    
except ImportError as e:
    print(f"\n❌ Import failed: {e}")
    exit(1)
```

---

## Migration Checklist

- [ ] Update main.py imports
- [ ] Update ai_brain.py imports
- [ ] Update all adaptive_learning imports
- [ ] Update all academic_qa imports
- [ ] Update all api.websocket imports
- [ ] Run validation script
- [ ] Run pytest
- [ ] Test in development
- [ ] Deploy

---

*v2.0 Import Guide - Updated March 8, 2026*
