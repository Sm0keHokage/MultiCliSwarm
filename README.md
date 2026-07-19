# Multi-CLI Swarm (TPROrchestrator)

Multi-CLI Swarm is a professional, **universal (language-agnostic)** implementation of the **MARE (Multi-Agent Refinement & Evaluation)** algorithm. It orchestrates a cooperative team of localized AI CLI models (`gemini`, `codex`, and optionally `claude`) using the principles of **Theory of Decision Making (TTPR)**, **Game Theory (Minimax peer review)**, and **Condorcet's Jury Theorem (Wisdom of the Crowd)**.

This framework is built as a **modular Python package (SDK)**, allowing seamless integration into any external system, web service, IDE, or CI/CD pipeline. It generates, peer-reviews, and auto-debugs code in **any programming language** (Python, JavaScript, TypeScript, Go, Rust, and more).

---

## 🚀 Autonomous Ecosystem Features (v0.5.0)

With the release of v0.5.0, Multi-CLI Swarm steps into the future, becoming a fully autonomous "Senior Developer in a Box":

* **👁️ Visual QA (Headless Vision):** Use `--visual-qa`. For HTML/frontend tasks, the Swarm automatically boots a headless Playwright browser, takes a screenshot of the rendered page, and sends it to a Vision model to critique UI bugs, overlaps, or styling issues!
* **📦 Autonomous Package Management:** Use `--auto-packages`. The Swarm detects required dependencies (like `package.json` or `requirements.txt`) and seamlessly installs them inside the Docker sandbox before running tests.
* **🌐 Web Search RAG:** Use `--web-search`. If the Architect needs the latest API documentation, it searches DuckDuckGo in real-time, parses the top websites, and injects 2026-accurate docs into the generation prompt.
* **🐙 Git Autopilot:** Use `--git-autopilot`. Once the task is fully tested and formatted, the Swarm automatically creates a new git branch, stages the files, and writes a beautiful Semantic Commit message.
* **🧠 Smart Codebase RAG:** Pass `--context-dir` to automatically scan your existing project (respecting `.gitignore`), read key files, and seamlessly integrate new features into legacy codebases.
* **🔀 Dynamic Smart Routing:** Use `--auto-route` to dynamically assign cheap, fast models (like `gemini-flash`) to draft code, reserving expensive models (like `claude-3.5-sonnet`) for architecture and debugging. Save up to 70% on token costs!
* **🖋️ Interactive Web Diff-Editor:** Visually compare the AI's drafts, tweak the code by hand, and hit "Approve" via our FastAPI + WebSockets dashboard.
* **📊 OpenTelemetry Tracing:** Pass `--telemetry` to trace every agent's thought process using OTLP.
* **👤 Human-in-the-Loop (HITL):** Approvals gate after the Architecture phase.
* **✨ Auto-Formatting & Linting:** Automatically runs native formatters (`black`, `prettier`, `gofmt`).
* **💾 Session Persistence (SQLite):** Remembers specs and code so you can `--resume`.
* **🛡️ Secure Docker Sandboxing:** Execute unit tests safely within isolated Alpine containers.

---

## 📐 Architecture / Swarm Pipeline

```
          [User Task / Prompt] + [RAG Context] + [Web Search Docs]
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
                │  Step 5: Test Execution   │ (Auto-Installs Packages & Runs tests in DOCKER)
                └─────────────┬─────────────┘
                              │
                       [ 👁️ Visual QA ] (Playwright screenshots -> Vision Model)
                              │
                    ┌─────────┴─────────┐
             Tests Failed         Tests Passed
                    │                   │
                    ▼                   ▼
        ┌───────────────────────┐  [ 🐙 Git Autopilot ] (Auto Branch & Commit)
        │   Step 6: Debugger    │           │
        └───────────┬───────────┘           ▼
                    ▲              [Completed Project] (Saved to SQLite DB)
                    └──(Fixes code and retries)
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

# Optional: Install Playwright browsers for Visual QA
playwright install chromium
```

---

## ⚙️ Usage Modes

### 1. Terminal CLI Mode (The Ultimate Command)
Execute the swarm with all SOTA features enabled:
```bash
multicliswarm \
  --task "Write a responsive HTML/JS landing page for a coffee shop." \
  --language "html" \
  --auto-route \
  --visual-qa \
  --web-search \
  --git-autopilot \
  --use-docker \
  --auto-packages
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
