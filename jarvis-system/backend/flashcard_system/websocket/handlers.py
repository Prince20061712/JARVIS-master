from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
from api.websocket.events import WSEvent, EventType
from utils.logger import logger
import json
import time

class ConnectionManager:
    """Manages active WebSocket connections."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, event: WSEvent):
        json_msg = event.to_json()
        for connection in self.active_connections:
            await connection.send_text(json_msg)

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                event = WSEvent.from_json(data)
                await handle_event(event, websocket)
            except Exception as e:
                logger.error(f"Error parsing WS event: {e}")
                err_event = WSEvent(type=EventType.ERROR, data={"detail": "Invalid event format"})
                await websocket.send_text(err_event.to_json())
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def handle_event(event: WSEvent, websocket: WebSocket):
    """Routes WebSocket events to appropriate handlers."""
    logger.debug(f"Handling WS event: {event.type}")
    
    if event.type == EventType.HEARTBEAT:
        pong = WSEvent(type=EventType.HEARTBEAT, data={"status": "alive"}, timestamp=time.time())
        await websocket.send_text(pong.to_json())
    
    elif event.type == EventType.NEW_QUERY:
        # In a real app, this would trigger the core engine's reactive pipeline
        logger.info(f"Received query via WS: {event.data.get('query')}")
        
    elif event.type == EventType.EMOTION_UPDATE:
        # Pass to multimodal fusion or state tracker
        pass
