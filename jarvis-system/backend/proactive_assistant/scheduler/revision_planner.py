from datetime import datetime, timedelta
from typing import List, Dict, Any
import math
from utils.logger import logger

class RevisionPlanner:
    """
    Implements a spaced repetition scheduler (SM-2 logic) for optimized learning.
    Determines next review dates based on topic difficulty and student performance.
    """
    def __init__(self):
        self.item_states = {} # {topic_id: {'interval': int, 'easiness': float, 'repetition': int}}

    def optimize_review_date(self, topic_id: str, quality: int) -> datetime:
        """
        SM-2 Algorithm update.
        quality: 0 (forgot) to 5 (perfect recall).
        """
        state = self.item_states.get(topic_id, {'interval': 0, 'easiness': 2.5, 'repetition': 0})
        
        if quality >= 3:
            if state['repetition'] == 0:
                state['interval'] = 1
            elif state['repetition'] == 1:
                state['interval'] = 6
            else:
                state['interval'] = math.ceil(state['interval'] * state['easiness'])
            state['repetition'] += 1
        else:
            state['repetition'] = 0
            state['interval'] = 1

        state['easiness'] = max(1.3, state['easiness'] + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
        self.item_states[topic_id] = state
        
        return datetime.now() + timedelta(days=state['interval'])

    def create_schedule(self, topics: List[str]) -> Dict[str, datetime]:
        """Generates a batch of recommended review dates for new topics."""
        schedule = {}
        for topic in topics:
            # New topics start with 1-day interval
            schedule[topic] = datetime.now() + timedelta(days=1)
        return schedule

    def adjust_plan(self, topic_id: str, feedback: str):
        """Manually overrides or fine-tunes the interval based on student feedback."""
        if "too hard" in feedback.lower():
            state = self.item_states.get(topic_id, {'interval': 1, 'easiness': 2.5, 'repetition': 0})
            state['interval'] = max(1, state['interval'] // 2)
            self.item_states[topic_id] = state
            logger.info(f"Adjusted interval for {topic_id} due to difficulty feedback.")
