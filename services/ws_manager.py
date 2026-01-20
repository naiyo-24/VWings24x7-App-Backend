from typing import Dict, Set, Any
from fastapi import WebSocket
import asyncio

class Connection:
    def __init__(self, websocket: WebSocket, user_id: str, role: str):
        self.websocket = websocket
        self.user_id = user_id
        self.role = role


class ConnectionManager:
    def __init__(self):
        # class_id -> set of Connection
        self.active_connections: Dict[str, Set[Connection]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, class_id: str, websocket: WebSocket, user_id: str, role: str):
        conn = Connection(websocket, user_id, role)
        async with self._lock:
            if class_id not in self.active_connections:
                self.active_connections[class_id] = set()
            self.active_connections[class_id].add(conn)
        return conn

    async def disconnect(self, class_id: str, conn: Connection):
        async with self._lock:
            if class_id in self.active_connections:
                self.active_connections[class_id].discard(conn)
                if not self.active_connections[class_id]:
                    del self.active_connections[class_id]

    async def broadcast(self, class_id: str, message: dict):
        conns = []
        async with self._lock:
            if class_id in self.active_connections:
                conns = list(self.active_connections[class_id])
        for c in conns:
            try:
                await c.websocket.send_json(message)
            except Exception:
                # ignore send errors here; client may disconnect
                pass


manager = ConnectionManager()
