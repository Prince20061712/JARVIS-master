#!/bin/bash

# Navigate to script directory (project root)
cd "$(dirname "$0")"

# Check if frontend is built
if [ ! -d "jarvis-system/frontend/dist" ]; then
    echo "Frontend build missing. Building frontend..."
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        echo "Error: npm is not installed. Please install Node.js/npm to build the frontend."
        # Don't exit, just warn, maybe user doesn't need frontend immediately
    else
        cd jarvis-system/frontend
        
        # Install dependencies if missing
        if [ ! -d "node_modules" ]; then
            echo "Installing frontend dependencies..."
            npm install
        fi
        
        # Build frontend
        echo "Building React app..."
        npm run build
        
        # Go back to root
        cd ../..
    fi
fi

# Navigate to backend
cd jarvis-system/backend

# Install/Update backend dependencies (quietly)
echo "Checking backend dependencies..."
python3 -m pip install -r requirements.txt --quiet

# Download NLP data (TextBlob corpora)
echo "Checking NLP data..."
python3 -m textblob.download_corpora

# Run the main application
echo "Starting JARVIS..."
python3 main.py
