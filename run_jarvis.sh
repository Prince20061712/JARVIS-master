#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for venv first
if [ -d ".venv" ]; then
    echo "Found .venv, using it."
    PYTHON_CMD=".venv/bin/python"
# Check for Python 3
elif command_exists python3; then
    PYTHON_CMD="python3"
elif command_exists python; then
    # Check if python is actually python 3
    if python --version 2>&1 | grep -q "Python 3"; then
        PYTHON_CMD="python"
    else
        echo "Error: Python 3 is required but not found."
        exit 1
    fi
else
    echo "Error: Python 3 is required but not found."
    exit 1
fi

echo "Using Python: $PYTHON_CMD"

# Install dependencies
echo "Installing dependencies..."
if [ -f "jarvis-system/backend/requirements.txt" ]; then
    $PYTHON_CMD -m pip install -r jarvis-system/backend/requirements.txt
else
    echo "Warning: requirements.txt not found in jarvis-system/backend/"
fi

# Run the application
echo "Starting JARVIS..."
if [ -f "jarvis-system/backend/main.py" ]; then
    # We need to run main.py from the jarvis-system/backend directory context or
    # ensure it can find its modules.
    # The import `from core.ai_brain import EnhancedAIBrain` inside main.py suggests
    # that `main.py` expects `core` to be importable.
    # `main.py` is in `backend/`. `core/` should be in `backend/` too (based on `from core...`).
    # Let's check if `core` exists in `backend`.
    
    # Wait, I should check if `core` exists.
    # Assuming standard structure, let's run it.
    # Setting PYTHONPATH to include the backend directory might be needed if running fro root.
    
    export PYTHONPATH=$PYTHONPATH:$(pwd)/jarvis-system/backend
    $PYTHON_CMD jarvis-system/backend/main.py
else
    echo "Error: main.py not found in jarvis-system/backend/"
    exit 1
fi
