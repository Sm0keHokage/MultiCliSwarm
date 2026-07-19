import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import json

from .orchestrator import SwarmOrchestrator

app = FastAPI(title="MultiCliSwarm Control Panel")

class SwarmRequest(BaseModel):
    task: str
    language: str = "python"
    developer_engines: str = "gemini,codex"
    use_docker: bool = False

# In-memory connection manager for WebSocket logs
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def get_ws_callback():
    def callback(level: str, message: str):
        # We need to broadcast asynchronously from a synchronous callback
        # This requires getting the running event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                payload = json.dumps({"level": level, "message": message})
                loop.create_task(manager.broadcast(payload))
        except Exception:
            pass
    return callback

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
        callback=get_ws_callback()
    )
    
    try:
        # Note: orchestrator.run is blocking. In a real heavy-duty async server, 
        # this would be offloaded to run_in_executor.
        result = orchestrator.run(task=req.task, language=req.language)
        return {
            "status": "success",
            "success": result["success"],
            "filename": result["filename"],
            "code": result["code"],
            "cost_usd": result.get("cost_usd", 0.0)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
def read_root():
    html_content = """
    <html>
        <head>
            <title>MultiCliSwarm Control Panel</title>
            <style>
                body { font-family: sans-serif; padding: 20px; background-color: #f4f4f9; }
                .container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
                .log-box { background: #1e1e1e; color: #00ff00; padding: 10px; height: 300px; overflow-y: scroll; font-family: monospace; border-radius: 4px; }
                input, button { padding: 10px; margin: 5px 0; width: 100%; box-sizing: border-box; }
                button { background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background-color: #0056b3; }
                .step { color: #ff00ff; font-weight: bold; }
                .success { color: #00ff00; }
                .warning { color: #ffff00; }
                .error { color: #ff0000; }
                .info { color: #00ffff; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>MultiCliSwarm Control Panel</h2>
                <input type="text" id="task" placeholder="Task description (e.g. Write a JWT middleware)" />
                <input type="text" id="language" placeholder="Language (e.g. go, python, javascript)" value="python" />
                <button onclick="runSwarm()">Launch Swarm</button>
                
                <h3>Live Execution Logs:</h3>
                <div id="logs" class="log-box"></div>
                
                <h3>Result:</h3>
                <pre id="result" style="background:#eee; padding:10px; border-radius:4px;"></pre>
            </div>
            
            <script>
                var ws = new WebSocket("ws://" + window.location.host + "/ws/logs");
                ws.onmessage = function(event) {
                    var data = JSON.parse(event.data);
                    var logs = document.getElementById('logs');
                    var span = document.createElement('span');
                    span.className = data.level;
                    span.innerHTML = "[" + data.level.toUpperCase() + "] " + data.message + "<br/>";
                    logs.appendChild(span);
                    logs.scrollTop = logs.scrollHeight;
                };
                
                async function runSwarm() {
                    document.getElementById('logs').innerHTML = "";
                    document.getElementById('result').innerHTML = "Running...";
                    var task = document.getElementById('task').value;
                    var lang = document.getElementById('language').value;
                    
                    const response = await fetch('/api/run', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ task: task, language: lang, use_docker: false })
                    });
                    
                    const result = await response.json();
                    document.getElementById('result').innerHTML = JSON.stringify(result, null, 2);
                }
            </script>
        </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content, status_code=200)

def main():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)

if __name__ == "__main__":
    main()
