"""WebSocket module for real-time communication."""

from .events import WSEvent, EventType
from .handlers import ConnectionManager
from .connection_manager import ConnectionManager as ConnManager

__all__ = [
    'WSEvent', 'EventType',
    'ConnectionManager', 'ConnManager'
]
