import os
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from core.runtime_state import state_manager

dashboard_router = APIRouter()

@dashboard_router.websocket("/api/dashboard/stream")
async def dashboard_stream(websocket: WebSocket):
    await websocket.accept()
    queue = asyncio.Queue()
    state_manager.connections.append(queue)
    try:
        # Send initial state immediately upon connection
        await websocket.send_json({"type": "full_state", "full_state": state_manager.get_state()})
        
        async def read_from_socket():
            while True:
                await websocket.receive_text()
                
        async def write_to_socket():
            while True:
                # Wait for queue with a 1-second timeout to act as a heartbeat
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=1.0)
                    await websocket.send_json(payload)
                except asyncio.TimeoutError:
                    # Heartbeat: Send updated state just to refresh the clock
                    await websocket.send_json({"type": "heartbeat", "full_state": state_manager.get_state()})
                
        await asyncio.gather(read_from_socket(), write_to_socket())
    except Exception:
        pass
    finally:
        if queue in state_manager.connections:
            state_manager.connections.remove(queue)

@dashboard_router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "dashboard", "index.html")
    try:
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard UI not found. Please ensure dashboard/index.html exists.</h1>", status_code=404)
