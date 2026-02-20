import json
import re
from typing import Dict, Any, List, Optional
from utils.logger import logger

class ResponseParser:
    """
    Parses and cleans LLM outputs to extract structured data, code, or math.
    """
    def __init__(self):
        pass

    def parse_json(self, text: str) -> Dict[str, Any]:
        """Attempts to extract a JSON block from free-form text."""
        try:
            # Look for everything between the first '{' and last '}'
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            return json.loads(text)
        except Exception:
            # Fallback if no JSON found
            return {"raw_text": text}

    def extract_code(self, text: str) -> List[str]:
        """Extracts all content within markdown code blocks."""
        # Finds ```language ... ```
        matches = re.findall(r'```(?:\w+)?\n(.*?)\n```', text, re.DOTALL)
        return matches

    def clean_response(self, text: str) -> str:
        """Removes common LLM fluff (e.g. 'Sure, I can help', 'Here is your answer')."""
        fluff_patterns = [
            r'^Sure,.*?\n',
            r'^Here is the.*?\n',
            r'^I have derived.*?\n',
            r'As an AI model,.*'
        ]
        cleaned = text
        for p in fluff_patterns:
            cleaned = re.sub(p, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        return cleaned.strip()

    def extract_equations(self, text: str) -> List[str]:
        """Extracts LaTeX math blocks ($$ ... $$)."""
        return re.findall(r'\$\$(.*?)\$\$', text, re.DOTALL)

    def validate_format(self, text: str, required_sections: List[str]) -> bool:
        """Checks if the LLM followed the requested structure (e.g. bolded sections)."""
        text_lower = text.lower()
        return all(section.lower() in text_lower for section in required_sections)
