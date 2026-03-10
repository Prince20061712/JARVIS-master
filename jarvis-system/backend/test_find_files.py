import os
from pathlib import Path
import sys

# Add backend dir to sys.path
sys.path.append("/Users/princegupta09372gmail.com/Downloads/JARVIS-master-main/jarvis-system/backend")

from flashcard_system.scanner.subject_scanner import SubjectScanner

scanner = SubjectScanner(root_dir=Path("/Users/princegupta09372gmail.com/Downloads/JARVIS-master-main/jarvis-system/backend/data/subjects"))
print("Scanner root:", scanner.root_dir)
subject_dir = scanner.root_dir / "Computer networks"
files = list(subject_dir.rglob('*'))
print(f"Files found: {files}")
