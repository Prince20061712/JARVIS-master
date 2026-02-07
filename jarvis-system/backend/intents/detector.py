from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import re
import logging
from utils.logger import logger

@dataclass
class Intent:
    type: str 
    name: str 
    confidence: float
    entities: Dict[str, Any]
    suggested_handler: str

class IntentDetector:
    def __init__(self):
        self.system_patterns = [
            (r"open\s+(.*)", "open_app", "system"),
            (r"launch\s+(.*)", "launch_app", "system"),
            (r"search\s+for\s+(.*)", "web_search", "system"),
            (r"play\s+(.*)", "play_media", "system"),
            (r"pause", "pause_media", "system"),
            (r"shutdown", "shutdown_system", "system"),
            (r"restart", "restart_system", "system"),
            (r"system\s+info", "system_info", "system"),
        ]
        
        self.knowledge_patterns = [
            (r"what\s+is\s+(.*)", "definition", "knowledge"),
            (r"who\s+is\s+(.*)", "biography", "knowledge"),
            (r"how\s+to\s+(.*)", "howto", "knowledge"),
            (r"explain\s+(.*)", "explanation", "knowledge"),
        ]

    def detect(self, text: str) -> Intent:
        text = text.lower().strip()
        
        # 1. System Commands
        for pattern, intent_name, handler in self.system_patterns:
            match = re.search(pattern, text)
            if match:
                entities = {"target": match.group(1)} if match.groups() else {}
                return Intent(
                    type="system",
                    name=intent_name,
                    confidence=0.95,
                    entities=entities,
                    suggested_handler=handler
                )

        # 2. Knowledge
        for pattern, intent_name, handler in self.knowledge_patterns:
            match = re.search(pattern, text)
            if match:
                entities = {"query": match.group(1)} if match.groups() else {}
                return Intent(
                    type="knowledge",
                    name=intent_name,
                    confidence=0.9,
                    entities=entities,
                    suggested_handler=handler
                )
        
        # 3. Fallback to Chat
        return Intent(
            type="chat",
            name="conversation",
            confidence=0.5,
            entities={"text": text},
            suggested_handler="chat"
        )
