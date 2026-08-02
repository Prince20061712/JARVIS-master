# JARVIS - Enterprise AI Voice Assistant

A comprehensive, enterprise-grade multi-modal AI voice assistant system designed for intelligent task automation and conversational intelligence. Built with Python and React, JARVIS delivers advanced conversational AI, system automation, media management, and context-aware processing with seamless macOS integration...

## 📋 Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [Hybrid AI Routing](#hybrid-ai-routing)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [API Usage](#api-usage)
- [Security Hardening](#security-hardening)
- [Project Architecture](#project-architecture)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## 📖 Overview

JARVIS is a sophisticated AI assistant system that combines state-of-the-art natural language processing, voice recognition, and system automation. The platform leverages a five-layer cognitive architecture to provide intelligent, context-aware responses and automated task execution across macOS environments.

## 🎯 Core Features

- **Multi-Modal Interaction:** Unified communication via voice, text, and graphical interfaces
- **Intelligent Conversational AI:** Advanced reasoning, problem-solving, and contextual understanding powered by fine-tuned language models
- **System Automation:** Programmatic control of system resources including screenshots, file creation, application launching, and web navigation
- **Media Integration:** Unified control and management of Spotify, YouTube, and system audio
- **Advanced Audio Processing:** Intelligent text-to-speech with emotional adaptation, priority queuing, and multi-provider fallback support
- **Learning & Development Tools:** Integrated flashcard system and AI-guided study environment for educational purposes

## ⚡ Hybrid AI Routing

JARVIS now supports a hybrid model router for faster and smarter responses.

- **COMMAND** queries route to system command execution (open, close, play, launch, search)
- **SIMPLE** queries route to local Ollama for offline and cost-free responses
- **FAST** queries route to Groq for low-latency output
- **COMPLEX** queries route to Gemini for deeper reasoning

Routing logic is implemented in:

- `jarvis-system/backend/services/llm/router.py`
- `jarvis-system/backend/services/llm/hybrid_brain.py`
- `jarvis-system/backend/services/llm/local_llm.py`
- `jarvis-system/backend/services/llm/groq_llm.py`
- `jarvis-system/backend/services/llm/gemini_llm.py`

## 🏗️ Technology Stack

### AI & Machine Learning
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language Models** | Ollama (Phi3/Mistral), Groq (Llama/Mixtral), Gemini 1.5 Flash | Hybrid routing for latency and reasoning quality |
| **Knowledge Retrieval** | RAG (Retrieval-Augmented Generation) | Context-aware academic and domain knowledge |
| **Cognitive Architecture** | 5-Layer Intelligence Model | Reactive, Cognitive, Metacognitive, Proactive, Creative layers |

### Speech & Audio Processing
| Component | Engine | Capabilities |
|-----------|--------|--------|
| **Speech-to-Text (STT)** | OpenAI Whisper, Google Speech API, Vosk, Sphinx | Multi-engine support with local and cloud options |
| **Text-to-Speech (TTS)** | Edge Neural Voices, ElevenLabs, pyttsx3 | Emotional synthesis, voice cloning, offline fallbacks |
| **Audio Management** | PyAudio | Real-time stream processing and priority-based queuing |

### Backend Infrastructure
- **Runtime:** Python 3.14
- **API Framework:** FastAPI (asynchronous, high-performance)
- **System Automation:** pynput, subprocess management
- **AI Orchestration:** LangChain, NumPy
- **Database:** Chroma Vector Store
- **Containerization:** Docker & Docker Compose

### Frontend Architecture
- **Framework:** React 18+ with TypeScript
- **Build Tool:** Vite (fast development and production builds)
- **Styling:** TailwindCSS
- **UI/UX:** Modern dashboard and real-time chat interface

## ⚡ Getting Started

### 💻 Compatibility & Hardware Notes
> **Built and Optimized for Apple Silicon (M-Series)**  
> This project was developed, tested, and optimized on a **MacBook Air M4**. 

* **macOS (Apple Silicon M1/M2/M3/M4):** Fully supported and highly recommended. Core inference (via Ollama), UI generation, and system-level automation run natively and smoothly on the unified memory architecture.
* **macOS (Intel):** Supported. Application will run fine, but local language model inference times will be noticeably slower without the Neural Engine.
* **Windows / Linux:** Partial support. The web frontend, NLP processing, and AI reasoning engine will work perfectly. However, **certain System Automation features** (like taking screenshots, opening specific apps, or controlling system volume) rely on macOS-specific commands (like AppleScript or native APIs). If you are using Windows or Linux, you will need to modify the system automation modules to use OS-specific equivalents (e.g., `pywin32` for Windows).

### System Requirements

| Requirement | Version | Notes |
|---|---|---|
| **Operating System** | macOS 10.15+ | M-Series Native (Tested on M4), Intel supported |
| **Python** | 3.10+ | Recommend 3.10 to 3.12. (Tested on 3.14) |
| **Node.js** | 18.0+ | Required for frontend development |
| **Ollama** | Latest | [Installation Guide](https://ollama.com/) |
| **Available Memory** | 8GB minimum | 16GB+ highly recommended for optimal performance with local LLMs |

### Installation

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd JARVIS-master
```

#### 2. Backend Setup
```bash
cd jarvis-system/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

#### 4. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Configure the following if using premium services:

- `LLM_MODEL` - Local Ollama model (recommended: `phi3` or `mistral`)
- `OLLAMA_BASE_URL` - Local Ollama endpoint (default: `http://localhost:11434`)
- `GROQ_API_KEY` - Required for FAST route
- `GEMINI_API_KEY` - Required for COMPLEX route
- `GROQ_MODEL` - Optional override (default: `llama-3.1-8b-instant`)
- `GEMINI_MODEL` - Optional override (default: `gemini-1.5-flash`)
- `OPENAI_API_KEY` - Optional for other modules

#### 5. Verify Installation
```bash
# Test Python environment
source jarvis-system/backend/venv/bin/activate
python3 -c "import fastapi; print('Backend dependencies OK')"

# Test Node.js installation
cd frontend
npm list | head -10
```

## 🚀 Running the Application

### Quick Start
Launch both backend and frontend services with the automated startup script:

```bash
./start_jarvis.sh
```

If you want a shorter command from the repository root, you can also run:

```bash
make start
```

This will automatically:
1. Activate the Python virtual environment
2. Start the FastAPI backend server (`http://localhost:8000`)
3. Start the React frontend development server (`http://localhost:5173`)
4. Open the web interface in your default browser

### Manual Startup

**Terminal 1 - Backend:**
```bash
cd jarvis-system/backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Stopping the Application
Press `Ctrl+C` in the terminal running `start_jarvis.sh` to gracefully shut down both services.

## 🌐 API Usage

### Hybrid Chat Streaming Endpoint

The root FastAPI app exposes a streaming endpoint:

- `POST /chat`

Request body:

```json
{
	"query": "quick summary of Fourier transform"
}
```

Response type:

- `text/event-stream` (Server-Sent Events)
- token chunks are streamed in real-time
- final event emits `[DONE]`

Example with curl:

```bash
curl -N -X POST http://localhost:8000/chat \
	-H "Content-Type: application/json" \
	-d '{"query":"latest AI news in 5 bullets"}'
```

### Route Selection Rules

- Contains `open`, `close`, `play`, `launch`, `search` -> COMMAND
- Fewer than 8 words -> SIMPLE
- Contains `quick`, `fast`, `latest`, `current` -> FAST
- Contains `explain`, `why`, `how`, `optimize`, `code`, `architecture` OR more than 15 words -> COMPLEX

### Response Cache

Hybrid responses are cached in-memory in the running backend process for repeated queries.

## 🔐 Security Hardening

### Pre-commit Secret Scan

A repo-managed pre-commit hook now blocks likely secrets before commit.

Enable it once per clone:

```bash
./scripts/setup-git-hooks.sh
```

This configures:

- hooks path: `.githooks/pre-commit`
- scanner: `scripts/security/check_secrets.py`

### Git Ignore Hardening

The repository now ignores:

- local env variants (`.env.local`, `.env.*.local`, `.envrc`)
- key and cert artifacts (`*.pem`, `*.key`, `*.p12`, `id_rsa`, `id_ed25519`)
- local runtime temp folders (`tmp/`, `temp/`, `temp_uploads/`)

Environment templates remain tracked:

- `.env.example`
- `jarvis-system/backend/.env.example`

## 📁 Project Architecture

```
JARVIS-master/
├── jarvis-system/
│   ├── backend/                    # Python FastAPI backend server
│   │   ├── ai/                     # AI & ML modules
│   │   ├── services/llm/           # Hybrid LLM routing and providers
│   │   ├── api/                    # REST & WebSocket endpoints
│   │   ├── brain/                  # Core AI brain logic
│   │   ├── context/                # Context awareness engine
│   │   ├── emotional_intelligence/ # EI modules and adapters
│   │   ├── memory_system/          # Memory management
│   │   ├── learning/               # Learning system components
│   │   ├── nlp/                    # Natural language processing
│   │   ├── config/                 # Configuration files
│   │   ├── data/                   # Data processing and storage
│   │   ├── ai_brain_data/          # AI training and cache data
│   │   ├── main.py                 # Application entry point
│   │   ├── requirements.txt        # Python dependencies
│   │   └── Dockerfile              # Container configuration
│   │
│   ├── frontend/                   # React TypeScript frontend
│   │   ├── src/                    # React components and logic
│   │   ├── package.json            # Node.js dependencies
│   │   ├── vite.config.ts          # Vite build configuration
│   │   └── tsconfig.json           # TypeScript configuration
│   │
│   └── data/                       # Persistent application data
│       ├── conversation_history.json
│       ├── jarvis_memory.json
│       └── metrics.json
│
├── start_jarvis.sh                 # Automated startup script
├── docker-compose.yml              # Docker orchestration
├── README.md                       # This file
└── LICENSE                         # License information
```

### Key Modules

| Module | Purpose | Technology |
|--------|---------|-----------|
| **AI Brain** | Core conversational and reasoning engine | LLM + RAG |
| **Context Awareness** | Environmental and user context management | Temporal analysis |
| **Emotional Intelligence** | Emotion detection and adaptive responses | NLP + Sentiment analysis |
| **Memory System** | Persistent and working memory management | Vector DB + JSON |
| **Learning System** | Educational content processing | Flashcard engine |
| **NLP Pipeline** | Text processing and understanding | NLTK + Custom |
| **API Layer** | RESTful and WebSocket communication | FastAPI |

## 📚 Documentation

For comprehensive documentation and usage guides, please refer to:

- [Comprehensive Module Inventory](./COMPREHENSIVE_MODULE_INVENTORY.md)
- [Backend README](./jarvis-system/backend/README.md)
- [Frontend README](./jarvis-system/frontend/README.md)

## 🎬 Demo & Examples

Live demonstrations of JARVIS capabilities:

| Demo | Description | Location |
|------|---|---|
| **Sympathy Chat** | Emotional intelligence in conversation | [View](./demo_video/Sympathy_chat.mp4) |
| **Viva Chat** | Interactive study and assessment | [View](./demo_video/viva_chat.mp4) |

## 🔧 Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError` for dependencies
```bash
# Solution: Reinstall dependencies in activated venv
source jarvis-system/backend/venv/bin/activate
pip install --upgrade -r requirements.txt
```

**Issue:** Frontend won't start
```bash
# Solution: Clear npm cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**Issue:** Ollama models not found
```bash
# Solution: Pull required models
ollama pull phi3
ollama pull mistral
```

For additional support, please review the application logs or check the troubleshooting section in the backend README.

## 🤝 Contributing

JARVIS is a proprietary project with controlled contributions. If you are an authorized contributor:

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Commit your changes: `git commit -am 'Add new feature'`
3. Push to the branch: `git push origin feature/your-feature-name`
4. Submit a Pull Request with detailed description

### Contribution Guidelines

- Ensure all code follows PEP 8 standards
- Write unit tests for new functionality
- Update documentation for API changes
- Test both backend and frontend thoroughly

## 📝 License

**PROPRIETARY LICENSE**

This project is proprietary software. While the code may be downloaded and viewed, any modification, redistribution, or publication without explicit written permission from Prince Gupta is strictly prohibited.

For full license terms, see the [LICENSE](LICENSE) file.

## 👨‍💼 Author

**Prince Gupta**

---

## 📊 System Requirements Summary

- **Supported Platforms:** macOS 10.15 and later
- **Minimum RAM:** 8GB (16GB recommended)
- **Storage:** 20GB available space
- **Network:** Internet connection for cloud-based models
- **Processor:** Intel Core i5 or Apple Silicon M1+

## 🔐 Security & Privacy

- All user data is stored locally by default
- API keys should be kept in `.env` and never committed to version control
- Use `.gitignore` to exclude sensitive files
- For cloud services, ensure proper authentication and token management

---

**Last Updated:** April 10, 2026
**Version:** 1.1.0
