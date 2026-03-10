import os
from pathlib import Path
import sys

# Add backend dir to sys.path
sys.path.append("/Users/princegupta09372gmail.com/Downloads/JARVIS-master-main/jarvis-system/backend")

from flashcard_system.scanner.subject_scanner import SubjectScanner

scanner = SubjectScanner(root_dir=Path("/Users/princegupta09372gmail.com/Downloads/JARVIS-master-main/jarvis-system/backend/data/subjects"))
print("Scanner root:", scanner.root_dir)
content = scanner.get_subject_content("Computer networks")
print(f"Content length for 'Computer networks': {len(content)}")
if not content.strip():
    print("Content is empty!")
else:
    print("Content found!")
