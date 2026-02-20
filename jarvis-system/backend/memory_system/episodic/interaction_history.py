import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from utils.logger import logger
from utils.helpers import sanitize_html

class InteractionHistory:
    """
    Maintains a detailed, query-level history of everything the student asks 
    and the AI's response, allowing for analytics and search.
    """
    def __init__(self, history_file: str = "data/user_data/learning_history/interactions.jsonl"):
        self.history_file = history_file
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

    def log_interaction(self, query: str, response: str, emotion: str, context: Dict[str, Any], tags: List[str] = None):
        """Append a single interaction to the JSONL history file."""
        interaction = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "query": sanitize_html(query),
            "response_length": len(response), # Complete response might be too bulky to store forever, storing length as proxy or could store snippet
            "emotion_detected": emotion,
            "context": context,
            "tags": tags or []
        }
        
        try:
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(interaction) + "\n")
            logger.debug(f"Logged interaction: {interaction['id']}")
        except Exception as e:
            logger.error(f"Failed to log interaction to history: {e}")

    def search_history(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Basic text search through past interactions."""
        if not os.path.exists(self.history_file):
            return []
            
        results = []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                for line in reversed(list(f)): # Read backwards roughly (requires reading all to memory or complex backward reading; keeping simple for now)
                    if not line.strip(): continue
                    record = json.loads(line)
                    if keyword.lower() in record.get("query", "").lower() or keyword in record.get("tags", []):
                        results.append(record)
                        if len(results) >= limit:
                            break
            return results
        except Exception as e:
            logger.error(f"Search history failed: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Calculates basic stats over the interaction history file."""
        if not os.path.exists(self.history_file):
            return {"total_interactions": 0, "emotions": {}}

        total = 0
        emotions = {}
        tags = {}
        
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    record = json.loads(line)
                    total += 1
                    
                    e = record.get("emotion_detected", "unknown")
                    emotions[e] = emotions.get(e, 0) + 1
                    
                    for t in record.get("tags", []):
                        tags[t] = tags.get(t, 0) + 1
                        
            return {
                "total_interactions": total,
                "emotion_breakdown": emotions,
                "top_tags": dict(sorted(tags.items(), key=lambda item: item[1], reverse=True)[:5])
            }
        except Exception as e:
            logger.error(f"Failed to calculate history statistics: {e}")
            return {"error": str(e)}

    def export_anonymized(self, export_path: str) -> bool:
        """Exports history without user-identifiable context for research/analysis."""
        if not os.path.exists(self.history_file):
            return False
            
        try:
            with open(self.history_file, "r", encoding="utf-8") as f_in, \
                 open(export_path, "w", encoding="utf-8") as f_out:
                for line in f_in:
                    if not line.strip(): continue
                    record = json.loads(line)
                    # Strip PII fields if they existed in context
                    record.pop("context", None) 
                    f_out.write(json.dumps(record) + "\n")
            return True
        except Exception as e:
            logger.error(f"Failed to export anonymized history: {e}")
            return False
