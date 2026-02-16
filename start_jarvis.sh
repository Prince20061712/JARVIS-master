#!/bin/bash

# JARVIS Startup Script

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping JARVIS..."
    # Kill all background jobs started by this script
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Trap SIGINT (Ctrl+C)
trap cleanup SIGINT

echo "🚀 Initializing JARVIS..."./start_jarvis.sh

# check if .venv exists
if [ -d ".venv" ]; then
    echo "🔵 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  .venv not found! Ensure you have set up the python environment."
fi

# Start Backend
echo "🧠 Starting Backend Server..."
cd jarvis-system/backend
# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ Error: jarvis-system/backend/main.py not found!"
    exit 1
fi
python3 main.py &
cd "$SCRIPT_DIR"

# Start Frontend
echo "💻 Starting Frontend Client..."
cd jarvis-system/frontend
npm run dev &
cd "$SCRIPT_DIR"

echo "✅ Services Started."
echo "   - Backend: http://localhost:8000"
echo "   - Frontend: http://localhost:5173"
echo "⏳ Waiting for services to handle requests..."

sleep 5

echo "🌍 Opening Browser..."
# Use 'open' for macOS, 'xdg-open' for Linux if needed (assuming Mac based on context)
open http://localhost:5173 2>/dev/null || xdg-open http://localhost:5173 2>/dev/null

echo "⌨️  Press Ctrl+C to stop JARVIS."

# Wait for alll background processes
wait
