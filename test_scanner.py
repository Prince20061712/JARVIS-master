#!/usr/bin/env python3
"""
Test script to check if SubjectScanner can find materials
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "jarvis-system" / "backend"
sys.path.insert(0, str(backend_dir))

from flashcard_system.scanner.subject_scanner import SubjectScanner

def test_scanner():
    scanner = SubjectScanner()
    
    subjects = ["operating system", "Computer networks"]
    
    for subject in subjects:
        print(f"Checking subject: {subject}")
        content = scanner.get_subject_content(subject)
        if content and content.strip():
            print(f"  ✅ Found content ({len(content)} chars)")
            print(f"  Preview: {content[:200]}...")
        else:
            print("  ❌ No content found"
if __name__ == "__main__":
    test_scanner()