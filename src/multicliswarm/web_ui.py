import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, List
import json
import threading
import uuid
import sqlite3
import os

from .orchestrator import SwarmOrchestrator
from .schemas import ArchitectResponse

app = FastAPI(title="MultiCliSwarm SOTA Control Panel")

class SwarmRequest(BaseModel):
    task: str
    language: str = "python"
    developer_engines: str = "gemini,codex"
    use_docker: bool = False
    auto_route: bool = True
    context_dir: str = ""
    pair_programming: bool = False

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
            except:
                pass

manager = ConnectionManager()
pending_approvals = {}

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def get_ws_callback():
    def callback(level: str, message: str):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                payload = {"type": "log", "level": level, "message": message}
                loop.create_task(manager.broadcast(payload))
        except Exception:
            pass
    return callback

def ui_ask_approval(task: str, arch: ArchitectResponse) -> bool:
    return True

def ui_ask_code_approval(files_dict: Dict[str, str]) -> Dict[str, str]:
    approval_id = str(uuid.uuid4())
    event = threading.Event()
    pending_approvals[approval_id] = {
        "event": event,
        "files": files_dict
    }
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            payload = {
                "type": "code_approval",
                "approval_id": approval_id,
                "files": files_dict
            }
            loop.create_task(manager.broadcast(payload))
    except Exception:
        pass
        
    event.wait()
    return pending_approvals[approval_id]["files"]

@app.post("/api/approve_code")
async def approve_code(req: CodeApprovalRequest):
    if req.approval_id in pending_approvals:
        pending_approvals[req.approval_id]["files"] = req.files
        pending_approvals[req.approval_id]["event"].set()
        return {"status": "success"}
    return {"status": "error", "message": "Approval ID not found."}

@app.get("/api/sessions")
async def get_sessions():
    DB_PATH = os.path.expanduser("~/.multicliswarm.db")
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, task, timestamp FROM sessions ORDER BY timestamp DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "task": r[1][:50] + "...", "date": r[2]} for r in rows]

@app.post("/api/run")
async def run_swarm(req: SwarmRequest):
    engines = [e.strip() for e in req.developer_engines.split(",")]
    context = req.context_dir if req.context_dir else None
    
    orchestrator = SwarmOrchestrator(
        architect_engine="gemini",
        developer_engines=engines,
        reviewer_engine="gemini",
        synthesizer_engine="gemini",
        debugger_engine="gemini",
        use_docker=req.use_docker,
        auto_route=req.auto_route,
        pair_programming=req.pair_programming,
        callback=get_ws_callback(),
        ask_approval=ui_ask_approval,
        ask_code_approval=ui_ask_code_approval
    )
    
    try:
        result = orchestrator.run(task=req.task, language=req.language, context_dir=context)
        return {
            "status": "success",
            "success": result["success"],
            "files": result["files"],
            "cost_usd": result.get("cost_usd", 0.0),
            "session_id": result["session_id"]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
def read_root():
    html_content = """
    <html>
        <head>
            <title>MultiCliSwarm v0.6.0 - Team Space</title>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.38.0/min/vs/loader.js"></script>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0e0e1a; margin: 0; display: flex; height: 100vh; color: #fff; }
                .sidebar { width: 320px; padding: 20px; background: #1a1a2e; box-shadow: 2px 0 5px rgba(0,0,0,0.5); overflow-y: auto; display: flex; flex-direction: column; gap: 15px;}
                .main { flex-grow: 1; display: flex; flex-direction: column; background: #0e0e1a; }
                .log-box { flex-grow: 1; background: #000; color: #00ff00; padding: 15px; overflow-y: scroll; font-family: 'Fira Code', monospace; font-size: 14px;}
                .editor-box { display: none; flex-grow: 1; flex-direction: column; background: #1e1e1e; }
                #monaco-container { flex-grow: 1; border-top: 1px solid #333; }
                .editor-header { padding: 10px; background: #2a2a3e; color: white; display: flex; justify-content: space-between; align-items: center;}
                input, select { padding: 12px; margin: 0; width: 100%; box-sizing: border-box; border: 1px solid #333; border-radius: 6px; background: #2a2a3e; color: white; }
                button { background-color: #5a32fa; color: white; border: none; cursor: pointer; padding: 12px; border-radius: 6px; font-weight: bold; transition: background 0.3s;}
                button:hover { background-color: #4824d6; }
                .btn-success { background-color: #28a745; }
                .btn-success:hover { background-color: #218838; }
                .sessions-list { margin-top: 20px; border-top: 1px solid #333; padding-top: 15px;}
                .session-item { padding: 10px; background: #2a2a3e; border-radius: 6px; margin-bottom: 10px; cursor: pointer; font-size: 12px;}
                .session-item:hover { background: #3a3a5e; }
                .step { color: #d782ff; font-weight: bold; }
                .success { color: #00ff9d; }
                .warning { color: #ffb86c; }
                .error { color: #ff5555; }
                .info { color: #8be9fd; }
                h2, h3 { margin: 0; color: #fff; }
                label { font-size: 14px; display: flex; align-items: center; gap: 8px;}
            </style>
        </head>
        <body>
            <div class="sidebar">
                <h2>MultiCliSwarm <span style="font-size: 12px; color: #8be9fd;">v0.6.0</span></h2>
                <input type="text" id="task" placeholder="Describe the feature or issue..." />
                <input type="text" id="language" placeholder="Language (go, python, js)" value="python" />
                <input type="text" id="context_dir" placeholder="Local project path for RAG" />
                
                <div style="display:flex; flex-direction:column; gap:8px;">
                    <label><input type="checkbox" id="auto_route" checked> Dynamic Model Routing</label>
                    <label><input type="checkbox" id="pair_programming"> Pair Programming Mode</label>
                    <label><input type="checkbox" id="use_docker"> Docker Sandboxing</label>
                </div>
                
                <button onclick="runSwarm()">Launch Autonomous Swarm</button>
                
                <div class="sessions-list" id="sessions-list">
                    <h3>Team Session History</h3>
                    <div id="session-items"></div>
                </div>
            </div>
            
            <div class="main">
                <div id="logs" class="log-box"></div>
                
                <div id="editor-wrapper" class="editor-box">
                    <div class="editor-header">
                        <span>Review & Edit Generated Code: <select id="file-select" onchange="switchFile()"></select></span>
                        <button class="btn-success" style="width: auto; margin:0;" onclick="submitCodeApproval()">Approve & Deploy</button>
                    </div>
                    <div id="monaco-container"></div>
                </div>
            </div>
            
            <script>
                var ws = new WebSocket("ws://" + window.location.host + "/ws/logs");
                var monacoEditor = null;
                var currentApprovalId = null;
                var currentFiles = {};
                var activeFile = null;

                require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.38.0/min/vs' }});
                require(['vs/editor/editor.main'], function() {
                    monacoEditor = monaco.editor.create(document.getElementById('monaco-container'), {
                        value: '',
                        language: 'python',
                        theme: 'vs-dark'
                    });
                    
                    monacoEditor.onDidChangeModelContent((e) => {
                        if (activeFile) {
                            currentFiles[activeFile] = monacoEditor.getValue();
                        }
                    });
                });

                ws.onmessage = function(event) {
                    var data = JSON.parse(event.data);
                    
                    if (data.type === 'log') {
                        var logs = document.getElementById('logs');
                        var span = document.createElement('span');
                        span.className = data.level;
                        span.innerHTML = "[" + data.level.toUpperCase() + "] " + data.message + "<br/>";
                        logs.appendChild(span);
                        logs.scrollTop = logs.scrollHeight;
                    } 
                    else if (data.type === 'code_approval') {
                        document.getElementById('logs').style.display = 'none';
                        document.getElementById('editor-wrapper').style.display = 'flex';
                        
                        currentApprovalId = data.approval_id;
                        currentFiles = data.files;
                        
                        var select = document.getElementById('file-select');
                        select.innerHTML = '';
                        for (var fname in currentFiles) {
                            var opt = document.createElement('option');
                            opt.value = fname;
                            opt.innerHTML = fname;
                            select.appendChild(opt);
                        }
                        
                        activeFile = Object.keys(currentFiles)[0];
                        monacoEditor.setValue(currentFiles[activeFile]);
                    }
                };

                function switchFile() {
                    activeFile = document.getElementById('file-select').value;
                    monacoEditor.setValue(currentFiles[activeFile]);
                }

                async function submitCodeApproval() {
                    document.getElementById('editor-wrapper').style.display = 'none';
                    document.getElementById('logs').style.display = 'block';
                    
                    await fetch('/api/approve_code', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ approval_id: currentApprovalId, files: currentFiles })
                    });
                    loadSessions();
                }
                
                async function runSwarm() {
                    document.getElementById('logs').innerHTML = "";
                    var task = document.getElementById('task').value;
                    var lang = document.getElementById('language').value;
                    var ctx = document.getElementById('context_dir').value;
                    var route = document.getElementById('auto_route').checked;
                    var pair = document.getElementById('pair_programming').checked;
                    var docker = document.getElementById('use_docker').checked;
                    
                    fetch('/api/run', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ task: task, language: lang, use_docker: docker, auto_route: route, context_dir: ctx, pair_programming: pair })
                    });
                }
                
                async function loadSessions() {
                    const res = await fetch('/api/sessions');
                    const sessions = await res.json();
                    let html = '';
                    for(let s of sessions) {
                        html += `<div class="session-item" title="${s.id}"><b>${s.date.split(' ')[0]}</b>: ${s.task}</div>`;
                    }
                    document.getElementById('session-items').innerHTML = html;
                }
                
                // Init load
                loadSessions();
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

def main():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)

if __name__ == "__main__":
    main()
