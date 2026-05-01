from fastapi import WebSocket, WebSocketDisconnect

from api import app
from api.state import jobs


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault(job_id, []).append(websocket)

    def disconnect(self, job_id: str, websocket: WebSocket):
        if job_id in self.connections:
            self.connections[job_id].remove(websocket)
            if not self.connections[job_id]:
                del self.connections[job_id]

    async def send_progress(self, job_id: str, message: dict):
        for ws in self.connections.get(job_id, []):
            await ws.send_json(message)

manager = ConnectionManager()

@app.websocket("/scan-jobs/{job_id}/ws")
async def scan_job_ws(websocket: WebSocket, job_id: str):
    await manager.connect(job_id, websocket)
    try:
        if job_id in jobs:
            await websocket.send_json(jobs[job_id])

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)