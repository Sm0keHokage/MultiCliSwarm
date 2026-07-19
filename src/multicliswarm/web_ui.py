import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import threading
import uuid
import sqlite3
import os

from .orchestrator import SwarmOrchestrator
from .schemas import ArchitectResponse
from .visualizer import generate_dependency_graph

app = FastAPI(title="MultiCliSwarm v1.2.0 - Elite Control Panel")

class SwarmRequest(BaseModel):
    task: str
    language: str = "python"
    developer_engines: str = "gemini,codex"
    use_docker: bool = False
    auto_route: bool = True
    context_dir: str = ""
    pair_programming: bool = False
    semantic_rag: bool = True
    semantic_cache: bool = True
    performance_bench: bool = True
    reviewer_consensus: bool = True
    security_audit: bool = True
    auto_docs: bool = True

class CodeApprovalRequest(BaseModel):
    approval_id: str
    files: Dict[str, str]

class ChatMessage(BaseModel):
    message: str

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
live_interventions = [] # Queue for the current session

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

def ui_ask_code_approval(files_dict: Dict[str, str]) -> Dict[str, str]:
    approval_id = str(uuid.uuid4())
    event = threading.Event()
    pending_approvals[approval_id] = {"event": event, "files": files_dict}
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            payload = {"type": "code_approval", "approval_id": approval_id, "files": files_dict}
            loop.create_task(manager.broadcast(payload))
    except Exception: pass
        
    event.wait()
    return pending_approvals[approval_id]["files"]

def ui_chat_interrupt() -> Optional[str]:
    if live_interventions:
        return live_interventions.pop(0)
    return None

@app.post("/api/chat")
async def send_chat(req: ChatMessage):
    live_interventions.append(req.message)
    return {"status": "received"}

@app.post("/api/approve_code")
async def approve_code(req: CodeApprovalRequest):
    if req.approval_id in pending_approvals:
        pending_approvals[req.approval_id]["files"] = req.files
        pending_approvals[req.approval_id]["event"].set()
        return {"status": "success"}
    return {"status": "error"}

@app.get("/api/visualize")
async def get_viz(project_dir: str = "."):
    return generate_dependency_graph(project_dir)

@app.get("/api/sessions")
async def get_sessions():
    DB_PATH = os.path.expanduser("~/.multicliswarm.db")
    if not os.path.exists(DB_PATH): return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, task, timestamp FROM sessions ORDER BY timestamp DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "task": r[1][:50] + "...", "date": r[2]} for r in rows]

@app.post("/api/run")
async def run_swarm(req: SwarmRequest):
    engines = [e.strip() for e in req.developer_engines.split(",")]
    
    orchestrator = SwarmOrchestrator(
        architect_engine="gemini",
        developer_engines=engines,
        reviewer_engine="gemini",
        synthesizer_engine="gemini",
        debugger_engine="gemini",
        use_docker=req.use_docker,
        auto_route=req.auto_route,
        pair_programming=req.pair_programming,
        semantic_rag=req.semantic_rag,
        semantic_cache=req.semantic_cache,
        performance_bench=req.performance_bench,
        reviewer_consensus=req.reviewer_consensus,
        security_audit=req.security_audit,
        auto_docs=req.auto_docs,
        callback=get_ws_callback(),
        ask_code_approval=ui_ask_code_approval,
        live_chat_interrupt=ui_chat_interrupt
    )
    
    try:
        # In a real async app, run in thread. Blocking for now as per previous logic.
        result = orchestrator.run(task=req.task, language=req.language, context_dir=req.context_dir)
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
            <title>MultiCliSwarm v1.2.0 - Ascension Suite</title>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.38.0/min/vs/loader.js"></script>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body { font-family: 'Inter', sans-serif; background-color: #05050a; margin: 0; display: flex; height: 100vh; color: #e0e0e0; }
                .sidebar { width: 340px; padding: 25px; background: #0c0c16; border-right: 1px solid #1e1e2e; overflow-y: auto; display: flex; flex-direction: column; gap: 20px;}
                .main { flex-grow: 1; display: flex; flex-direction: column; background: #05050a; }
                .log-box { flex-grow: 1; background: #000; color: #00ffaa; padding: 20px; overflow-y: scroll; font-family: 'JetBrains Mono', monospace; font-size: 13px; line-height: 1.5; border-bottom: 1px solid #1e1e2e; }
                .chat-box { height: 60px; background: #0c0c16; padding: 10px; display: flex; gap: 10px; border-top: 1px solid #1e1e2e;}
                .editor-box { display: none; flex-grow: 1; flex-direction: column; background: #1e1e1e; }
                #monaco-container { flex-grow: 1; }
                .tab-bar { display: flex; background: #0c0c16; border-bottom: 1px solid #1e1e2e;}
                .tab { padding: 12px 25px; cursor: pointer; border-bottom: 2px solid transparent; transition: 0.3s; font-size: 14px; font-weight: 500;}
                .tab.active { border-bottom: 2px solid #5a32fa; color: #fff; background: #16162a; }
                input, select { padding: 12px; width: 100%; box-sizing: border-box; border: 1px solid #1e1e2e; border-radius: 8px; background: #16162a; color: white; outline: none;}
                button { background: linear-gradient(135deg, #5a32fa 0%, #4824d6 100%); color: white; border: none; cursor: pointer; padding: 12px; border-radius: 8px; font-weight: 600; transition: transform 0.2s;}
                button:hover { transform: translateY(-2px); }
                .session-item { padding: 12px; background: #16162a; border-radius: 8px; margin-bottom: 12px; cursor: pointer; font-size: 13px; border: 1px solid #1e1e2e;}
                .session-item:hover { border-color: #5a32fa; }
                .step { color: #ff00ff; } .success { color: #00ffaa; } .warning { color: #ffaa00; } .info { color: #00ccff; }
                #viz-container { width: 100%; height: 100%; display: none; position: relative;}
                circle { fill: #5a32fa; stroke: #fff; stroke-width: 1.5px; }
                line { stroke: #444; stroke-opacity: 0.6; stroke-width: 1px; }
                text { font-size: 10px; fill: #ccc; pointer-events: none; }
            </style>
        </head>
        <body>
            <div class="sidebar">
                <h1 style="font-size: 22px; margin: 0; background: linear-gradient(to right, #8be9fd, #bd93f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Swarm Elite <span style="font-size: 12px; color: #6272a4;">v1.2.0</span></h1>
                <input type="text" id="task" placeholder="Task for the Swarm..." />
                <input type="text" id="language" placeholder="Language (go, py, js...)" value="python" />
                <input type="text" id="context_dir" placeholder="Context directory (RAG)" />
                
                <div style="font-size: 12px; color: #6272a4;">Production Features:</div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                    <label><input type="checkbox" id="auto_route" checked> Route</label>
                    <label><input type="checkbox" id="semantic_rag" checked> RAG</label>
                    <label><input type="checkbox" id="security_audit" checked> Security</label>
                    <label><input type="checkbox" id="performance_bench" checked> Bench</label>
                    <label><input type="checkbox" id="pair_programming"> Pair</label>
                    <label><input type="checkbox" id="use_docker"> Docker</label>
                </div>
                
                <button onclick="runSwarm()">🚀 Deploy Swarm</button>
                
                <div id="session-items"></div>
            </div>
            
            <div class="main">
                <div class="tab-bar">
                    <div class="tab active" onclick="showTab('logs')">Live Logs</div>
                    <div class="tab" onclick="showTab('editor')">Review Code</div>
                    <div class="tab" onclick="showTab('viz')">Architecture Map</div>
                </div>
                
                <div id="logs" class="log-box"></div>
                <div id="viz-container"></div>
                
                <div id="editor-wrapper" class="editor-box">
                    <div style="padding:10px; background:#16162a; display:flex; justify-content:space-between;">
                        <select id="file-select" style="width:250px;" onchange="switchFile()"></select>
                        <button class="btn-success" onclick="submitCodeApproval()">Accept & Finalize</button>
                    </div>
                    <div id="monaco-container"></div>
                </div>

                <div class="chat-box">
                    <input type="text" id="chat-input" placeholder="Interrupt swarm / Send instruction..." />
                    <button style="width: 100px;" onclick="sendChat()">Send</button>
                </div>
            </div>
            
            <script>
                var ws = new WebSocket("ws://" + window.location.host + "/ws/logs");
                var monacoEditor = null;
                var currentFiles = {};
                var activeFile = null;

                require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.38.0/min/vs' }});
                require(['vs/editor/editor.main'], function() {
                    monacoEditor = monaco.editor.create(document.getElementById('monaco-container'), {
                        value: '', language: 'python', theme: 'vs-dark'
                    });
                    monacoEditor.onDidChangeModelContent(() => { if(activeFile) currentFiles[activeFile] = monacoEditor.getValue(); });
                });

                ws.onmessage = function(event) {
                    var data = JSON.parse(event.data);
                    if (data.type === 'log') {
                        var logs = document.getElementById('logs');
                        logs.innerHTML += `<span class="${data.level}">[${data.level.toUpperCase()}] ${data.message}</span><br/>`;
                        logs.scrollTop = logs.scrollHeight;
                    } 
                    else if (data.type === 'code_approval') {
                        showTab('editor');
                        currentFiles = data.files;
                        var select = document.getElementById('file-select');
                        select.innerHTML = '';
                        for (var f in currentFiles) {
                            var opt = document.createElement('option'); opt.value = f; opt.innerHTML = f; select.appendChild(opt);
                        }
                        activeFile = Object.keys(currentFiles)[0];
                        monacoEditor.setValue(currentFiles[activeFile]);
                    }
                };

                function showTab(name) {
                    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                    event.target.classList.add('active');
                    document.getElementById('logs').style.display = name === 'logs' ? 'block' : 'none';
                    document.getElementById('editor-wrapper').style.display = name === 'editor' ? 'flex' : 'none';
                    document.getElementById('viz-container').style.display = name === 'viz' ? 'block' : 'none';
                    if(name === 'viz') runViz();
                }

                async function sendChat() {
                    var input = document.getElementById('chat-input');
                    await fetch('/api/chat', { method: 'POST', body: JSON.stringify({ message: input.value }), headers: {'Content-Type': 'application/json'} });
                    input.value = '';
                }

                async function submitCodeApproval() {
                    showTab('logs');
                    await fetch('/api/approve_code', { method: 'POST', body: JSON.stringify({ approval_id: currentApprovalId, files: currentFiles }), headers: {'Content-Type': 'application/json'} });
                }

                function runViz() {
                    var width = document.getElementById('viz-container').clientWidth;
                    var height = document.getElementById('viz-container').clientHeight;
                    d3.select("#viz-container svg").remove();
                    var svg = d3.select("#viz-container").append("svg").attr("width", width).attr("height", height);
                    
                    fetch('/api/visualize').then(r => r.json()).then(data => {
                        var simulation = d3.forceSimulation(data.nodes).force("link", d3.forceLink(data.links).id(d) => d.id).force("charge", d3.forceManyBody().strength(-100)).force("center", d3.forceCenter(width/2, height/2));
                        var link = svg.append("g").selectAll("line").data(data.links).enter().append("line");
                        var node = svg.append("g").selectAll("circle").data(data.nodes).enter().append("circle").attr("r", 8).call(d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended));
                        node.append("title").text(d => d.label);
                        simulation.on("tick", () => {
                            link.attr("x1", d => d.source.x).attr("y1", d => d.source.y).attr("x2", d => d.target.x).attr("y2", d => d.target.y);
                            node.attr("cx", d => d.x).attr("cy", d => d.y);
                        });
                        function dragstarted(event, d) { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }
                        function dragged(event, d) { d.fx = event.x; d.fy = event.y; }
                        function dragended(event, d) { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }
                    });
                }

                async function runSwarm() {
                    document.getElementById('logs').innerHTML = "";
                    var req = {
                        task: document.getElementById('task').value,
                        language: document.getElementById('language').value,
                        context_dir: document.getElementById('context_dir').value,
                        auto_route: document.getElementById('auto_route').checked,
                        use_docker: document.getElementById('use_docker').checked,
                        semantic_rag: document.getElementById('semantic_rag').checked,
                        security_audit: document.getElementById('security_audit').checked,
                        performance_bench: document.getElementById('performance_bench').checked,
                        pair_programming: document.getElementById('pair_programming').checked
                    };
                    fetch('/api/run', { method: 'POST', body: JSON.stringify(req), headers: {'Content-Type': 'application/json'} });
                }
                
                function switchFile() {
                    activeFile = document.getElementById('file-select').value;
                    monacoEditor.setValue(currentFiles[activeFile]);
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
