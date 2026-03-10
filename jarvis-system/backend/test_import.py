import sys
from pathlib import Path

# Add backend dir to sys.path
sys.path.append("/Users/princegupta09372gmail.com/Downloads/JARVIS-master-main/jarvis-system/backend")

from flashcard_system.scanner.subject_scanner import SubjectScanner

scanner = SubjectScanner()
print(f"Scanner root: {scanner.root_dir.absolute()}")
content = scanner.get_subject_content("Computer networks")
print(f"Content length: {len(content)}")
