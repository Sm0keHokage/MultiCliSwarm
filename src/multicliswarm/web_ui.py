import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any
import json
import threading
import uuid

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
    # Auto-approve architecture in UI for now to focus on the Code Diff Editor
    return True

def ui_ask_code_approval(files_dict: Dict[str, str]) -> Dict[str, str]:
    approval_id = str(uuid.uuid4())
    event = threading.Event()
    pending_approvals[approval_id] = {
        "event": event,
        "files": files_dict
    }
    
    # Send a message to the frontend to open the diff editor
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
        
    # Block the orchestrator thread until the user submits via the REST API
    event.wait()
    return pending_approvals[approval_id]["files"]

@app.post("/api/approve_code")
async def approve_code(req: CodeApprovalRequest):
    if req.approval_id in pending_approvals:
        pending_approvals[req.approval_id]["files"] = req.files
        pending_approvals[req.approval_id]["event"].set()
        return {"status": "success"}
    return {"status": "error", "message": "Approval ID not found."}

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
        callback=get_ws_callback(),
        ask_approval=ui_ask_approval,
        ask_code_approval=ui_ask_code_approval
    )
    
    try:
        # Note: running in the same thread blocks FastAPI workers. In a prod app, wrap in thread.
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
            <title>MultiCliSwarm SOTA Control Panel</title>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.38.0/min/vs/loader.js"></script>
            <style>
                body { font-family: sans-serif; background-color: #f4f4f9; margin: 0; display: flex; height: 100vh; }
                .sidebar { width: 300px; padding: 20px; background: white; box-shadow: 2px 0 5px rgba(0,0,0,0.1); overflow-y: auto; }
                .main { flex-grow: 1; display: flex; flex-direction: column; }
                .log-box { flex-grow: 1; background: #1e1e1e; color: #00ff00; padding: 10px; overflow-y: scroll; font-family: monospace; }
                .editor-box { display: none; flex-grow: 1; flex-direction: column; background: #fff; }
                #monaco-container { flex-grow: 1; border-top: 1px solid #ccc; }
                .editor-header { padding: 10px; background: #333; color: white; display: flex; justify-content: space-between; align-items: center;}
                input, button { padding: 10px; margin: 5px 0; width: 100%; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }
                button { background-color: #007bff; color: white; border: none; cursor: pointer; }
                button:hover { background-color: #0056b3; }
                .btn-success { background-color: #28a745; }
                .step { color: #ff00ff; font-weight: bold; }
                .success { color: #00ff00; }
                .warning { color: #ffff00; }
                .error { color: #ff0000; }
                .info { color: #00ffff; }
            </style>
        </head>
        <body>
            <div class="sidebar">
                <h2>MultiCliSwarm</h2>
                <input type="text" id="task" placeholder="Task description..." />
                <input type="text" id="language" placeholder="Language (go, python...)" value="python" />
                <input type="text" id="context_dir" placeholder="RAG Context Dir (optional)" />
                <label><input type="checkbox" id="auto_route" checked> Enable Smart Routing</label><br>
                <label><input type="checkbox" id="use_docker"> Use Docker Sandbox</label>
                <button onclick="runSwarm()">Launch Swarm</button>
            </div>
            
            <div class="main">
                <div id="logs" class="log-box"></div>
                
                <div id="editor-wrapper" class="editor-box">
                    <div class="editor-header">
                        <span>Review Generated Code: <select id="file-select" onchange="switchFile()"></select></span>
                        <button class="btn-success" style="width: auto; margin:0;" onclick="submitCodeApproval()">Approve & Continue</button>
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
                }
                
                async function runSwarm() {
                    document.getElementById('logs').innerHTML = "";
                    var task = document.getElementById('task').value;
                    var lang = document.getElementById('language').value;
                    var ctx = document.getElementById('context_dir').value;
                    var route = document.getElementById('auto_route').checked;
                    var docker = document.getElementById('use_docker').checked;
                    
                    fetch('/api/run', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ task: task, language: lang, use_docker: docker, auto_route: route, context_dir: ctx })
                    });
                }
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
