"""WebSocket connection manager for managing multiple concurrent connections."""

from typing import Dict, Set, Optional, Callable
from fastapi import WebSocket
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections with support for:
    - Multiple concurrent connections
    - Broadcasting messages to specific users or all users
    - Connection lifecycle management
    - Heartbeat/ping-pong handling
    """
    
    def __init__(self, max_connections: int = 100, heartbeat_interval: int = 30):
        """
        Initialize connection manager.
        
        Args:
            max_connections: Maximum concurrent connections
            heartbeat_interval: Heartbeat interval in seconds
        """
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.max_connections = max_connections
        self.heartbeat_interval = heartbeat_interval
        self.connection_metadata: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Register new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
        """
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        if len(self.active_connections[user_id]) >= self.max_connections:
            await websocket.close(code=1008, reason="Max connections exceeded")
            return
        
        self.active_connections[user_id].add(websocket)
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.now(),
            "messages_sent": 0,
            "messages_received": 0
        }
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Unregister WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        if websocket in self.connection_metadata:
            metadata = self.connection_metadata.pop(websocket)
            logger.info(f"User {user_id} disconnected. Messages sent: {metadata['messages_sent']}")
    
    async def broadcast(self, message: dict, user_id: Optional[str] = None):
        """
        Broadcast message to all connections or specific user.
        
        Args:
            message: Message to broadcast
            user_id: Target user (None for all)
        """
        if user_id:
            # Broadcast to specific user
            if user_id in self.active_connections:
                for connection in self.active_connections[user_id]:
                    try:
                        await connection.send_json(message)
                        if connection in self.connection_metadata:
                            self.connection_metadata[connection]["messages_sent"] += 1
                    except Exception as e:
                        logger.error(f"Error sending message to {user_id}: {str(e)}")
        else:
            # Broadcast to all users
            for user_conns in self.active_connections.values():
                for connection in user_conns:
                    try:
                        await connection.send_json(message)
                        if connection in self.connection_metadata:
                            self.connection_metadata[connection]["messages_sent"] += 1
                    except Exception as e:
                        logger.error(f"Error broadcasting message: {str(e)}")
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """
        Send message to specific connection.
        
        Args:
            websocket: Target WebSocket
            message: Message to send
        """
        try:
            await websocket.send_json(message)
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["messages_sent"] += 1
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")
    
    def get_connection_count(self, user_id: Optional[str] = None) -> int:
        """
        Get number of active connections.
        
        Args:
            user_id: Specific user (None for total)
        
        Returns:
            Connection count
        """
        if user_id:
            return len(self.active_connections.get(user_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_connected_users(self) -> list:
        """
        Get list of connected user IDs.
        
        Returns:
            List of user IDs
        """
        return list(self.active_connections.keys())
    
    def get_connection_info(self) -> dict:
        """
        Get connection statistics.
        
        Returns:
            Connection information dictionary
        """
        total_connections = self.get_connection_count()
        total_users = len(self.active_connections)
        
        return {
            "total_connections": total_connections,
            "total_users": total_users,
            "max_connections": self.max_connections,
            "connected_users": self.get_connected_users(),
            "average_connections_per_user": (
                total_connections / total_users if total_users > 0 else 0
            )
        }
