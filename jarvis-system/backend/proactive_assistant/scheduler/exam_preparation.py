from datetime import datetime, timedelta
from typing import List, Dict, Any
from utils.logger import logger

class ExamPreparation:
    """
    Creates intensive study plans leading up to university exams.
    Allocates time based on topic weightage and preparation gaps.
    """
    def __init__(self, exam_date: datetime):
        self.exam_date = exam_date
        self.study_plan = {}

    def create_study_plan(self, syllabus: Dict[str, List[str]], mastery_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Generates a day-by-day countdown schedule.
        Allocates more time to weak topics (low mastery).
        """
        days_left = (self.exam_date - datetime.now()).days
        if days_left <= 0:
            return {"error": "Exam date has passed or is today!"}

        plan = {}
        topics_to_cover = []
        for unit, topics in syllabus.items():
            for t in topics:
                mastery = mastery_data.get(t, 0.0)
                topics_to_cover.append({'name': t, 'priority': 1.0 - mastery})

        # Sort by priority (weakest first)
        topics_to_cover.sort(key=lambda x: x['priority'], reverse=True)
        
        # Simple allocation: distribute topics over available days
        for i, topic in enumerate(topics_to_cover):
            day_offset = i % days_left
            scheduled_date = (datetime.now() + timedelta(days=day_offset)).date().isoformat()
            if scheduled_date not in plan:
                plan[scheduled_date] = []
            plan[scheduled_date].append(topic['name'])

        self.study_plan = plan
        return plan

    def allocate_time(self, available_hours: float) -> Dict[str, float]:
        """Suggests hour distribution per topic for the current day."""
        today = datetime.now().date().isoformat()
        daily_topics = self.study_plan.get(today, [])
        if not daily_topics:
            return {}
            
        time_per_topic = available_hours / len(daily_topics)
        return {t: round(time_per_topic, 1) for t in daily_topics}

    def simulate_exam(self, topic: str) -> str:
        """Triggers a mock-test environment for a specific topic."""
        return f"Starting 60-minute mock test for {topic}. No external aids allowed!"
