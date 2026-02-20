from typing import Dict, Any, List, Optional
import re
from utils.logger import logger

class CodeFormatter:
    """
    Formats programming answers with syntax highlighting, comments, and complexity analysis.
    Supports Python, C++, and Java.
    """
    def __init__(self):
        self.supported_languages = ["python", "cpp", "java", "javascript"]

    def format_code(self, code: str, language: str = "python", comments: Optional[Dict[int, str]] = None) -> str:
        """Wraps code in markdown blocks and optionally injects comments at specific lines."""
        lines = code.splitlines()
        if comments:
            new_lines = []
            for i, line in enumerate(lines, 1):
                new_lines.append(line)
                if i in comments:
                    comment_prefix = "#" if language in ["python", "bash"] else "//"
                    new_lines.append(f"    {comment_prefix} {comments[i]}")
            code = "\n".join(new_lines)
            
        return f"```{language}\n{code}\n```"

    def add_comments(self, code: str, logic_explanation: List[str]) -> str:
        """Attempts to inject logic explanations as block comments at the top."""
        comment_block = '"""\n' + "\n".join(logic_explanation) + '\n"""\n'
        return comment_block + code

    def explain_code(self, code: str) -> str:
        """Generates a textual breakdown of the code's logic."""
        # Simple heuristic: count loops and conditionals
        loops = len(re.findall(r'\b(for|while)\b', code))
        ifs = len(re.findall(r'\bif\b', code))
        
        explanation = f"This code uses {loops} loop(s) and {ifs} conditional statement(s) to achieve the result.\n"
        return explanation

    def analyze_complexity(self, code: str) -> Dict[str, str]:
        """Naively estimates time and space complexity."""
        # Extremely basic heuristic
        if "for" in code and "for" in code.split("for", 1)[1]: # nested
            time = "O(n^2)"
        elif "for" in code or "while" in code:
            time = "O(n)"
        else:
            time = "O(1)"
            
        return {
            "time_complexity": time,
            "space_complexity": "O(1) [Default]"
        }
