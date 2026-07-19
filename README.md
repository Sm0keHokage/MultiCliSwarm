# Multi-CLI Swarm (TPROrchestrator)

Multi-CLI Swarm is a professional, **universal (language-agnostic)** implementation of the **MARE (Multi-Agent Refinement & Evaluation)** algorithm. It orchestrates a cooperative team of localized AI CLI models (`gemini`, `codex`, and optionally `claude`) using the principles of **Theory of Decision Making (TTPR)**, **Game Theory (Minimax peer review)**, and **Condorcet's Jury Theorem (Wisdom of the Crowd)**.

This framework is built as a **modular Python package (SDK)**, allowing seamless integration into any external system, web service, IDE, or CI/CD pipeline. It generates, peer-reviews, and auto-debugs code in **any programming language** (Python, JavaScript, TypeScript, Go, Rust, and more).

---

## 🚀 Enterprise Key Features (v0.3.0)

* **👤 Human-in-the-Loop (HITL):** Approvals gate after the Architecture phase to prevent costly hallucinations before code generation begins.
* **📂 Multi-file Architecture:** Generates entire microservices or component structures at once using dynamically mapped file trees.
* **✨ Auto-Formatting & Linting:** Automatically runs native formatters (`black`, `prettier`, `gofmt`, `cargo fmt`) to ensure code matches industry standards.
* **💾 Session Persistence (SQLite):** Remembers previous architecture specs and generated code so you can `--resume` and iteratively improve your project!
* **🔌 IDE Integration (MCP Server):** Directly integrate the Swarm into Cursor, Claude Desktop, and Windsurf via the Model Context Protocol.
* **🛡️ Secure Docker Sandboxing:** Execute unit tests and debug loops safely within isolated Docker containers to protect your local environment.
* **💰 Cost & Token Tracking:** Real-time tracking and calculation of LLM API costs for every swarm session.
* **🌐 Web Dashboard (FastAPI + WebSockets):** Watch the agent swarm debate and code in real-time through an interactive web UI.
* **✅ Pydantic Strict Validation:** All AI reasoning is strictly schema-validated to prevent parsing errors and hallucinations.
* **🔑 Zero-Config Authentication:** Automatically uses your existing local authentication sessions from your CLI tools.
* **🌍 Universal Language Support:** Fully language-agnostic. Generate and verify code for **Python, JS, TS, Go, Rust, C++, Java**, etc.
* **🔌 Dynamic Custom CLI Engines:** Register *any* local command-line interface (e.g., Ollama, curl scripts) as a dynamic engine!

---

## 📐 Architecture / Swarm Pipeline

```
                     [User Task / Prompt]
                              │
                              ▼
                ┌───────────────────────────┐
                │     Step 1: Architect     │ (Designs multi-file plan & tests in language L)
                └─────────────┬─────────────┘
                              │
                        [ 👤 HITL Approval ]
                              │
                              ▼
                ┌───────────────────────────┐
                │  Step 2: Developers (||)  │ (Concurrently write draft code for ALL files)
                │  [Gemini, Codex, Claude]  │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │     Step 3: Reviewer      │ (Critiques drafts, finds language edge cases)
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │    Step 4: Synthesizer    │ (Blends best designs into final files)
                └─────────────┬─────────────┘
                              │
                     [ ✨ Auto-Formatting ]
                              │
                              ▼
                ┌───────────────────────────┐
                │  Step 5: Test Execution   │ (Runs native test command in DOCKER container)
                └─────────────┬─────────────┘
                              │
                    ┌─────────┴─────────┐
             Tests Failed         Tests Passed
                    │                   │
                    ▼                   ▼
        ┌───────────────────────┐  [Completed Project]
        │   Step 6: Debugger    │ (Saved to SQLite DB)
        └───────────┬───────────┘
                    ▲ (Fixes code and retries)
```

---

## 💻 Installation & Requirements

Ensure you have Python 3.8+ and at least one or more of the following CLI tools installed:
1. **Gemini CLI** (`gemini`)
2. **Codex CLI** (`codex`)
3. **Claude Code** (`claude`)

### Installation (as a local package):
```bash
# Clone the repo and install
git clone https://github.com/Sm0keHokage/MultiCliSwarm.git
cd MultiCliSwarm
pip install -e .
```

---

## ⚙️ Usage Modes

The SDK provides multiple ways to interact with the Swarm.

### 1. Terminal CLI Mode
You can execute the swarm using the installed package command `multicliswarm`.
```bash
multicliswarm \
  --task "Write a python class to calculate the nth Fibonacci number using memoization, with validation." \
  --language "python" \
  --developer-engines "gemini,codex"
```

### 1.1 Resuming a Session (Iterative Development)
You can build upon previous generation sessions (stored in `~/.multicliswarm.db`):
```bash
multicliswarm --resume "your-session-uuid-here" --task "Add a new method to clear the Fibonacci cache."
```

### 2. Web UI Dashboard Mode
Start the live visual dashboard to interact with the swarm via your browser.
```bash
multicliswarm-ui
# Open http://127.0.0.1:8080 in your browser
```

### 3. MCP Server Mode (Cursor / Claude Desktop Integration)
You can expose the swarm as an MCP Tool. Add this to your `claude_desktop_config.json` or Cursor settings:
```json
{
  "mcpServers": {
    "multicliswarm": {
      "command": "multicliswarm-mcp"
    }
  }
}
```
Now you can type `@MultiCliSwarm write me a rust API` in your IDE chat!

---

## 🔌 Integrating as an SDK

Because **Multi-CLI Swarm** is structured as a standard Python package, other backend services can easily import and run it with Docker sandboxing enabled:

```python
from multicliswarm import SwarmOrchestrator, register_custom_engine

# Setup callback to receive real-time streaming updates
def my_status_callback(level, message):
    print(f"[{level.upper()}] {message}")

# Initialize and run with Docker isolation enabled
orchestrator = SwarmOrchestrator(
    architect_engine="gemini",
    developer_engines=["gemini", "codex"],
    use_docker=True,
    callback=my_status_callback
)

result = orchestrator.run(
    task="Create a secure JWT authentication middleware in Go",
    language="go"
)

if result["success"]:
    print(f"Total Cost: ${result['cost_usd']:.4f}")
```

---

## 🧠 Scientific Foundations

1. **Condorcet's Jury Theorem (Wisdom of the Crowd):**
   When multiple independent estimators (models) each have an accuracy greater than $0.5$, the probability that a majority vote yields the correct solution increases towards $1.0$ as the number of estimators increases.
2. **Asymmetric Minimax Game (Peer Review):**
   In software development, finding bugs is mathematically less computationally complex than drafting a solution from scratch. We establish a stable Nash Equilibrium where the final code has no obvious bugs.
3. **Self-Healing Loop (Docker Execution):**
   A major flaw of LLMs is hallucinations. We anchor the models to reality by executing the generated test cases safely in an isolated Alpine container and returning real runtime exception tracebacks back to a debugger agent.
