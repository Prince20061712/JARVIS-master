# 🗂️ FLASHCARD SYSTEM v2.0 - MODULE REFERENCE

## Quick Module Glossary

### 📌 core/ - Card Generation & Scheduling
**Location:** `flashcard_system/core/`  
**Files:** generator.py, spaced_repetition.py

**Classes:**
- `FlashcardGenerator` - Generate cards from text/documents
- `Flashcard` - Individual card model
- `FlashcardSet` - Collection of cards
- `SpacedRepetition` - SM-2 scheduling algorithm
- `CardProgress` - Card review tracking

**Use When:** You need to generate flashcards or schedule reviews

**Example:**
```python
from flashcard_system.core import FlashcardGenerator
gen = FlashcardGenerator()
cards = gen.generate_from_text("Quantum mechanics...")
```

---

### 🔌 api/ - REST API Endpoints
**Location:** `flashcard_system/api/`  
**Files:** flashcard_controller.py, viva_controller.py

**Routes:**
- Flashcard CRUD (20+ endpoints)
- Viva exam endpoints
- Progress tracking endpoints
- Statistics endpoints

**Use When:** You need HTTP API endpoints for your application

**Example:**
```python
from fastapi import FastAPI
from flashcard_system.api import router

app = FastAPI()
app.include_router(router, prefix="/api/flashcards")
```

---

### 📄 scanner/ - Material Processing
**Location:** `flashcard_system/scanner/`  
**Files:** subject_scanner.py

**Classes:**
- `SubjectScanner` - Scan folders for materials
- `MaterialProcessor` - Extract text from documents

**Supported Formats:** PDF, DOCX, TXT, MD, PPT

**Use When:** You need to process uploaded documents

**Example:**
```python
from flashcard_system.scanner import SubjectScanner
scanner = SubjectScanner("data/subjects")
materials = scanner.scan_subject("operating system")
```

---

### 📊 analytics/ - Learning Analytics
**Location:** `flashcard_system/analytics/`  
**Files:** learning_patterns.py, api_routes.py

**Classes:**
- `LearningPatterns` - Analyze learner progress
- `RetentionCurve` - Forgetting curve analysis
- `WeaknessAnalysis` - Identify weak areas

**Use When:** You need insights about learning progress

**Example:**
```python
from flashcard_system.analytics import LearningPatterns
analyzer = LearningPatterns()
patterns = analyzer.analyze_user_progress(user_id)
```

---

### 🎓 viva/ - Exam Sessions
**Location:** `flashcard_system/viva/`  
**Files:** viva_session.py, adaptive_questioner.py

**Classes:**
- `VivaSession` - Manage exam sessions
- `AdaptiveQuestioner` - Generate adaptive questions
- `SessionConfig` - Configure exam parameters
- `VivaMode` - Session modes (PRACTICE, TIMED, ADAPTIVE, MOCK, RESEARCH)

**Use When:** You need to conduct oral exams with adaptation

**Example:**
```python
from flashcard_system.viva import VivaSession, SessionConfig
config = SessionConfig(mode=VivaMode.ADAPTIVE)
viva = VivaSession(config=config)
```

---

### 🎨 formatters/ - Content Formatting
**Location:** `flashcard_system/formatters/`  
**Files:** code_formatter.py

**Classes:**
- `CodeFormatter` - Format and analyze code

**Use When:** You need to format code snippets

**Example:**
```python
from flashcard_system.formatters import CodeFormatter
formatter = CodeFormatter()
formatted = formatter.format_code(code)
```

---

## 🧠 ACADEMIC INTELLIGENCE SYSTEM

### 📝 response_formatter/ - Response Formatting & Evaluation
**Location:** `flashcard_system/academic/response_formatter/`  
**Files:** 5 Python modules

**Components:**

#### CodeFormatter
- **Use:** Format and analyze code
- **Classes:** CodeFormatter, CodeBlock, CodeAnalysis
- **Methods:** format_code(), analyze_syntax(), highlight()

#### DiagramGenerator  
- **Use:** Generate diagrams from descriptions
- **Classes:** DiagramGenerator, Diagram, DiagramType
- **Methods:** generate_ascii_diagram(), generate_visual()

#### DerivationBuilder
- **Use:** Build step-by-step derivations
- **Classes:** DerivationBuilder, DerivationStep
- **Methods:** build_derivation(), add_step(), validate()

#### MarksAllocator
- **Use:** Award marks based on answers
- **Classes:** MarksAllocator, MarksCriteria, AnswerQuality
- **Methods:** allocate_marks(), grade_answer()

#### NumericalSolver
- **Use:** Solve numerical problems step-by-step
- **Classes:** NumericalSolver, Solution, SolutionStep
- **Methods:** solve(), build_solution(), explain_steps()

**Example:**
```python
from flashcard_system.academic.response_formatter import (
    CodeFormatter, DerivationBuilder, MarksAllocator
)

formatter = CodeFormatter()
code = formatter.format_code("x=1+2")

builder = DerivationBuilder()
steps = builder.build_derivation("solve x² + 3x + 2 = 0")

allocator = MarksAllocator()
marks = allocator.allocate_marks(evaluation)
```

---

### 💡 concept_explainer/ - Concept Learning
**Location:** `flashcard_system/academic/concept_explainer/`  
**Files:** 4 Python modules

**Components:**

#### AnalogyGenerator
- **Use:** Create helpful analogies for concepts
- **Classes:** AnalogyGenerator, Analogy, AnalogyType
- **Methods:** generate_analogy(), find_analogies()

#### PrerequisiteCheck
- **Use:** Identify knowledge gaps
- **Classes:** PrerequisiteCheck, PrerequisiteGap, LearningPath
- **Methods:** find_gaps(), build_learning_path(), check_readiness()

#### StepByStepExplainer
- **Use:** Break down concepts into steps
- **Classes:** StepByStepExplainer, ExplanationStep, Difficulty
- **Methods:** explain(), add_step(), set_depth()

#### Visualization
- **Use:** Create visual representations
- **Classes:** Visualization, VisualAsset, VisualizationType
- **Methods:** generate_visualization(), create_diagram(), render()

**Example:**
```python
from flashcard_system.academic.concept_explainer import (
    AnalogyGenerator, PrerequisiteCheck, StepByStepExplainer
)

# Create analogy
gen = AnalogyGenerator()
analogy = gen.generate_analogy("Recursion")
# → "Recursion is like Russian nesting dolls..."

# Check prerequisites
checker = PrerequisiteCheck()
gaps = checker.find_gaps(user_id, "Binary Trees")
# → Identifies missing knowledge

# Step-by-step explanation
explainer = StepByStepExplainer()
steps = explainer.explain("Quicksort", depth=5)
# → Detailed breakdown of algorithm
```

---

### 📋 exam_simulator/ - Exam & Assessment
**Location:** `flashcard_system/academic/exam_simulator/`  
**Files:** 3 Python modules

**Components:**

#### QuestionGenerator
- **Use:** Generate exam questions intelligently
- **Classes:** QuestionGenerator, Question, QuestionDifficulty
- **Methods:** generate_questions(), create_question(), set_difficulty()

#### AnswerEvaluator
- **Use:** Evaluate and score answers
- **Classes:** AnswerEvaluator, EvaluationResult, Feedback
- **Methods:** evaluate(), score_answer(), generate_feedback()

#### TimeManager
- **Use:** Manage exam timing
- **Classes:** TimeManager, TimeAllocation, TimingStrategy
- **Methods:** allocate_time(), track_time(), suggest_pace()

**Example:**
```python
from flashcard_system.academic.exam_simulator import (
    QuestionGenerator, AnswerEvaluator, TimeManager
)

# Generate questions
q_gen = QuestionGenerator()
questions = q_gen.generate_questions("Math", count=10, difficulty="HARD")

# Allocate time
timer = TimeManager()
allocation = timer.allocate_time(questions)

# Evaluate answered
evaluator = AnswerEvaluator()
for q, answer in answers:
    result = evaluator.evaluate(q, answer)
    feedback = result.feedback
```

---

### 👁️ vision/ - Handwriting & OCR
**Location:** `flashcard_system/vision/`  
**Files:** hand_drawing.py

**Classes:**
- `HandwritingRecognizer` - Recognize handwritten text
- `HandwritingAnalyzer` - Analyze writing characteristics
- `StrokeData` - Extract stroke information
- `DrawingAnalysis` - Analyze drawings/diagrams

**Supported:**
- Handwritten text recognition
- Mathematical notation
- Cursive and print
- Multiple scripts

**Example:**
```python
from flashcard_system.vision import HandwritingRecognizer

recognizer = HandwritingRecognizer()
text = recognizer.recognize_from_image("handwritten.jpg")
# → "Binary search algorithm..."

analysis = recognizer.analyze_handwriting(image)
# → Quality metrics, confidence scores
```

---

### ⚡ websocket/ - Real-time Communication
**Location:** `flashcard_system/websocket/`  
**Files:** events.py, handlers.py

**Classes:**
- `WSEvent` - WebSocket event definition
- `EventType` - Event type enumeration
- `EventHandler` - Handle specific events
- `ConnectionManager` - Manage connections

**Features:**
- Real-time notifications
- Event broadcasting
- Connection management
- Error handling

**Example:**
```python
from flashcard_system.websocket import WSEvent, EventType

# Send event
event = WSEvent(
    type=EventType.CARD_ANSWERED,
    data={"card_id": "123", "quality": 4}
)
await manager.broadcast(event)

# Real-time updates sent to connected clients
```

---

## 🏗️ Infrastructure Modules

### 📋 data_models/
**Location:** `flashcard_system/data_models/`

Purpose: Centralized data models  
Status: Ready for expansion  
Use When: You need shared data structures

---

### 💾 storage/
**Location:** `flashcard_system/storage/`

Purpose: Persistence implementations  
Status: Ready for expansion  
Use When: You need custom storage backends

---

### 🛠️ utils/
**Location:** `flashcard_system/utils/`

Purpose: Helper utilities  
Status: Ready for expansion  
Use When: You need shared utility functions

---

## 🔗 Import Shortcuts

### Import Everything
```python
from flashcard_system import *
```

### Import by Component
```python
# Learning
from flashcard_system.core import FlashcardGenerator, SpacedRepetition

# Assessment
from flashcard_system.academic.exam_simulator import (
    QuestionGenerator, AnswerEvaluator
)

# Teaching
from flashcard_system.academic.concept_explainer import AnalogyGenerator

# Processing
from flashcard_system.vision import HandwritingRecognizer
from flashcard_system.scanner import SubjectScanner

# Exams
from flashcard_system.viva import VivaSession

# Analytics
from flashcard_system.analytics import LearningPatterns

# Real-time
from flashcard_system.websocket import WSEvent
```

### Import by Category
```python
# All academic tools
from flashcard_system.academic import *

# All learning analytics
from flashcard_system.analytics import *
```

---

## 📚 When to Use Each Module

| Task | Module | Class |
|------|--------|-------|
| Generate cards | core | FlashcardGenerator |
| Schedule reviews | core | SpacedRepetition |
| REST API | api | router |
| Process materials | scanner | SubjectScanner |
| Learning insights | analytics | LearningPatterns |
| Oral exams | viva | VivaSession |
| Format code | formatters | CodeFormatter |
| *Generate derivations* | academic | DerivationBuilder |
| *Create analogies* | academic | AnalogyGenerator |
| *Generate questions* | academic | QuestionGenerator |
| *Evaluate answers* | academic | AnswerEvaluator |
| *Recognize handwriting* | vision | HandwritingRecognizer |
| *Real-time updates* | websocket | ConnectionManager |

(*New in v2.0)

---

## 🚀 Module Dependency Tree

```
flashcard_system/
│
├── core/
│   ├── generator.py (depends: LLM, DB)
│   └── spaced_repetition.py (depends: DB)
│
├── api/
│   ├── flashcard_controller.py (depends: core, analytics)
│   └── viva_controller.py (depends: viva)
│
├── scanner/
│   └── subject_scanner.py (depends: Document libs)
│
├── analytics/
│   └── learning_patterns.py (depends: core, DB)
│
├── viva/
│   ├── viva_session.py (depends: core, LLM)
│   └── adaptive_questioner.py (depends: LLM)
│
├── formatters/
│   └── code_formatter.py (independent)
│
├── academic/
│   ├── response_formatter/ (independent)
│   ├── concept_explainer/ (depends: LLM)
│   └── exam_simulator/ (depends: LLM)
│
├── vision/
│   └── hand_drawing.py (depends: OpenCV, OCR)
│
└── websocket/
    └── handlers.py (depends: FastAPI)
```

---

## 💡 Quick Lookup Table

**Looking for a specific feature?**

| I want to... | Go to... | Class |
|-------------|---------|-------|
| Create flashcards | `core/` | FlashcardGenerator |
| Track card progress | `core/` | SpacedRepetition |
| Analyze learning | `analytics/` | LearningPatterns |
| Give oral exam | `viva/` | VivaSession |
| Format code answers | `formatters/` | CodeFormatter |
| **Explain concepts** | **academic/concept_explainer/** | **StepByStepExplainer** |
| **Grade answers** | **academic/response_formatter/** | **MarksAllocator** |
| **Generate exam Qs** | **academic/exam_simulator/** | **QuestionGenerator** |
| **Recognize handwriting** | **vision/** | **HandwritingRecognizer** |
| **Send live updates** | **websocket/** | **ConnectionManager** |
| **Expose via REST** | **api/** | **router** |
| **Extract from PDFs** | **scanner/** | **MaterialProcessor** |

---

## 🔍 Module Statistics

| Module | Files | Size | Functions | Classes |
|--------|-------|------|-----------|---------|
| core | 2 | 82 KB | 30+ | 5 |
| api | 2 | 90 KB | 50+ | 10 |
| analytics | 2 | 63 KB | 25+ | 5 |
| scanner | 1 | 6 KB | 5+ | 2 |
| viva | 2 | 72 KB | 40+ | 8 |
| formatters | 1 | 50 KB | 15+ | 3 |
| **academic** | **12** | **180 KB** | **80+** | **20** |
| **vision** | **1** | **56 KB** | **10+** | **3** |
| **websocket** | **2** | **10 KB** | **5+** | **2** |
| **TOTAL** | **25** | **609 KB** | **260+** | **58** |

---

*Module Reference v2.0 - March 8, 2026*
