# JARVIS Academic Copilot

An emotionally intelligent, syllabus-aware academic assistant for engineering students.

#### Features

- 📚 **Syllabus-aware RAG engine** for precise answers
- 🎯 **Exam-oriented response formatting** (2/5/10/15 marks)
- 🧠 **Emotional intelligence** with voice/text sentiment analysis
- 🤖 **Proactive learning suggestions** and revision planning
- 🔒 **Privacy-first, offline-first architecture**

## Quick Start

1. Clone repository
2. Install dependencies:
   ```bash
   pip install -r requirements/base.txt
   pip install -r requirements/rag.txt
   pip install -r requirements/emotion.txt
   pip install -r requirements/voice.txt
   ```
3. Set up configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your settings (Ollama URL, database paths, etc.)
   ```
4. Run with Docker:
   ```bash
   docker-compose up -d
   ```
5. Access API at http://localhost:8000/docs

## Development

Run tests:
```bash
pytest tests/ -v
```

Run with hot reload:
```bash
uvicorn main:app --reload
```

## Setup University Syllabus
Place syllabus PDFs in `data/raw/syllabus/`
Place textbooks in `data/raw/textbooks/`
Run setup script:
```bash
python scripts/setup_university.py --university MU --semester 3
```
