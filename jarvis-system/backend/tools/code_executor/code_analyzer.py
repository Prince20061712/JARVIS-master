import re
from typing import Dict, Any, List, Optional
from utils.logger import logger

try:
    import radon.complexity as cc
except ImportError:
    cc = None

class CodeAnalyzer:
    """
    Analyzes student code for quality, complexity, and style.
    Uses static analysis heuristics and specialized tools.
    """
    def __init__(self):
        pass

    def analyze_complexity(self, code: str) -> Dict[str, Any]:
        """Calculates Cyclomatic Complexity."""
        if cc:
            try:
                results = cc.cc_visit(code)
                avg_complexity = sum(r.complexity for r in results) / len(results) if results else 1
                return {
                    "complexity_score": round(avg_complexity, 2),
                    "rating": self._get_complexity_rating(avg_complexity)
                }
            except Exception as e:
                logger.error(f"Radon analysis failed: {e}")
        
        # Heuristic fallback
        control_structures = len(re.findall(r'\b(if|for|while|elif|case|except)\b', code))
        return {
            "complexity_score": control_structures + 1,
            "rating": self._get_complexity_rating(control_structures + 1),
            "note": "Using heuristic fallback"
        }

    def check_style(self, code: str, language: str = "python") -> List[Dict[str, Any]]:
        """Checks for common style issues (PEP8 for Python)."""
        issues = []
        lines = code.splitlines()
        
        for i, line in enumerate(lines, 1):
            if len(line) > 88:
                issues.append({"line": i, "message": "Line too long (over 88 chars)"})
            if language == "python" and re.search(r'[^ ]:[^ ]', line) and not line.startswith("#"):
                # Basic check for lack of space around colons
                pass
                
        return issues

    def find_bugs(self, code: str) -> List[str]:
        """Scans for high-risk patterns like infinite loops or unsafe imports."""
        bugs = []
        if "while True" in code and "break" not in code:
            bugs.append("Potential infinite loop detected (while True without break).")
        if "eval(" in code or "exec(" in code:
            bugs.append("Use of unsafe functions (eval/exec) detected.")
        return bugs

    def get_metrics(self, code: str) -> Dict[str, int]:
        """Calculates basic code metrics (LOC, SLOC, Comment count)."""
        lines = code.splitlines()
        return {
            "loc": len(lines),
            "sloc": len([l for l in lines if l.strip() and not l.strip().startswith(("#", "//"))]),
            "comments": len([l for l in lines if l.strip().startswith(("#", "//"))])
        }

    def _get_complexity_rating(self, score: float) -> str:
        if score <= 5: return "Simple"
        if score <= 10: return "Moderate"
        if score <= 20: return "Complex"
        return "Highly Volatile"
