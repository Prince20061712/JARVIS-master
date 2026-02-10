#!/bin/bash
# Script to start JARVIS from the project root

# Navigate to backend directory
cd backend

# Install/Update dependencies (quietly)
echo "Checking dependencies..."
python3 -m pip install -r requirements.txt --quiet

# Run the main application
python3 main.py
