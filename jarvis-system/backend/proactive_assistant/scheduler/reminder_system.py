"""
Reminder System Module - Enhanced version
Intelligent reminder system with context awareness, adaptive scheduling, and multi-channel notifications.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
import numpy as np
from collections import defaultdict
from dataclasses import dataclass, field
import json
from pathlib import Path
import asyncio
import hashlib
import random

logger = logging.getLogger(__name__)

class ReminderType(Enum):
    """Types of reminders."""
    TASK = "task"
    EVENT = "event"
    DEADLINE = "deadline"
    HABIT = "habit"
    WELLNESS = "wellness"
    LEARNING = "learning"
    SOCIAL = "social"
    APPOINTMENT = "appointment"
    BILL = "bill"
    CUSTOM = "custom"

class ReminderPriority(Enum):
    """Priority levels for reminders."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class ReminderStatus(Enum):
    """Status of reminders."""
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    COMPLETED = "completed"
    SNOOZED = "snoozed"
    CANCELLED = "cancelled"
    MISSED = "missed"

class NotificationChannel(Enum):
    """Notification delivery channels."""
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    DESKTOP = "desktop"
    VOICE = "voice"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"

@dataclass
class Reminder:
    """Data class for reminders."""
    reminder_id: str
    title: str
    description: str
    reminder_type: ReminderType
    priority: ReminderPriority
    due_time: datetime
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Recurrence
    recurring: bool = False
    recurrence_pattern: Optional[Dict] = None  # {'interval': 'daily', 'every': 1, 'until': None}
    
    # Status
    status: ReminderStatus = ReminderStatus.PENDING
    snooze_count: int = 0
    snooze_until: Optional[datetime] = None
    
    # Notifications
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    notification_history: List[Dict] = field(default_factory=list)
    
    # Context
    context_tags: List[str] = field(default_factory=list)
    location: Optional[str] = None
    related_task_id: Optional[str] = None
    related_event_id: Optional[str] = None
    
    # Advanced
    smart_reminder: bool = False  # Use AI to determine best reminder time
    minimum_notice: int = 5  # minutes before
    maximum_notice: int = 60  # minutes before
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ReminderTemplate:
    """Template for creating common reminders."""
    template_id: str
    title: str
    description: str
    reminder_type: ReminderType
    default_priority: ReminderPriority
    suggested_channels: List[NotificationChannel]
    suggested_context: List[str]
    smart_defaults: Dict[str, Any] = field(default_factory=dict)

class ReminderSystem:
    """
    Enhanced reminder system with intelligent scheduling, context awareness,
    and multi-channel notifications.
    """
    
    def __init__(self, storage_path: str = "data/scheduler/reminders"):
        """
        Initialize the reminder system.
        
        Args:
            storage_path: Path to store reminder data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Reminder storage
        self.reminders: Dict[str, Reminder] = {}
        self.templates: Dict[str, ReminderTemplate] = {}
        self.reminder_history: List[Dict] = []
        
        # User preferences
        self.user_preferences = {
            'default_channels': [NotificationChannel.PUSH, NotificationChannel.DESKTOP],
            'quiet_hours': {'start': 22, 'end': 7},  # 10 PM to 7 AM
            'lead_time': {
                ReminderType.TASK: 30,  # minutes
                ReminderType.EVENT: 60,
                ReminderType.DEADLINE: 120,
                ReminderType.HABIT: 15,
                ReminderType.WELLNESS: 5
            },
            'max_reminders_per_hour': 5,
            'snooze_increments': [5, 15, 30, 60, 120],  # minutes
            'enable_smart_reminders': True,
            'learning_mode': True
        }
        
        # Response tracking for ML
        self.response_patterns: Dict[str, List[float]] = defaultdict(list)  # reminder_type -> response times
        self.snooze_patterns: Dict[str, int] = defaultdict(int)
        self.optimal_times: Dict[str, List[int]] = defaultdict(list)  # reminder_type -> optimal hours
        
        # Notification handlers
        self.notification_handlers: Dict[NotificationChannel, Callable] = {}
        
        # Initialize default templates
        self._initialize_templates()
        
        # Load existing data
        self._load_data()
        
        logger.info("ReminderSystem initialized successfully")
    
    def _initialize_templates(self):
        """Initialize default reminder templates."""
        templates = [
            ReminderTemplate(
                template_id="daily_standup",
                title="Daily Standup Meeting",
                description="Team daily sync-up meeting",
                reminder_type=ReminderType.EVENT,
                default_priority=ReminderPriority.MEDIUM,
                suggested_channels=[NotificationChannel.PUSH, NotificationChannel.SLACK],
                suggested_context=["work", "meeting"],
                smart_defaults={"lead_time": 15}
            ),
            ReminderTemplate(
                template_id="water_break",
                title="Hydration Reminder",
                description="Time to drink water! Stay hydrated.",
                reminder_type=ReminderType.WELLNESS,
                default_priority=ReminderPriority.MEDIUM,
                suggested_channels=[NotificationChannel.PUSH, NotificationChannel.DESKTOP],
                suggested_context=["health", "wellness"],
                smart_defaults={"recurring": True, "interval": "hourly", "every": 1}
            ),
            ReminderTemplate(
                template_id="deadline_reminder",
                title="Upcoming Deadline",
                description="A deadline is approaching",
                reminder_type=ReminderType.DEADLINE,
                default_priority=ReminderPriority.HIGH,
                suggested_channels=[NotificationChannel.PUSH, NotificationChannel.EMAIL],
                suggested_context=["work", "urgent"],
                smart_defaults={"lead_time": 120}
            ),
            ReminderTemplate(
                template_id="meditation",
                title="Meditation Time",
                description="Take a few minutes to meditate and clear your mind",
                reminder_type=ReminderType.WELLNESS,
                default_priority=ReminderPriority.LOW,
                suggested_channels=[NotificationChannel.PUSH, NotificationChannel.VOICE],
                suggested_context=["mindfulness", "wellness"],
                smart_defaults={"recurring": True, "interval": "daily", "time": "19:00"}
            ),
            ReminderTemplate(
                template_id="pill_reminder",
                title="Take Medication",
                description="Time to take your medication",
                reminder_type=ReminderType.WELLNESS,
                default_priority=ReminderPriority.URGENT,
                suggested_channels=[NotificationChannel.PUSH, NotificationChannel.SMS],
                suggested_context=["health", "critical"],
                smart_defaults={"recurring": True, "interval": "daily", "strict": True}
            ),
            ReminderTemplate(
                template_id="bill_payment",
                title="Bill Due",
                description="Your bill payment is due soon",
                reminder_type=ReminderType.BILL,
                default_priority=ReminderPriority.HIGH,
                suggested_channels=[NotificationChannel.EMAIL, NotificationChannel.PUSH],
                suggested_context=["finance", "important"],
                smart_defaults={"lead_time": 48 * 60}  # 2 days in minutes
            )
        ]
        
        for template in templates:
            self.templates[template.template_id] = template
    
    def _load_data(self):
        """Load reminder data from storage."""
        reminders_file = self.storage_path / "reminders.json"
        history_file = self.storage_path / "history.json"
        prefs_file = self.storage_path / "preferences.json"
        patterns_file = self.storage_path / "patterns.json"
        
        if reminders_file.exists():
            try:
                with open(reminders_file, 'r') as f:
                    data = json.load(f)
                    for rem_id, rem_data in data.items():
                        reminder = Reminder(
                            reminder_id=rem_id,
                            title=rem_data['title'],
                            description=rem_data['description'],
                            reminder_type=ReminderType(rem_data['reminder_type']),
                            priority=ReminderPriority(rem_data['priority']),
                            due_time=datetime.fromisoformat(rem_data['due_time']),
                            created_at=datetime.fromisoformat(rem_data['created_at']),
                            updated_at=datetime.fromisoformat(rem_data['updated_at']),
                            recurring=rem_data.get('recurring', False),
                            recurrence_pattern=rem_data.get('recurrence_pattern'),
                            status=ReminderStatus(rem_data.get('status', 'pending')),
                            snooze_count=rem_data.get('snooze_count', 0),
                            notification_channels=[
                                NotificationChannel(ch) for ch in rem_data.get('notification_channels', [])
                            ],
                            notification_history=rem_data.get('notification_history', []),
                            context_tags=rem_data.get('context_tags', []),
                            location=rem_data.get('location'),
                            related_task_id=rem_data.get('related_task_id'),
                            related_event_id=rem_data.get('related_event_id'),
                            smart_reminder=rem_data.get('smart_reminder', False),
                            minimum_notice=rem_data.get('minimum_notice', 5),
                            maximum_notice=rem_data.get('maximum_notice', 60),
                            user_preferences=rem_data.get('user_preferences', {}),
                            metadata=rem_data.get('metadata', {})
                        )
                        self.reminders[rem_id] = reminder
                logger.info(f"Loaded {len(self.reminders)} reminders")
            except Exception as e:
                logger.error(f"Error loading reminders: {e}")
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    self.reminder_history = json.load(f)
                logger.info(f"Loaded {len(self.reminder_history)} reminder history entries")
            except Exception as e:
                logger.error(f"Error loading reminder history: {e}")
        
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r') as f:
                    loaded_prefs = json.load(f)
                    # Convert channel strings back to enums
                    if 'default_channels' in loaded_prefs:
                        loaded_prefs['default_channels'] = [
                            NotificationChannel(ch) for ch in loaded_prefs['default_channels']
                        ]
                    # Convert lead_time keys back to enums
                    if 'lead_time' in loaded_prefs:
                        lead_time = {}
                        for k, v in loaded_prefs['lead_time'].items():
                            try:
                                lead_time[ReminderType(k)] = v
                            except:
                                lead_time[k] = v
                        loaded_prefs['lead_time'] = lead_time
                    
                    self.user_preferences.update(loaded_prefs)
                logger.info("Loaded reminder preferences")
            except Exception as e:
                logger.error(f"Error loading preferences: {e}")
        
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    patterns = json.load(f)
                    self.response_patterns = defaultdict(list, patterns.get('response_patterns', {}))
                    self.snooze_patterns = defaultdict(int, patterns.get('snooze_patterns', {}))
                    self.optimal_times = defaultdict(list, patterns.get('optimal_times', {}))
                logger.info("Loaded response patterns")
            except Exception as e:
                logger.error(f"Error loading patterns: {e}")
    
    async def create_reminder(self,
                            title: str,
                            description: str,
                            reminder_type: ReminderType,
                            due_time: datetime,
                            priority: Optional[ReminderPriority] = None,
                            template_id: Optional[str] = None,
                            notification_channels: Optional[List[NotificationChannel]] = None,
                            recurring: bool = False,
                            recurrence_pattern: Optional[Dict] = None,
                            context_tags: Optional[List[str]] = None,
                            smart_reminder: bool = False,
                            **kwargs) -> Reminder:
        """
        Create a new reminder.
        
        Args:
            title: Reminder title
            description: Reminder description
            reminder_type: Type of reminder
            due_time: When the reminder is due
            priority: Priority level (auto-determined if not specified)
            template_id: Optional template to use
            notification_channels: Channels to notify on
            recurring: Whether reminder recurs
            recurrence_pattern: Pattern for recurrence
            context_tags: Tags for context
            smart_reminder: Whether to use AI optimization
            **kwargs: Additional parameters
            
        Returns:
            Created Reminder object
        """
        # Apply template if specified
        if template_id and template_id in self.templates:
            template = self.templates[template_id]
            title = title or template.title
            description = description or template.description
            reminder_type = reminder_type or template.reminder_type
            if not priority:
                priority = template.default_priority
            if not notification_channels:
                notification_channels = template.suggested_channels
            if not context_tags:
                context_tags = template.suggested_context
            if template.smart_defaults:
                kwargs.update(template.smart_defaults)
        
        # Determine priority if not set
        if not priority:
            priority = self._determine_priority(reminder_type, due_time)
        
        # Set default notification channels
        if not notification_channels:
            notification_channels = self.user_preferences['default_channels']
        
        # Calculate optimal reminder time if smart reminder
        if smart_reminder and self.user_preferences['enable_smart_reminders']:
            due_time = await self._optimize_reminder_time(reminder_type, due_time)
        
        # Generate unique ID
        reminder_id = self._generate_reminder_id(title)
        
        # Create reminder
        reminder = Reminder(
            reminder_id=reminder_id,
            title=title,
            description=description,
            reminder_type=reminder_type,
            priority=priority,
            due_time=due_time,
            recurring=recurring,
            recurrence_pattern=recurrence_pattern,
            notification_channels=notification_channels,
            context_tags=context_tags or [],
            smart_reminder=smart_reminder,
            **kwargs
        )
        
        self.reminders[reminder_id] = reminder
        
        # Schedule notifications
        await self._schedule_notifications(reminder)
        
        # Save data
        await self._save_data()
        
        logger.info(f"Created reminder: {title} (ID: {reminder_id}) due at {due_time}")
        
        return reminder
    
    def _determine_priority(self, reminder_type: ReminderType, due_time: datetime) -> ReminderPriority:
        """Determine appropriate priority based on type and timing."""
        now = datetime.now()
        time_until = (due_time - now).total_seconds() / 3600  # hours
        
        # Base priority by type
        type_priority = {
            ReminderType.DEADLINE: ReminderPriority.HIGH,
            ReminderType.BILL: ReminderPriority.HIGH,
            ReminderType.APPOINTMENT: ReminderPriority.MEDIUM,
            ReminderType.EVENT: ReminderPriority.MEDIUM,
            ReminderType.TASK: ReminderPriority.MEDIUM,
            ReminderType.HABIT: ReminderPriority.LOW,
            ReminderType.WELLNESS: ReminderPriority.LOW,
            ReminderType.LEARNING: ReminderPriority.LOW,
            ReminderType.SOCIAL: ReminderPriority.LOW,
            ReminderType.CUSTOM: ReminderPriority.MEDIUM
        }
        
        base = type_priority.get(reminder_type, ReminderPriority.MEDIUM)
        
        # Adjust based on time urgency
        if time_until < 1:  # Less than 1 hour
            if base.value < ReminderPriority.URGENT.value:
                return ReminderPriority.URGENT
        elif time_until < 24:  # Less than 1 day
            if base.value < ReminderPriority.HIGH.value:
                return ReminderPriority.HIGH
        
        return base
    
    async def _optimize_reminder_time(self,
                                     reminder_type: ReminderType,
                                     due_time: datetime) -> datetime:
        """Optimize reminder time based on user patterns."""
        # Get optimal hours for this reminder type
        optimal_hours = self.optimal_times.get(reminder_type.value, [])
        
        if not optimal_hours and self.response_patterns:
            # Infer from response patterns
            response_data = self.response_patterns.get(reminder_type.value, [])
            if response_data:
                # Find time of day with fastest responses
                # This would require more sophisticated analysis
                pass
        
        # Default to sending 30 minutes before for most reminders
        lead_time = self.user_preferences['lead_time'].get(
            reminder_type,
            self.user_preferences['lead_time'].get(ReminderType.TASK, 30)
        )
        
        # Calculate reminder time
        reminder_time = due_time - timedelta(minutes=lead_time)
        
        # Check quiet hours
        reminder_time = self._respect_quiet_hours(reminder_time)
        
        return reminder_time
    
    def _respect_quiet_hours(self, reminder_time: datetime) -> datetime:
        """Adjust reminder time if it falls in quiet hours."""
        quiet_start = self.user_preferences['quiet_hours']['start']
        quiet_end = self.user_preferences['quiet_hours']['end']
        
        reminder_hour = reminder_time.hour
        
        if quiet_start <= quiet_end:
            # Normal overnight quiet hours (e.g., 22-7)
            if quiet_start <= reminder_hour or reminder_hour < quiet_end:
                # Move to just after quiet hours end
                new_time = reminder_time.replace(
                    hour=quiet_end,
                    minute=0,
                    second=0
                )
                if new_time < reminder_time:
                    new_time += timedelta(days=1)
                return new_time
        else:
            # Wrapped around midnight (rare)
            if reminder_hour >= quiet_start or reminder_hour < quiet_end:
                new_time = reminder_time.replace(
                    hour=quiet_end,
                    minute=0,
                    second=0
                )
                if new_time < reminder_time:
                    new_time += timedelta(days=1)
                return new_time
        
        return reminder_time
    
    async def _schedule_notifications(self, reminder: Reminder):
        """Schedule notifications for a reminder."""
        # In a real implementation, this would integrate with a task queue
        # For now, we'll just log the scheduling
        logger.info(f"Scheduled notifications for reminder {reminder.reminder_id} via "
                   f"{[ch.value for ch in reminder.notification_channels]}")
    
    def _generate_reminder_id(self, title: str) -> str:
        """Generate a unique reminder ID."""
        unique_string = f"{title}_{datetime.now().isoformat()}_{random.random()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    async def get_due_reminders(self, max_count: int = 10) -> List[Reminder]:
        """Get reminders that are due now."""
        now = datetime.now()
        due = []
        
        for reminder in self.reminders.values():
            if reminder.status == ReminderStatus.PENDING:
                # Check if it's time to send
                time_until = (reminder.due_time - now).total_seconds() / 60
                
                if time_until <= reminder.maximum_notice and time_until >= -5:  # Within window or slightly overdue
                    # Check if we haven't sent too many recently
                    if self._can_send_reminder(reminder):
                        due.append(reminder)
        
        # Sort by urgency
        due.sort(key=lambda r: (r.priority.value, r.due_time))
        
        return due[:max_count]
    
    def _can_send_reminder(self, reminder: Reminder) -> bool:
        """Check if we can send this reminder now (rate limiting)."""
        # Check rate limiting
        last_hour = datetime.now() - timedelta(hours=1)
        recent_sent = [
            n for n in reminder.notification_history
            if datetime.fromisoformat(n['timestamp']) > last_hour
        ]
        
        if len(recent_sent) >= self.user_preferences['max_reminders_per_hour']:
            return False
        
        # Check if already sent recently
        if reminder.notification_history:
            last_sent = datetime.fromisoformat(reminder.notification_history[-1]['timestamp'])
            if (datetime.now() - last_sent).total_seconds() < 300:  # 5 minutes
                return False
        
        return True
    
    async def send_reminder(self, reminder: Reminder, channel: NotificationChannel) -> bool:
        """Send a reminder through a specific channel."""
        # This would integrate with actual notification services
        # For now, we'll just log and record
        
        success = True
        error_msg = None
        
        try:
            # Simulate sending
            logger.info(f"Sending reminder '{reminder.title}' via {channel.value}")
            
            # Record in history
            reminder.notification_history.append({
                'timestamp': datetime.now().isoformat(),
                'channel': channel.value,
                'success': success
            })
            
            # Update status
            reminder.status = ReminderStatus.SENT
            reminder.updated_at = datetime.now()
            
            # Track response pattern
            self.response_patterns[reminder.reminder_type.value].append(
                (reminder.due_time - datetime.now()).total_seconds() / 60
            )
            
        except Exception as e:
            success = False
            error_msg = str(e)
            logger.error(f"Failed to send reminder: {e}")
        
        # Record in history
        self.reminder_history.append({
            'reminder_id': reminder.reminder_id,
            'title': reminder.title,
            'type': reminder.reminder_type.value,
            'channel': channel.value,
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'error': error_msg
        })
        
        return success
    
    async def acknowledge_reminder(self, reminder_id: str, notes: str = "") -> bool:
        """Mark a reminder as acknowledged by user."""
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return False
        
        reminder.status = ReminderStatus.ACKNOWLEDGED
        reminder.updated_at = datetime.now()
        
        # Track response time
        if reminder.notification_history:
            last_sent = datetime.fromisoformat(reminder.notification_history[-1]['timestamp'])
            response_time = (datetime.now() - last_sent).total_seconds() / 60
            self.response_patterns[reminder.reminder_type.value].append(response_time)
        
        # Handle recurrence
        if reminder.recurring and reminder.recurrence_pattern:
            await self._schedule_next_recurrence(reminder)
        
        await self._save_data()
        
        logger.info(f"Reminder {reminder_id} acknowledged")
        return True
    
    async def snooze_reminder(self, reminder_id: str, minutes: Optional[int] = None) -> bool:
        """Snooze a reminder."""
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return False
        
        # Determine snooze duration
        if not minutes:
            increments = self.user_preferences['snooze_increments']
            idx = min(reminder.snooze_count, len(increments) - 1)
            minutes = increments[idx]
        
        reminder.snooze_until = datetime.now() + timedelta(minutes=minutes)
        reminder.snooze_count += 1
        reminder.status = ReminderStatus.SNOOZED
        reminder.updated_at = datetime.now()
        
        # Track snooze pattern
        self.snooze_patterns[reminder.reminder_type.value] += 1
        
        await self._save_data()
        
        logger.info(f"Reminder {reminder_id} snoozed for {minutes} minutes")
        return True
    
    async def complete_reminder(self, reminder_id: str) -> bool:
        """Mark a reminder as completed."""
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return False
        
        reminder.status = ReminderStatus.COMPLETED
        reminder.updated_at = datetime.now()
        
        # Handle recurrence
        if reminder.recurring and reminder.recurrence_pattern:
            await self._schedule_next_recurrence(reminder)
        
        await self._save_data()
        
        logger.info(f"Reminder {reminder_id} completed")
        return True
    
    async def cancel_reminder(self, reminder_id: str) -> bool:
        """Cancel a reminder."""
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return False
        
        reminder.status = ReminderStatus.CANCELLED
        reminder.updated_at = datetime.now()
        
        await self._save_data()
        
        logger.info(f"Reminder {reminder_id} cancelled")
        return True
    
    async def _schedule_next_recurrence(self, reminder: Reminder):
        """Schedule the next occurrence of a recurring reminder."""
        if not reminder.recurrence_pattern:
            return
        
        pattern = reminder.recurrence_pattern
        interval = pattern.get('interval', 'daily')
        every = pattern.get('every', 1)
        until = pattern.get('until')
        
        # Calculate next due time
        if interval == 'daily':
            next_due = reminder.due_time + timedelta(days=every)
        elif interval == 'weekly':
            next_due = reminder.due_time + timedelta(weeks=every)
        elif interval == 'monthly':
            # Simple approximation
            next_due = reminder.due_time + timedelta(days=30 * every)
        elif interval == 'hourly':
            next_due = reminder.due_time + timedelta(hours=every)
        else:
            return
        
        # Check if we should stop
        if until and next_due > datetime.fromisoformat(until):
            return
        
        # Create next reminder
        await self.create_reminder(
            title=reminder.title,
            description=reminder.description,
            reminder_type=reminder.reminder_type,
            due_time=next_due,
            priority=reminder.priority,
            notification_channels=reminder.notification_channels,
            recurring=True,
            recurrence_pattern=reminder.recurrence_pattern,
            context_tags=reminder.context_tags,
            smart_reminder=reminder.smart_reminder,
            metadata=reminder.metadata
        )
    
    async def get_upcoming_reminders(self,
                                   days: int = 7,
                                   reminder_types: Optional[List[ReminderType]] = None) -> List[Reminder]:
        """Get upcoming reminders."""
        now = datetime.now()
        cutoff = now + timedelta(days=days)
        
        upcoming = []
        for reminder in self.reminders.values():
            if reminder.status in [ReminderStatus.PENDING, ReminderStatus.SNOOZED]:
                if reminder.due_time <= cutoff:
                    if not reminder_types or reminder.reminder_type in reminder_types:
                        # Handle snoozed reminders
                        if reminder.status == ReminderStatus.SNOOZED and reminder.snooze_until:
                            if reminder.snooze_until <= cutoff:
                                upcoming.append(reminder)
                        else:
                            upcoming.append(reminder)
        
        # Sort by due time
        upcoming.sort(key=lambda r: r.due_time)
        
        return upcoming
    
    async def get_reminder_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get statistics about reminders."""
        cutoff = datetime.now() - timedelta(days=days)
        
        # Filter reminders in period
        period_reminders = [
            r for r in self.reminders.values()
            if r.created_at > cutoff
        ]
        
        # Filter history
        period_history = [
            h for h in self.reminder_history
            if datetime.fromisoformat(h['timestamp']) > cutoff
        ]
        
        if not period_reminders and not period_history:
            return {'message': 'No reminder data available'}
        
        # Calculate stats
        total_reminders = len(period_reminders)
        completed = sum(1 for r in period_reminders if r.status == ReminderStatus.COMPLETED)
        missed = sum(1 for r in period_reminders if r.status == ReminderStatus.MISSED)
        snoozed = sum(1 for r in period_reminders if r.status == ReminderStatus.SNOOZED)
        
        # By type
        by_type = defaultdict(int)
        for r in period_reminders:
            by_type[r.reminder_type.value] += 1
        
        # Response times
        response_times = []
        for r in period_reminders:
            if r.notification_history and r.status == ReminderStatus.ACKNOWLEDGED:
                last_sent = datetime.fromisoformat(r.notification_history[-1]['timestamp'])
                if r.updated_at:
                    response_time = (r.updated_at - last_sent).total_seconds() / 60
                    response_times.append(response_time)
        
        avg_response = np.mean(response_times) if response_times else None
        
        # Success rate by channel
        channel_success = defaultdict(lambda: {'sent': 0, 'success': 0})
        for h in period_history:
            channel = h['channel']
            channel_success[channel]['sent'] += 1
            if h.get('success', False):
                channel_success[channel]['success'] += 1
        
        channel_rates = {
            ch: data['success'] / data['sent'] if data['sent'] > 0 else 0
            for ch, data in channel_success.items()
        }
        
        return {
            'period_days': days,
            'total_reminders': total_reminders,
            'completion_rate': completed / total_reminders if total_reminders > 0 else 0,
            'missed_rate': missed / total_reminders if total_reminders > 0 else 0,
            'snooze_rate': snoozed / total_reminders if total_reminders > 0 else 0,
            'by_type': dict(by_type),
            'average_response_time_minutes': avg_response,
            'channel_success_rates': channel_rates,
            'total_notifications_sent': len(period_history)
        }
    
    async def learn_from_history(self):
        """Learn from reminder history to improve future scheduling."""
        if not self.user_preferences['learning_mode']:
            return
        
        # Analyze optimal times by reminder type
        for reminder in self.reminders.values():
            if reminder.status == ReminderStatus.ACKNOWLEDGED and reminder.notification_history:
                # Find when user typically acknowledges
                for notification in reminder.notification_history:
                    if notification.get('success'):
                        sent_time = datetime.fromisoformat(notification['timestamp'])
                        self.optimal_times[reminder.reminder_type.value].append(sent_time.hour)
        
        # Keep only recent data
        for rt in self.optimal_times:
            if len(self.optimal_times[rt]) > 100:
                self.optimal_times[rt] = self.optimal_times[rt][-100:]
        
        # Analyze response patterns to adjust lead times
        for rt_str, times in self.response_patterns.items():
            if len(times) > 10:
                avg_response = np.mean(times)
                try:
                    rt = ReminderType(rt_str)
                    # Adjust lead time based on actual response patterns
                    current_lead = self.user_preferences['lead_time'].get(rt, 30)
                    if avg_response < current_lead * 0.7:
                        # User responds quickly, can reduce lead time
                        new_lead = max(5, int(current_lead * 0.9))
                        self.user_preferences['lead_time'][rt] = new_lead
                    elif avg_response > current_lead * 1.3:
                        # User needs more notice
                        new_lead = min(240, int(current_lead * 1.1))
                        self.user_preferences['lead_time'][rt] = new_lead
                except:
                    pass
        
        logger.info("Learned from reminder history")
    
    async def register_notification_handler(self,
                                          channel: NotificationChannel,
                                          handler: Callable) -> None:
        """Register a handler for a notification channel."""
        self.notification_handlers[channel] = handler
        logger.info(f"Registered handler for {channel.value}")
    
    async def update_preferences(self, new_preferences: Dict[str, Any]) -> None:
        """Update user preferences."""
        # Convert channel strings to enums if needed
        if 'default_channels' in new_preferences:
            channels = []
            for ch in new_preferences['default_channels']:
                if isinstance(ch, str):
                    channels.append(NotificationChannel(ch))
                else:
                    channels.append(ch)
            new_preferences['default_channels'] = channels
        
        # Convert lead_time keys to enums if needed
        if 'lead_time' in new_preferences:
            lead_time = {}
            for k, v in new_preferences['lead_time'].items():
                if isinstance(k, str):
                    try:
                        lead_time[ReminderType(k)] = v
                    except:
                        lead_time[k] = v
                else:
                    lead_time[k] = v
            new_preferences['lead_time'] = lead_time
        
        self.user_preferences.update(new_preferences)
        await self._save_data()
        logger.info("Reminder preferences updated")
    
    async def _save_data(self):
        """Save reminder data to storage."""
        try:
            # Save reminders
            reminders_file = self.storage_path / "reminders.json"
            reminders_data = {}
            for rem_id, reminder in self.reminders.items():
                reminders_data[rem_id] = {
                    'title': reminder.title,
                    'description': reminder.description,
                    'reminder_type': reminder.reminder_type.value,
                    'priority': reminder.priority.value,
                    'due_time': reminder.due_time.isoformat(),
                    'created_at': reminder.created_at.isoformat(),
                    'updated_at': reminder.updated_at.isoformat(),
                    'recurring': reminder.recurring,
                    'recurrence_pattern': reminder.recurrence_pattern,
                    'status': reminder.status.value,
                    'snooze_count': reminder.snooze_count,
                    'notification_channels': [ch.value for ch in reminder.notification_channels],
                    'notification_history': reminder.notification_history,
                    'context_tags': reminder.context_tags,
                    'location': reminder.location,
                    'related_task_id': reminder.related_task_id,
                    'related_event_id': reminder.related_event_id,
                    'smart_reminder': reminder.smart_reminder,
                    'minimum_notice': reminder.minimum_notice,
                    'maximum_notice': reminder.maximum_notice,
                    'user_preferences': reminder.user_preferences,
                    'metadata': reminder.metadata
                }
            
            with open(reminders_file, 'w') as f:
                json.dump(reminders_data, f, indent=2, default=str)
            
            # Save history
            history_file = self.storage_path / "history.json"
            with open(history_file, 'w') as f:
                json.dump(self.reminder_history[-1000:], f, indent=2, default=str)
            
            # Save preferences
            prefs_file = self.storage_path / "preferences.json"
            prefs_to_save = self.user_preferences.copy()
            # Convert enums to strings for JSON
            if 'default_channels' in prefs_to_save:
                prefs_to_save['default_channels'] = [
                    ch.value for ch in prefs_to_save['default_channels']
                ]
            if 'lead_time' in prefs_to_save:
                lead_time = {}
                for k, v in prefs_to_save['lead_time'].items():
                    if isinstance(k, ReminderType):
                        lead_time[k.value] = v
                    else:
                        lead_time[k] = v
                prefs_to_save['lead_time'] = lead_time
            
            with open(prefs_file, 'w') as f:
                json.dump(prefs_to_save, f, indent=2)
            
            # Save patterns
            patterns_file = self.storage_path / "patterns.json"
            with open(patterns_file, 'w') as f:
                json.dump({
                    'response_patterns': dict(self.response_patterns),
                    'snooze_patterns': dict(self.snooze_patterns),
                    'optimal_times': dict(self.optimal_times)
                }, f, indent=2, default=str)
            
            logger.debug("Reminder data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving reminder data: {e}")