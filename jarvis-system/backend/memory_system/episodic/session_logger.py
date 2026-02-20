import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from utils.logger import logger

class SessionLogger:
    """
    Tracks complete study sessions for episodic memory generation.
    """
    def __init__(self):
        self.active_session: Optional[Dict[str, Any]] = None
        self.completed_sessions: List[Dict[str, Any]] = []

    def start_session(self) -> str:
        """Starts a new study session."""
        if self.active_session:
            self.end_session()
            
        session_id = str(uuid.uuid4())
        self.active_session = {
            "session_id": session_id,
            "start_time": datetime.now(),
            "end_time": None,
            "topics_covered": set(),
            "events": []
        }
        logger.info(f"Started new session: {session_id}")
        return session_id

    def add_event(self, event_type: str, details: Dict[str, Any]):
        """Logs an event to the current active session."""
        if not self.active_session:
            logger.warning("Attempted to add event but no active session exists.")
            return

        self.active_session["events"].append({
            "timestamp": datetime.now(),
            "type": event_type,
            "details": details
        })
        
        # Track topics implicitly if present in events
        if "topic" in details:
            self.active_session["topics_covered"].add(details["topic"])

    def end_session(self) -> Optional[Dict[str, Any]]:
        """Ends the active session and generates a summary."""
        if not self.active_session:
            return None

        self.active_session["end_time"] = datetime.now()
        # Convert sets to lists for JSON serialization later if needed
        self.active_session["topics_covered"] = list(self.active_session["topics_covered"])
        
        # Calculate duration
        duration = self.active_session["end_time"] - self.active_session["start_time"]
        self.active_session["duration_seconds"] = duration.total_seconds()
        
        self.completed_sessions.append(self.active_session)
        
        completed_id = self.active_session["session_id"]
        logger.info(f"Ended session: {completed_id} (Duration: {duration.total_seconds()//60} mins)")
        
        summary = self._generate_summary(self.active_session)
        self.active_session = None
        return summary

    def _generate_summary(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a high-level summary of the session."""
        event_counts = {}
        for event in session_data["events"]:
            t = event["type"]
            event_counts[t] = event_counts.get(t, 0) + 1
            
        return {
            "session_id": session_data["session_id"],
            "duration_mins": round(session_data["duration_seconds"] / 60, 2),
            "topics": session_data["topics_covered"],
            "event_summary": event_counts
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        for sess in self.completed_sessions:
            if sess["session_id"] == session_id:
                return sess
        if self.active_session and self.active_session["session_id"] == session_id:
            return self.active_session
        return None
