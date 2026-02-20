from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from utils.logger import logger

class ReminderSystem:
    """
    Handles proactive notifications for upcoming sessions, revision dates, or breaks.
    Supports context-aware triggers and delivery tracking.
    """
    def __init__(self):
        self.active_reminders = [] # List of {'id': str, 'trigger_time': datetime, 'message': str, 'context': str}

    def set_reminder(self, message: str, trigger_time: datetime, context: str = "general"):
        reminder = {
            "id": f"rem_{len(self.active_reminders)}",
            "trigger_time": trigger_time,
            "message": message,
            "context": context,
            "sent": False
        }
        self.active_reminders.append(reminder)
        logger.info(f"Reminder set for {trigger_time}: {message}")

    def check_conditions(self, current_time: datetime) -> List[Dict[str, Any]]:
        """Finds all reminders that are due and haven't been sent."""
        due = []
        for r in self.active_reminders:
            if not r['sent'] and current_time >= r['trigger_time']:
                r['sent'] = True
                due.append(r)
        return due

    def send_notification(self, reminder_id: str) -> bool:
        """Placeholder for actual notification delivery (Websocket/Email)."""
        logger.info(f"Notification triggered for {reminder_id}")
        return True

    def smart_delay(self, reminder_id: str, minutes: int = 15):
        """Snoozes a reminder if the user is currently focused or busy."""
        for r in self.active_reminders:
            if r['id'] == reminder_id:
                r['trigger_time'] += timedelta(minutes=minutes)
                r['sent'] = False
                logger.info(f"Reminder {reminder_id} snoozed by {minutes} mins.")
                break
