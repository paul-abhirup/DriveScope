import asyncio
import json
from typing import Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["WebSockets"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.global_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, run_id: str = None):
        await websocket.accept()
        if run_id:
            if run_id not in self.active_connections:
                self.active_connections[run_id] = set()
            self.active_connections[run_id].add(websocket)
        else:
            self.global_connections.add(websocket)

    def disconnect(self, websocket: WebSocket, run_id: str = None):
        if run_id and run_id in self.active_connections:
            self.active_connections[run_id].discard(websocket)
            if not self.active_connections[run_id]:
                del self.active_connections[run_id]
        self.global_connections.discard(websocket)

    async def broadcast_to_run(self, run_id: str, message: dict):
        payload = json.dumps(message)
        if run_id in self.active_connections:
            for connection in list(self.active_connections[run_id]):
                try:
                    await connection.send_text(payload)
                except Exception:
                    self.disconnect(connection, run_id)
        
        # Also broadcast to global listeners
        for connection in list(self.global_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws/runs/{run_id}")
async def websocket_run_endpoint(websocket: WebSocket, run_id: str):
    await manager.connect(websocket, run_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or handle ping
            await websocket.send_text(json.dumps({"event": "pong", "run_id": run_id}))
    except WebSocketDisconnect:
        manager.disconnect(websocket, run_id)


@router.websocket("/ws/events")
async def websocket_global_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
