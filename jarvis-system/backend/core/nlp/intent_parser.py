from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import re

@dataclass
class Intent:
    type: str # 'system', 'knowledge', 'chat'
    name: str # 'open_app', 'ask_question', 'small_talk'
    confidence: float
    entities: Dict[str, Any]

class IntentParser:
    def __init__(self):
        # Compiled regex patterns for basic system commands
        self.system_patterns = [
            (r"open\s+(.*)", "open_app"),
            (r"close\s+(.*)", "close_app"),
            (r"search\s+for\s+(.*)", "search"),
            (r"turn\s+on\s+(.*)", "turn_on"),
            (r"turn\s+off\s+(.*)", "turn_off"),
        ]
        
        self.knowledge_patterns = [
            (r"what\s+is\s+(.*)", "definition"),
            (r"how\s+to\s+(.*)", "howto"),
            (r"explain\s+(.*)", "explanation"),
        ]

    def parse(self, text: str) -> Intent:
        text = text.lower().strip()
        
        # 1. Check System Patterns (High Priority)
        for pattern, intent_name in self.system_patterns:
            match = re.search(pattern, text)
            if match:
                return Intent(
                    type="system",
                    name=intent_name,
                    confidence=1.0,
                    entities={"target": match.group(1)}
                )

        # 2. Check Knowledge Patterns (Medium Priority)
        for pattern, intent_name in self.knowledge_patterns:
            match = re.search(pattern, text)
            if match:
                return Intent(
                    type="knowledge",
                    name=intent_name,
                    confidence=0.9,
                    entities={"query": match.group(1)}
                )

        # 3. Fallback / Chat (Low Priority)
        # TODO: Integrate ML/LLM here for intelligent classification
        return Intent(
            type="chat",
            name="conversation",
            confidence=0.5,
            entities={"text": text}
        )
