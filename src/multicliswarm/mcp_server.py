import logging
from mcp.server.fastapi import McpServer
from .orchestrator import SwarmOrchestrator

logger = logging.getLogger("multicliswarm.mcp")

# Create the MCP Server instance
app = McpServer("MultiCliSwarm")

@app.tool()
def run_swarm_orchestration(task: str, language: str = "python", use_docker: bool = False) -> str:
    """
    Executes the Multi-CLI Swarm agentic loop to generate, cross-review, and auto-test code.
    
    Args:
        task: The detailed coding task description.
        language: The target programming language (e.g. python, javascript, go).
        use_docker: If true, runs the generated tests safely inside an isolated Docker container.
    """
    logger.info(f"MCP Call: run_swarm_orchestration(task='{task}', language='{language}')")
    
    # Callback to stream back logs or print them locally
    def local_callback(level, message):
        print(f"[{level.upper()}] {message}")

    try:
        orchestrator = SwarmOrchestrator(
            architect_engine="gemini",
            developer_engines=["gemini", "codex"],
            reviewer_engine="gemini",
            synthesizer_engine="gemini",
            debugger_engine="gemini",
            use_docker=use_docker,
            callback=local_callback
        )
        
        result = orchestrator.run(task=task, language=language)
        
        status = "PASSED" if result["success"] else "FAILED (or partially completed)"
        
        report = (
            f"Multi-CLI Swarm Task Completed!\n"
            f"Status: {status}\n"
            f"Cost Estimate: ${result.get('cost_usd', 0.0):.5f} USD\n\n"
            f"--- Generated File: {result['filename']} ---\n"
            f"```\n{result['code']}\n```\n"
        )
        return report
        
    except Exception as e:
        logger.error(f"Swarm orchestration failed: {e}")
        return f"Error executing swarm: {str(e)}"

def main():
    import uvicorn
    # Start the MCP server using FastAPI integration
    logger.info("Starting MultiCliSwarm MCP Server on port 8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
