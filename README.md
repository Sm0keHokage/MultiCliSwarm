# Multi-CLI Swarm (TPROrchestrator)

Multi-CLI Swarm is a professional, **universal (language-agnostic)** implementation of the **MARE (Multi-Agent Refinement & Evaluation)** algorithm. It orchestrates a cooperative team of localized AI CLI models (`gemini`, `codex`, and optionally `claude`) using the principles of **Theory of Decision Making (TTPR)**, **Game Theory (Minimax peer review)**, and **Condorcet's Jury Theorem (Wisdom of the Crowd)**.

This framework is built as a **modular Python package (SDK)**, allowing seamless integration into any external system, web service, IDE, or CI/CD pipeline. It generates, peer-reviews, and auto-debugs code in **any programming language** (Python, JavaScript, TypeScript, Go, Rust, and more).

---

## 🚀 State-of-the-Art Enterprise Features (v0.4.0)

With the release of v0.4.0, Multi-CLI Swarm rivals commercial AI software engineers (like Devin or Cosine) by bringing advanced autonomy and transparency to your local workspace:

* **🧠 Smart Codebase RAG:** Pass `--context-dir` to let the Architect automatically scan your existing project (respecting `.gitignore`), read key files, and seamlessly integrate new features into your massive legacy codebases.
* **🔀 Dynamic Smart Routing:** Use `--auto-route` to automatically assign cheap, fast models (like `gemini-flash` or local `Llama 3`) to draft code, while reserving expensive reasoning models (like `claude-3.5-sonnet`) for architecture, peer-review, and debugging. Save up to 70% on token costs!
* **🖋️ Interactive Web Diff-Editor:** In the Web UI, before code is saved and tested, an interactive Monaco Editor pops up. Visually compare the AI's drafts, tweak the code by hand, and hit "Approve & Continue"!
* **📊 OpenTelemetry Tracing (Phoenix / Jaeger):** Pass `--telemetry` to trace every agent's thought process, duration, and token usage using the industry standard OTLP protocol. Perfect for debugging the Swarm's logic.
* **👤 Human-in-the-Loop (HITL):** Approvals gate after the Architecture phase to prevent costly hallucinations before code generation begins.
* **📂 Multi-file Architecture:** Generates entire microservices or component structures at once using dynamically mapped file trees.
* **✨ Auto-Formatting & Linting:** Automatically runs native formatters (`black`, `prettier`, `gofmt`, `cargo fmt`) to ensure code matches industry standards.
* **💾 Session Persistence (SQLite):** Remembers previous architecture specs and generated code so you can `--resume` and iteratively improve your project!
* **🔌 IDE Integration (MCP Server):** Directly integrate the Swarm into Cursor, Claude Desktop, and Windsurf via the Model Context Protocol.
* **🛡️ Secure Docker Sandboxing:** Execute unit tests and debug loops safely within isolated Docker containers to protect your local environment.

---

## 📐 Architecture / Swarm Pipeline

```
                     [User Task / Prompt] + [RAG Context]
                              │
                              ▼
                ┌───────────────────────────┐
                │     Step 1: Architect     │ (Designs multi-file plan & tests)
                └─────────────┬─────────────┘
                              │
                        [ 👤 HITL Approval ]
                              │
                              ▼
                ┌───────────────────────────┐
                │  Step 2: Developers (||)  │ (Concurrently write drafts. Cheap Models if routed)
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
                  [ 🖋️ Web Diff-Editor Approval ]
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
        │   Step 6: Debugger    │ (Traced to OpenTelemetry)
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

### 1. Terminal CLI Mode
Execute the swarm using the installed package command `multicliswarm`.
```bash
multicliswarm \
  --task "Write a python class to calculate the nth Fibonacci number." \
  --language "python" \
  --auto-route \
  --telemetry \
  --context-dir "./src"
```

### 1.1 Resuming a Session (Iterative Development)
You can build upon previous generation sessions (stored in `~/.multicliswarm.db`):
```bash
multicliswarm --resume "your-session-uuid-here" --task "Add a new method to clear the cache."
```

### 2. Web UI Dashboard Mode (with Interactive Diff)
Start the live visual dashboard to interact with the swarm via your browser.
```bash
multicliswarm-ui
# Open http://127.0.0.1:8080 in your browser
```

### 3. MCP Server Mode (Cursor / Claude Desktop Integration)
You can expose the swarm as an MCP Tool. Add this to your IDE configs:
```json
{
  "mcpServers": {
    "multicliswarm": {
      "command": "multicliswarm-mcp"
    }
  }
}
```

---

## 🔌 Registering Custom CLI Engines (e.g., Ollama or custom scripts)

You can register *any* CLI command dynamically!

**Ollama Example:**
```bash
multicliswarm \
  --register-engine "local_llama=ollama run llama3" \
  --developer-engines "gemini,local_llama" \
  --task "Write a bubble sort in Python"
```
