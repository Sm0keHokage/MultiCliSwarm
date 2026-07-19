from fastapi import FastAPI, Request
import subprocess
import uvicorn
import logging

app = FastAPI(title="MultiCliSwarm IDE Bridge")
logger = logging.getLogger("multicliswarm.bridge")

@app.post("/run")
async def run_from_ide(req: Request):
    """
    Receives task from IDE (VS Code / JetBrains).
    Triggered via a curl or simple fetch from extension.
    """
    data = await req.json()
    task = data.get("task")
    lang = data.get("language", "python")
    
    # Run the multicliswarm CLI tool in a detached process or wait for it
    # For a bridge, we often want to stream logs back, but here we just trigger
    logger.info(f"IDE Bridge: Received task '{task}'")
    
    cmd = ["multicliswarm", "-t", task, "-l", lang, "--auto-route", "--auto-approve"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {"status": "success", "output": result.stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    uvicorn.run(app, host="127.0.0.1", port=9999)

if __name__ == "__main__":
    main()
