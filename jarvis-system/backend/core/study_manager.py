import json
import datetime
import os
from pathlib import Path

class StudyManager:
    """Manages study sessions, flashcards, and analytics"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, "study_data.json")
        self._ensure_data_dir()
        self.data = self._load_data()
        
    def _ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
    def _load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "sessions": [],
            "total_focus_minutes": 0,
            "flashcards": [],
            "quizzes": [],
            "streak_days": 0,
            "last_study_date": None
        }
        
    def _save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
            
    def start_study_session(self, subject):
        """Start tracking a study session"""
        session = {
            "id": len(self.data["sessions"]) + 1,
            "subject": subject,
            "start_time": datetime.datetime.now().isoformat(),
            "end_time": None,
            "duration_minutes": 0,
            "notes": []
        }
        self.current_session = session
        return session
        
    def end_study_session(self):
        """End current session and update stats"""
        if hasattr(self, 'current_session') and self.current_session:
            end_time = datetime.datetime.now()
            start_time = datetime.datetime.fromisoformat(self.current_session["start_time"])
            duration = (end_time - start_time).seconds // 60
            
            self.current_session["end_time"] = end_time.isoformat()
            self.current_session["duration_minutes"] = duration
            
            self.data["sessions"].append(self.current_session)
            self.data["total_focus_minutes"] += duration
            
            # Update streak
            today = datetime.date.today().isoformat()
            if self.data["last_study_date"] != today:
                # Simple streak logic: if last date was yesterday, increment, else reset
                # For now just increment daily unique logins
                self.data["streak_days"] += 1
                self.data["last_study_date"] = today
                
            self._save_data()
            session_summary = self.current_session
            self.current_session = None
            return session_summary
        return None

    def create_flashcard(self, subject, question, answer):
        """Create a new flashcard"""
        card = {
            "id": len(self.data["flashcards"]) + 1,
            "subject": subject,
            "question": question,
            "answer": answer,
            "review_count": 0,
            "last_reviewed": None,
            "confidence_level": 0 # 0-5
        }
        self.data["flashcards"].append(card)
        self._save_data()
        return card
        
    def get_flashcards(self, subject=None):
        """Get flashcards, optionally filtered by subject"""
        if subject:
            return [c for c in self.data["flashcards"] if c["subject"].lower() == subject.lower()]
        return self.data["flashcards"]
        
    def get_analytics(self):
        """Get study analytics"""
        return {
            "total_minutes": self.data["total_focus_minutes"],
            "streak": self.data["streak_days"],
            "sessions_count": len(self.data["sessions"]),
            "cards_count": len(self.data["flashcards"])
        }
