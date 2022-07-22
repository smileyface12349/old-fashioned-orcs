import uuid
from typing import List

from fastapi import WebSocket


class ConnectionManager:
    """It handles ALL players websockets"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Generate client's unique ID
        unique_id = uuid.uuid4().hex
        return {"unique_id": unique_id}

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def update(self, websocket: WebSocket):
        payload = await websocket.receive_json()
        return payload
    
    def connections(self):
        return self.active_connections
