# JARVIS - Enterprise AI Voice Assistant

A comprehensive, enterprise-grade multi-modal AI voice assistant system designed for intelligent task automation and conversational intelligence. Built with Python and React, JARVIS delivers advanced conversational AI, system automation, media management, and context-aware processing with seamless macOS integration.

## 📋 Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
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

## 🏗️ Technology Stack

### AI & Machine Learning
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language Models** | Ollama (Llama 3.1, Mistral) | Core intelligence and reasoning engine |
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
- `ELEVENLABS_API_KEY` - Optional, for premium voice synthesis
- `AZURE_TTS_KEY` - Optional, for Azure Text-to-Speech
- `OPENAI_API_KEY` - Optional, for advanced features

#### 5. Verify Installation
```bash
# Test Python environment
source jarvis-system/backend/venv/bin/activate
python3 -c "import fastapi; print('Backend dependencies OK')"

# Test Node.js installation
cd jarvis-system/frontend
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
cd jarvis-system/frontend
npm run dev
```

### Stopping the Application
Press `Ctrl+C` in the terminal running `start_jarvis.sh` to gracefully shut down both services.

## 📁 Project Architecture

## 📁 Project Architecture

```
JARVIS-master/
├── jarvis-system/
│   ├── backend/                    # Python FastAPI backend server
│   │   ├── ai/                     # AI & ML modules
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
cd jarvis-system/frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**Issue:** Ollama models not found
```bash
# Solution: Pull required models
ollama pull llama3
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

**Last Updated:** March 27, 2026
**Version:** 1.0.0
