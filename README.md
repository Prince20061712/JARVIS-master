# JARVIS - AI Voice Assistant System

A comprehensive, multi-modal AI voice assistant designed to emulate the capabilities of Tony Stark's JARVIS. Built with Python and React, it features advanced conversational agents, system automation, media management, and intelligent context processing, seamlessly integrated into macOS.

## 🚀 Features

* **Multi-Modal Interaction:** Communicate via text, voice, or rich UI elements.
* **Intelligent AI Brain:** Uses Ollama and modular AI systems for conversational responses, problem-solving, and reasoning. 
* **Seamless Media Control:** Deep integration with Spotify, YouTube, and volume controls for unified media experiences.
* **Mac Automation & Toolset:** Take screenshots, create code files, open URLs or desktop apps, and perform complex browser searches directly via natural language.
* **Advanced Audio Management:** Priority-queued text-to-speech with localized sound caching and multiple TTS provider fallbacks (Edge, pyttsx3, ElevenLabs, Azure, etc.).
* **Flashcard & Learning System:** Upload materials for an AI-guided viva and study environment.

## 🛠 Tech Stack

* **Backend:** Python 3.14, FastAPI
* **Frontend:** React, TypeScript, Vite, TailwindCSS
* **AI & NLP:** Ollama (Local LLM), SpeechRecognition, LangChain
* **Services:** PyAudio, pynput, Edge-TTS, and more.

## ⚙️ Getting Started

### Prerequisites

* macOS
* Python 3.14+
* Node.js & npm
* [Ollama](https://ollama.ai/) installed locally (Recommended models: `llama3`, `mistral`)

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd JARVIS-master-main
   ```

2. **Set up Python Virtual Environment:**
   Run the setup or manually create a venv inside `jarvis-system/backend`:
   ```bash
   cd jarvis-system/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install Frontend Dependencies:**
   ```bash
   cd jarvis-system/frontend
   npm install
   ```

4. **Environment Variables:**
   Copy `.env.example` to `.env` inside `jarvis-system/backend/` and configure your API keys if you plan to use premium models like ElevenLabs or Azure TTS.

## 🏃 Running JARVIS

You can launch JARVIS with the provided automated startup script at the root of the project:

```bash
./start_jarvis.sh
```

This script will automatically:
1. Activate the Python virtual environment.
2. Spin up the FastAPI backend on `http://localhost:8000`.
3. Launch the React Vite frontend on `http://localhost:5173`.
4. Open the Web UI in your default browser.

To stop JARVIS, simply press `Ctrl+C` in the terminal to gracefully exit both the frontend and backend processes.

## 📚 Project Structure

* `/jarvis-system/backend/`: Server, API routing, intelligence managers, and TTS systems.
* `/jarvis-system/frontend/`: React-based chat window, dashboard, and flashcard GUI.
* `/start_jarvis.sh`: Bootstrapper script.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🎬 Demo Videos

Watch the project in action using the demo videos included in the repository:

* [Sympathy Chat](./demo_video/Sympathy_chat.mp4)
* [Viva Chat](./demo_video/viva_chat.mp4)

> **Note:** Open these files with a media player that supports MP4 playback.

## 📝 License

This project is open-source and available under the MIT License.
