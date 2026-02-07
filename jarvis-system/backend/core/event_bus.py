import asyncio
from typing import Dict, List, Callable, Any, Awaitable
import logging
from collections import defaultdict
import uuid
import time

logger = logging.getLogger("EventBus")

class Event:
    def __init__(self, topic: str, data: Any = None):
        self.id = str(uuid.uuid4())
        self.topic = topic
        self.data = data
        self.timestamp = time.time()

class EventBus:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance.subscribers = defaultdict(list)
            cls._instance.dead_letter_queue = []
        return cls._instance

    def subscribe(self, topic: str, handler: Callable[[Event], Awaitable[None]]):
        """
        Subscribe to a topic. Handler must be async.
        """
        self.subscribers[topic].append(handler)
        logger.info(f"Subscribed to topic: {topic}")

    async def publish(self, topic: str, data: Any = None):
        """
        Publish an event to a topic.
        """
        event = Event(topic, data)
        if topic not in self.subscribers:
            # logger.debug(f"No subscribers for topic: {topic}")
            return

        handlers = self.subscribers[topic]
        tasks = []
        for handler in handlers:
            tasks.append(self._execute_handler(handler, event))
        
        # Run all handlers concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_handler(self, handler, event):
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error handling event {event.topic}: {e}")
            self.dead_letter_queue.append((event, str(e)))

# Global instance
event_bus = EventBus()
