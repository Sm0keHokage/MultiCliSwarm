import asyncio
import threading
import uuid
import os
import json
import sqlite3
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .orchestrator import SwarmOrchestrator
from .schemas import ArchitectResponse
from .visualizer import generate_dependency_graph
from .config import settings
from .logging_utils import setup_logging

setup_logging()
logger = logging.getLogger("multicliswarm.web_ui")

app = FastAPI(title="MultiCliSwarm v2.0.0 - Production Control Panel")

# State tracking for active background tasks
active_tasks: Dict[str, Dict[str, Any]] = {}

class SwarmRequest(BaseModel):
    task: str
    language: str = "python"
    developer_engines: str = "gemini,codex"
    use_docker: bool = False
    auto_route: bool = True
    context_dir: str = ""
    pair_programming: bool = False

class ChatMessage(BaseModel):
    message: str

class CodeApprovalRequest(BaseModel):
    approval_id: str
    files: Dict[str, str]

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, payload: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(payload))
            except: pass

manager = ConnectionManager()
live_interventions = {} # session_id -> list

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def get_ws_callback(session_id: str):
    def callback(level: str, message: str):
        try:
            loop = asyncio.get_event_loop()
            payload = {"type": "log", "session_id": session_id, "level": level, "message": message}
            if loop.is_running():
                loop.create_task(manager.broadcast(payload))
        except: pass
    return callback

def ui_ask_code_approval(session_id: str, files_dict: Dict[str, str]) -> Dict[str, str]:
    approval_id = f"appr-{session_id}"
    event = threading.Event()
    active_tasks[session_id]["approval"] = {"event": event, "files": files_dict}
    
    try:
        loop = asyncio.get_event_loop()
        payload = {"type": "code_approval", "session_id": session_id, "approval_id": approval_id, "files": files_dict}
        if loop.is_running():
            loop.create_task(manager.broadcast(payload))
    except: pass
        
    event.wait()
    return active_tasks[session_id]["approval"]["files"]

def ui_chat_interrupt(session_id: str) -> Optional[str]:
    if session_id in live_interventions and live_interventions[session_id]:
        return live_interventions[session_id].pop(0)
    return None

def run_swarm_background(session_id: str, req: SwarmRequest):
    """Execution wrapper for background thread."""
    engines = [e.strip() for e in req.developer_engines.split(",")]
    
    orchestrator = SwarmOrchestrator(
        architect_engine=settings.DEFAULT_ARCHITECT_ENGINE,
        developer_engines=engines,
        use_docker=req.use_docker,
        auto_route=req.auto_route,
        pair_programming=req.pair_programming,
        callback=get_ws_callback(session_id),
        ask_code_approval=lambda files: ui_ask_code_approval(session_id, files),
        live_chat_interrupt=lambda: ui_chat_interrupt(session_id)
    )
    
    try:
        result = orchestrator.run(task=req.task, language=req.language, context_dir=req.context_dir, resume_session_id=session_id)
        active_tasks[session_id]["result"] = result
        active_tasks[session_id]["status"] = "completed"
    except Exception as e:
        logger.error(f"Background task {session_id} failed: {e}")
        active_tasks[session_id]["status"] = "failed"
        active_tasks[session_id]["error"] = str(e)

@app.post("/api/run")
async def start_run(req: SwarmRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())
    active_tasks[session_id] = {"status": "running", "req": req}
    
    # Run orchestration in a separate thread to keep FastAPI main loop free
    thread = threading.Thread(target=run_swarm_background, args=(session_id, req))
    thread.start()
    
    return {"status": "started", "session_id": session_id}

@app.get("/api/status/{session_id}")
async def get_status(session_id: str):
    if session_id not in active_tasks:
        return {"status": "not_found"}
    return active_tasks[session_id]

@app.post("/api/chat/{session_id}")
async def send_chat(session_id: str, req: ChatMessage):
    if session_id not in live_interventions:
        live_interventions[session_id] = []
    live_interventions[session_id].append(req.message)
    return {"status": "received"}

@app.post("/api/approve_code/{session_id}")
async def approve_code(session_id: str, req: CodeApprovalRequest):
    if session_id in active_tasks and "approval" in active_tasks[session_id]:
        active_tasks[session_id]["approval"]["files"] = req.files
        active_tasks[session_id]["approval"]["event"].set()
        return {"status": "success"}
    return {"status": "error", "message": "Approval pending not found."}

@app.get("/api/sessions")
async def get_sessions():
    if not os.path.exists(settings.DB_PATH): return []
    conn = sqlite3.connect(settings.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, task, timestamp, status FROM sessions ORDER BY timestamp DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "task": r[1][:50] + "...", "date": r[2], "status": r[3]} for r in rows]

@app.get("/")
def read_root():
    # Production: Serve actual static files. For now, keep as string but improved.
    return HTMLResponse(content="<h1>MultiCliSwarm v2.0.0 Production Dashboard</h1><p>Websocket and API active.</p>", status_code=200)

def main():
    import uvicorn
    uvicorn.run(app, host=settings.UI_HOST, port=settings.UI_PORT)

if __name__ == "__main__":
    main()
