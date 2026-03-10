#!/usr/bin/env python3
"""
Script to ingest existing subject materials into RAG system
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "jarvis-system" / "backend"
sys.path.insert(0, str(backend_dir))

from brain.ai_brain import RAGAdapter

def ingest_materials():
    """Ingest all materials from subjects into RAG"""

    # Initialize RAG
    rag = RAGAdapter()

    # Subject directories
    subjects_dir = backend_dir / "data" / "subjects"

    if not subjects_dir.exists():
        print(f"Subjects directory not found: {subjects_dir}")
        return

    # Find all subject folders
    for subject_dir in subjects_dir.iterdir():
        if subject_dir.is_dir():
            subject_name = subject_dir.name
            print(f"Processing subject: {subject_name}")

            # Find all files in subject directory
            for file_path in subject_dir.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.txt', '.md', '.docx']:
                    print(f"  Ingesting: {file_path.name}")
                    try:
                        result = rag.ingest_document(str(file_path), subject_name)
                        print(f"    Result: {result}")
                    except Exception as e:
                        print(f"    Error: {e}")

if __name__ == "__main__":
    ingest_materials()