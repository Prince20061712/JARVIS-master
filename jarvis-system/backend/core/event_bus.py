import asyncio
import time
import uuid
import logging
import inspect
import functools
from typing import Dict, List, Callable, Any, Awaitable, Optional, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import heapq
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger("AdvancedEventBus")

class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class EventStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class SubscriptionType(Enum):
    ONCE = "once"          # Trigger only once
    MANY = "many"          # Trigger multiple times (default)
    THROTTLED = "throttled"  # Throttled execution
    DEBOUNCED = "debounced"  # Debounced execution

@dataclass
class Event:
    """Enhanced Event with metadata and lifecycle tracking"""
    id: str
    topic: str
    data: Any = None
    timestamp: float = field(default_factory=time.time)
    priority: EventPriority = EventPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    
    # Lifecycle tracking
    status: EventStatus = EventStatus.PENDING
    processing_start: Optional[float] = None
    processing_end: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.correlation_id is None:
            self.correlation_id = self.id
    
    @property
    def processing_time(self) -> Optional[float]:
        if self.processing_start and self.processing_end:
            return self.processing_end - self.processing_start
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "id": self.id,
            "topic": self.topic,
            "data": self.data,
            "timestamp": self.timestamp,
            "priority": self.priority.value,
            "metadata": self.metadata,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "headers": self.headers,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "error": self.error
        }

@dataclass
class Subscription:
    """Subscription with filtering and configuration"""
    id: str
    topic: str
    handler: Callable[[Event], Awaitable[None]]
    priority: int = 0  # Higher priority gets executed first
    filter_func: Optional[Callable[[Event], bool]] = None
    subscription_type: SubscriptionType = SubscriptionType.MANY
    config: Dict[str, Any] = field(default_factory=dict)
    
    # For throttling/debouncing
    last_execution: float = 0
    pending_execution: bool = False
    
    def matches(self, event: Event) -> bool:
        """Check if subscription matches event"""
        if self.filter_func:
            return self.filter_func(event)
        return True

class EventMiddleware:
    """Base class for event middleware"""
    async def before_publish(self, event: Event) -> Optional[Event]:
        """Called before publishing an event"""
        return event
    
    async def after_publish(self, event: Event):
        """Called after publishing an event"""
        pass
    
    async def before_process(self, event: Event, subscription: Subscription) -> Optional[Event]:
        """Called before processing an event"""
        return event
    
    async def after_process(self, event: Event, subscription: Subscription, result: Any):
        """Called after processing an event"""
        pass
    
    async def on_error(self, event: Event, subscription: Subscription, error: Exception):
        """Called when an error occurs during processing"""
        pass

class AdvancedEventBus:
    """Advanced Event Bus with middleware, filtering, and monitoring"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AdvancedEventBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.subscriptions: Dict[str, List[Subscription]] = defaultdict(list)
            self.middlewares: List[EventMiddleware] = []
            self.event_history: deque = deque(maxlen=10000)
            self.dead_letter_queue: List[Tuple[Event, str, Exception]] = []
            self.metrics: Dict[str, Any] = defaultdict(int)
            self.metrics['events_published'] = defaultdict(int)
            self.metrics['events_processed'] = defaultdict(int)
            self.metrics['event_errors'] = defaultdict(int)
            self._processing_lock = asyncio.Lock()
            self._subscription_lock = asyncio.Lock()
            
            # Priority queue for high-priority events
            self._priority_queue: List[Tuple[int, float, Event]] = []  # (-priority, timestamp, event)
            self._worker_task: Optional[asyncio.Task] = None
            self._is_running = False
            
            # Circuit breaker pattern
            self.circuit_breakers: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
                'failures': 0,
                'last_failure': 0,
                'state': 'CLOSED',
                'next_check': 0
            })
            
            # Retry policies
            self.retry_policies: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
                'max_retries': 3,
                'backoff_factor': 1.5,
                'max_delay': 60
            })
            
            self._initialized = True
            logger.info("Advanced Event Bus initialized")
    
    def add_middleware(self, middleware: EventMiddleware):
        """Add middleware to the event bus"""
        self.middlewares.append(middleware)
        logger.info(f"Added middleware: {middleware.__class__.__name__}")
    
    def remove_middleware(self, middleware: EventMiddleware):
        """Remove middleware from the event bus"""
        if middleware in self.middlewares:
            self.middlewares.remove(middleware)
            logger.info(f"Removed middleware: {middleware.__class__.__name__}")
    
    def subscribe(
        self,
        topic: str,
        handler: Callable[[Event], Awaitable[None]],
        priority: int = 0,
        filter_func: Optional[Callable[[Event], bool]] = None,
        subscription_type: SubscriptionType = SubscriptionType.MANY,
        **config
    ) -> str:
        """
        Subscribe to a topic with advanced options
        
        Args:
            topic: Event topic to subscribe to
            handler: Async handler function
            priority: Higher priority handlers execute first
            filter_func: Function to filter which events to handle
            subscription_type: Type of subscription
            config: Additional configuration (throttle_ms, debounce_ms, etc.)
        
        Returns:
            Subscription ID for later unsubscription
        """
        subscription_id = str(uuid.uuid4())
        subscription = Subscription(
            id=subscription_id,
            topic=topic,
            handler=handler,
            priority=priority,
            filter_func=filter_func,
            subscription_type=subscription_type,
            config=config
        )
        
        async def add_subscription():
            async with self._subscription_lock:
                self.subscriptions[topic].append(subscription)
                # Sort by priority (higher priority first)
                self.subscriptions[topic].sort(key=lambda s: s.priority, reverse=True)
        
        asyncio.create_task(add_subscription())
        
        logger.info(f"Subscribed to topic: {topic} with priority {priority}")
        return subscription_id
    
    def subscribe_once(
        self,
        topic: str,
        handler: Callable[[Event], Awaitable[None]],
        **kwargs
    ) -> str:
        """Subscribe to handle event only once"""
        return self.subscribe(
            topic=topic,
            handler=handler,
            subscription_type=SubscriptionType.ONCE,
            **kwargs
        )
    
    def subscribe_filtered(
        self,
        topics: List[str],
        handler: Callable[[Event], Awaitable[None]],
        filter_func: Callable[[Event], bool],
        **kwargs
    ) -> List[str]:
        """Subscribe to multiple topics with a filter"""
        subscription_ids = []
        for topic in topics:
            sub_id = self.subscribe(
                topic=topic,
                handler=handler,
                filter_func=filter_func,
                **kwargs
            )
            subscription_ids.append(sub_id)
        return subscription_ids
    
    def unsubscribe(self, subscription_id: str):
        """Unsubscribe using subscription ID"""
        async def remove_subscription():
            async with self._subscription_lock:
                for topic, subscriptions in self.subscriptions.items():
                    for i, subscription in enumerate(subscriptions):
                        if subscription.id == subscription_id:
                            subscriptions.pop(i)
                            logger.info(f"Unsubscribed from topic: {topic}")
                            return
        
        asyncio.create_task(remove_subscription())
    
    def unsubscribe_all(self, topic: str):
        """Unsubscribe all handlers from a topic"""
        async def remove_all():
            async with self._subscription_lock:
                if topic in self.subscriptions:
                    del self.subscriptions[topic]
                    logger.info(f"Unsubscribed all from topic: {topic}")
        
        asyncio.create_task(remove_all())
    
    async def publish(
        self,
        topic: str,
        data: Any = None,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
        reply_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        wait_for_handlers: bool = False
    ) -> str:
        """
        Publish an event with advanced options
        
        Args:
            topic: Event topic
            data: Event data
            priority: Event priority
            source: Source identifier
            correlation_id: Correlation ID for tracing
            reply_to: Topic to send replies to
            headers: Additional headers
            metadata: Additional metadata
            wait_for_handlers: Whether to wait for all handlers to complete
        
        Returns:
            Event ID
        """
        event = Event(
            id=str(uuid.uuid4()),
            topic=topic,
            data=data,
            priority=priority,
            source=source or "unknown",
            correlation_id=correlation_id,
            reply_to=reply_to,
            headers=headers or {},
            metadata=metadata or {}
        )
        
        # Apply middleware before publishing
        for middleware in self.middlewares:
            modified_event = await middleware.before_publish(event)
            if modified_event is None:
                logger.info(f"Middleware {middleware.__class__.__name__} cancelled event {event.id}")
                return event.id
            event = modified_event
        
        # Store in history
        self.event_history.append(event.to_dict())
        
        # Update metrics
        self.metrics['events_published'][topic] += 1
        self.metrics['total_events_published'] += 1
        
        # Process based on priority
        if priority in [EventPriority.HIGH, EventPriority.CRITICAL]:
            # Add to priority queue
            heapq.heappush(self._priority_queue, (
                -priority.value,  # Negative for max-heap behavior
                event.timestamp,
                event
            ))
            logger.debug(f"Added high priority event {event.id} to queue")
            
            if wait_for_handlers:
                # Wait for processing (simplified - would need more complex tracking)
                await asyncio.sleep(0.01)
        else:
            # Process normally
            await self._process_event(event, wait_for_handlers)
        
        # Apply middleware after publishing
        for middleware in self.middlewares:
            await middleware.after_publish(event)
        
        logger.info(f"Published event {event.id} to topic {topic}")
        return event.id
    
    async def _process_event(self, event: Event, wait_for_handlers: bool = False):
        """Process a single event"""
        event.status = EventStatus.PROCESSING
        event.processing_start = time.time()
        
        async with self._processing_lock:
            if event.topic not in self.subscriptions:
                logger.debug(f"No subscribers for topic: {event.topic}")
                event.status = EventStatus.COMPLETED
                event.processing_end = time.time()
                return
        
        handlers = self.subscriptions[event.topic]
        tasks = []
        handlers_to_remove = []
        
        for subscription in handlers:
            if not subscription.matches(event):
                continue
            
            # Check circuit breaker
            cb_key = f"{event.topic}_{subscription.id}"
            if not self._check_circuit_breaker(cb_key):
                logger.warning(f"Circuit breaker open for {cb_key}")
                continue
            
            # Handle different subscription types
            if subscription.subscription_type == SubscriptionType.ONCE:
                handlers_to_remove.append(subscription)
            
            elif subscription.subscription_type == SubscriptionType.THROTTLED:
                throttle_ms = subscription.config.get('throttle_ms', 100)
                now = time.time() * 1000
                if now - subscription.last_execution < throttle_ms:
                    if not subscription.pending_execution:
                        subscription.pending_execution = True
                        # Schedule for later execution
                        asyncio.create_task(
                            self._execute_throttled(subscription, event, throttle_ms)
                        )
                    continue
            
            elif subscription.subscription_type == SubscriptionType.DEBOUNCED:
                debounce_ms = subscription.config.get('debounce_ms', 100)
                subscription.last_execution = time.time() * 1000
                subscription.pending_execution = True
                # Cancel previous debounced execution if any
                asyncio.create_task(
                    self._execute_debounced(subscription, event, debounce_ms)
                )
                continue
            
            # Execute handler
            task = asyncio.create_task(
                self._execute_handler(subscription, event, cb_key)
            )
            tasks.append(task)
        
        # Remove once handlers
        if handlers_to_remove:
            async with self._subscription_lock:
                for subscription in handlers_to_remove:
                    if subscription in self.subscriptions[event.topic]:
                        self.subscriptions[event.topic].remove(subscription)
        
        # Wait for handlers if requested
        if wait_for_handlers and tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Handler {i} failed: {result}")
        elif tasks:
            # Fire and forget
            asyncio.create_task(self._wait_for_tasks(tasks, event))
        
        event.processing_end = time.time()
        if event.status == EventStatus.PROCESSING:
            event.status = EventStatus.COMPLETED
    
    async def _execute_handler(
        self,
        subscription: Subscription,
        event: Event,
        circuit_breaker_key: str
    ):
        """Execute a single handler with error handling and retries"""
        start_time = time.time()
        
        # Apply middleware before processing
        modified_event = event
        for middleware in self.middlewares:
            modified_event = await middleware.before_process(event, subscription)
            if modified_event is None:
                logger.debug(f"Middleware cancelled processing for event {event.id}")
                return
            event = modified_event
        
        try:
            # Update subscription last execution time
            subscription.last_execution = time.time() * 1000
            
            # Execute handler
            await subscription.handler(event)
            
            # Update metrics
            self.metrics['events_processed'][event.topic] += 1
            self.metrics['total_events_processed'] += 1
            
            # Reset circuit breaker on success
            self._reset_circuit_breaker(circuit_breaker_key)
            
            # Apply middleware after successful processing
            for middleware in self.middlewares:
                await middleware.after_process(event, subscription, "success")
            
            logger.debug(f"Handler executed successfully for event {event.id}")
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Update metrics
            self.metrics['event_errors'][event.topic] += 1
            
            # Record error in event
            event.error = str(e)
            event.status = EventStatus.FAILED
            
            # Update circuit breaker
            self._record_circuit_failure(circuit_breaker_key)
            
            # Apply middleware on error
            for middleware in self.middlewares:
                await middleware.on_error(event, subscription, e)
            
            # Handle retries
            if event.retry_count < event.max_retries:
                await self._handle_retry(event, subscription, e)
            else:
                # Move to dead letter queue
                self.dead_letter_queue.append((event, subscription.id, e))
                logger.error(
                    f"Handler failed for event {event.id} after {event.retry_count} retries. "
                    f"Moved to DLQ. Error: {e}"
                )
    
    async def _handle_retry(self, event: Event, subscription: Subscription, error: Exception):
        """Handle retry logic with exponential backoff"""
        event.retry_count += 1
        event.status = EventStatus.RETRYING
        
        # Calculate backoff delay
        retry_policy = self.retry_policies[event.topic]
        backoff_factor = retry_policy['backoff_factor']
        max_delay = retry_policy['max_delay']
        
        delay = min(
            backoff_factor ** event.retry_count,
            max_delay
        )
        
        logger.info(
            f"Retrying event {event.id} (attempt {event.retry_count}) "
            f"after {delay:.2f}s delay. Error: {error}"
        )
        
        await asyncio.sleep(delay)
        
        # Retry the handler
        await self._execute_handler(subscription, event, f"{event.topic}_{subscription.id}")
    
    async def _execute_throttled(
        self,
        subscription: Subscription,
        event: Event,
        throttle_ms: float
    ):
        """Execute a throttled handler"""
        await asyncio.sleep(throttle_ms / 1000)
        subscription.pending_execution = False
        await self._execute_handler(subscription, event, f"{event.topic}_{subscription.id}")
    
    async def _execute_debounced(
        self,
        subscription: Subscription,
        event: Event,
        debounce_ms: float
    ):
        """Execute a debounced handler"""
        await asyncio.sleep(debounce_ms / 1000)
        if subscription.pending_execution:
            subscription.pending_execution = False
            await self._execute_handler(subscription, event, f"{event.topic}_{subscription.id}")
    
    async def _wait_for_tasks(self, tasks: List[asyncio.Task], event: Event):
        """Wait for tasks to complete and update metrics"""
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error waiting for tasks for event {event.id}: {e}")
    
    def _check_circuit_breaker(self, key: str) -> bool:
        """Check if circuit breaker allows execution"""
        cb = self.circuit_breakers[key]
        
        if cb['state'] == 'OPEN':
            # Check if we should try again
            if time.time() > cb['next_check']:
                cb['state'] = 'HALF_OPEN'
                return True
            return False
        
        return True
    
    def _record_circuit_failure(self, key: str):
        """Record a circuit failure"""
        cb = self.circuit_breakers[key]
        cb['failures'] += 1
        cb['last_failure'] = time.time()
        
        if cb['failures'] >= 5:  # Threshold
            cb['state'] = 'OPEN'
            cb['next_check'] = time.time() + 30  # Try again after 30 seconds
            logger.warning(f"Circuit breaker opened for {key}")
    
    def _reset_circuit_breaker(self, key: str):
        """Reset circuit breaker on success"""
        cb = self.circuit_breakers[key]
        cb['failures'] = 0
        cb['state'] = 'CLOSED'
    
    async def start_priority_worker(self):
        """Start worker for processing high-priority events"""
        self._is_running = True
        self._worker_task = asyncio.create_task(self._priority_worker())
        logger.info("Priority worker started")
    
    async def _priority_worker(self):
        """Worker that processes high-priority events"""
        while self._is_running:
            try:
                if self._priority_queue:
                    # Get highest priority event
                    _, _, event = heapq.heappop(self._priority_queue)
                    await self._process_event(event)
                else:
                    await asyncio.sleep(0.01)  # Small sleep to prevent busy waiting
            except Exception as e:
                logger.error(f"Priority worker error: {e}")
                await asyncio.sleep(1)
    
    async def stop_priority_worker(self):
        """Stop the priority worker"""
        self._is_running = False
        if self._worker_task:
            await self._worker_task
            self._worker_task = None
        logger.info("Priority worker stopped")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            'events_published': dict(self.metrics['events_published']),
            'events_processed': dict(self.metrics['events_processed']),
            'event_errors': dict(self.metrics['event_errors']),
            'total_events_published': self.metrics['total_events_published'],
            'total_events_processed': self.metrics['total_events_processed'],
            'active_subscriptions': sum(len(subs) for subs in self.subscriptions.values()),
            'dead_letter_queue_size': len(self.dead_letter_queue),
            'event_history_size': len(self.event_history)
        }
    
    def get_event_history(
        self,
        topic: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get event history with filtering"""
        history = list(self.event_history)
        
        if topic:
            history = [e for e in history if e['topic'] == topic]
        
        return history[offset:offset + limit]
    
    def get_subscription_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get information about all subscriptions"""
        info = {}
        for topic, subscriptions in self.subscriptions.items():
            info[topic] = [
                {
                    'id': s.id,
                    'priority': s.priority,
                    'type': s.subscription_type.value,
                    'config': s.config,
                    'last_execution': s.last_execution
                }
                for s in subscriptions
            ]
        return info
    
    def clear_dead_letter_queue(self):
        """Clear the dead letter queue"""
        self.dead_letter_queue.clear()
        logger.info("Dead letter queue cleared")
    
    def retry_dead_letter_queue(self):
        """Retry all events in dead letter queue"""
        retry_count = len(self.dead_letter_queue)
        for event, subscription_id, error in self.dead_letter_queue:
            asyncio.create_task(self._retry_dlq_event(event, subscription_id))
        
        self.dead_letter_queue.clear()
        logger.info(f"Retrying {retry_count} events from dead letter queue")
    
    async def _retry_dlq_event(self, event: Event, subscription_id: str):
        """Retry a single event from dead letter queue"""
        # Find the subscription
        subscription = None
        for topic_subs in self.subscriptions.values():
            for sub in topic_subs:
                if sub.id == subscription_id:
                    subscription = sub
                    break
            if subscription:
                break
        
        if subscription:
            event.retry_count = 0
            event.status = EventStatus.PENDING
            event.error = None
            await self._execute_handler(subscription, event, f"{event.topic}_{subscription.id}")
        else:
            logger.warning(f"Subscription {subscription_id} not found for DLQ retry")
    
    async def wait_for_event(
        self,
        topic: str,
        timeout: float = 10.0,
        filter_func: Optional[Callable[[Event], bool]] = None
    ) -> Optional[Event]:
        """
        Wait for a specific event with timeout
        
        Returns:
            The awaited event or None if timeout
        """
        event_received = asyncio.Event()
        received_event = None
        
        async def handler(event: Event):
            nonlocal received_event
            if filter_func is None or filter_func(event):
                received_event = event
                event_received.set()
        
        subscription_id = self.subscribe_once(topic, handler)
        
        try:
            await asyncio.wait_for(event_received.wait(), timeout=timeout)
            return received_event
        except asyncio.TimeoutError:
            return None
        finally:
            self.unsubscribe(subscription_id)
    
    @asynccontextmanager
    async def request_reply(
        self,
        request_topic: str,
        reply_topic: str,
        request_data: Any = None,
        timeout: float = 10.0
    ):
        """
        Context manager for request-reply pattern
        
        Usage:
            async with event_bus.request_reply('request.topic', 'reply.topic') as reply:
                # reply will contain the response event or None
        """
        reply_event = None
        reply_received = asyncio.Event()
        
        async def reply_handler(event: Event):
            nonlocal reply_event
            reply_event = event
            reply_received.set()
        
        # Subscribe to reply topic
        subscription_id = self.subscribe_once(reply_topic, reply_handler)
        
        try:
            # Publish request
            request_id = await self.publish(
                topic=request_topic,
                data=request_data,
                reply_to=reply_topic
            )
            
            # Wait for reply
            try:
                await asyncio.wait_for(reply_received.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Request {request_id} timed out waiting for reply")
            
            yield reply_event
        finally:
            self.unsubscribe(subscription_id)


# Example middleware implementations
class LoggingMiddleware(EventMiddleware):
    """Middleware for logging events"""
    async def before_publish(self, event: Event) -> Optional[Event]:
        logger.info(f"Publishing event {event.id} to topic {event.topic}")
        return event
    
    async def after_process(self, event: Event, subscription: Subscription, result: Any):
        logger.info(f"Processed event {event.id} by subscription {subscription.id}")
    
    async def on_error(self, event: Event, subscription: Subscription, error: Exception):
        logger.error(f"Error processing event {event.id}: {error}")

class MetricsMiddleware(EventMiddleware):
    """Middleware for collecting metrics"""
    def __init__(self):
        self.processing_times = []
    
    async def before_process(self, event: Event, subscription: Subscription) -> Optional[Event]:
        event.processing_start = time.time()
        return event
    
    async def after_process(self, event: Event, subscription: Subscription, result: Any):
        if event.processing_start:
            processing_time = time.time() - event.processing_start
            self.processing_times.append(processing_time)
    
    def get_average_processing_time(self) -> float:
        if not self.processing_times:
            return 0.0
        return sum(self.processing_times) / len(self.processing_times)

class ValidationMiddleware(EventMiddleware):
    """Middleware for validating events"""
    def __init__(self, validation_rules: Dict[str, Callable[[Event], bool]]):
        self.validation_rules = validation_rules
    
    async def before_publish(self, event: Event) -> Optional[Event]:
        if event.topic in self.validation_rules:
            if not self.validation_rules[event.topic](event):
                logger.warning(f"Event {event.id} failed validation for topic {event.topic}")
                return None
        return event


# Global instance
event_bus = AdvancedEventBus()


# Example usage
async def example_usage():
    """Example demonstrating advanced event bus features"""
    
    # Add middleware
    event_bus.add_middleware(LoggingMiddleware())
    event_bus.add_middleware(MetricsMiddleware())
    
    # Start priority worker
    await event_bus.start_priority_worker()
    
    # Subscribe with filter
    def filter_high_priority(event: Event) -> bool:
        return event.priority in [EventPriority.HIGH, EventPriority.CRITICAL]
    
    async def handle_user_created(event: Event):
        print(f"Processing user created: {event.data}")

    subscription_id = event_bus.subscribe(
        topic="user.created",
        handler=handle_user_created,
        filter_func=filter_high_priority,
        priority=10
    )
    
    # Subscribe with throttling
    async def handle_user_activity(event: Event):
        print(f"Processing user activity: {event.data}")

    event_bus.subscribe(
        topic="user.activity",
        handler=handle_user_activity,
        subscription_type=SubscriptionType.THROTTLED,
        config={'throttle_ms': 1000}  # Max once per second
    )
    
    # Publish events
    await event_bus.publish(
        topic="user.created",
        data={"user_id": 123, "name": "John Doe"},
        priority=EventPriority.HIGH,
        source="auth_service"
    )
    
    # Use request-reply pattern
    async def handle_request(event: Event):
        # Process request and send reply
        await event_bus.publish(
            topic=event.reply_to,
            data={"processed": True, "request_id": event.id},
            correlation_id=event.correlation_id
        )
    
    event_bus.subscribe("data.process", handle_request)
    
    async with event_bus.request_reply(
        request_topic="data.process",
        reply_topic="data.processed",
        request_data={"action": "process"}
    ) as reply:
        if reply:
            print(f"Received reply: {reply.data}")
    
    # Get metrics
    metrics = event_bus.get_metrics()
    print(f"Metrics: {metrics}")
    
    # Cleanup
    await event_bus.stop_priority_worker()

if __name__ == "__main__":
    asyncio.run(example_usage())