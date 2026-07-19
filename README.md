# Multi-CLI Swarm (TPROrchestrator)

Multi-CLI Swarm is a professional, **universal (language-agnostic)** implementation of the **MARE (Multi-Agent Refinement & Evaluation)** algorithm. It orchestrates a cooperative team of localized AI CLI models (`gemini`, `codex`, and optionally `claude`) using the principles of **Theory of Decision Making (TTPR)**, **Game Theory (Minimax peer review)**, and **Condorcet's Jury Theorem (Wisdom of the Crowd)**.

This framework is built as a **modular Python package (SDK)**, allowing seamless integration into any external system, web service, IDE, or CI/CD pipeline. It generates, peer-reviews, and auto-debugs code in **any programming language** (Python, JavaScript, TypeScript, Go, Rust, and more).

---

## 🚀 Key Features

* **🔑 Zero-Config Authentication:** Automatically uses your existing local authentication sessions from your CLI tools (`gemini`, `codex`, and `claude-code`). No API keys to configure!
* **🌍 Universal Language Support:** Fully language-agnostic. Generate and verify code for **Python, JS, TS, Go, Rust, C++, Java**, etc.
* **🔌 Dynamic Custom CLI Engines:** Register *any* local command-line interface, local model (e.g. Ollama, Llama.cpp), or remote API wrapper as a dynamic engine!
* **⚡ Concurrency:** Runs multiple Developer agents in parallel using Python thread pooling.
* **🔎 Cooperative Peer Review:** Combines draft implementations and lets an independent reviewer critique the designs.
* **🛡️ Self-Correction & Auto-Debugging:** Runs the generated unit tests locally, parses any tracebacks/errors, and executes an automated debugging cycle up to a set limit.
* **🔌 Integrable SDK Architecture:** Exposes a clean, fully parameterizable public Python API with callbacks for integration into GUI apps, FastAPI microservices, or custom agents.
* **🎨 Visually Rich Output:** Provides real-time ANSI-colored logs showing steps, milestones, review summaries, and error logs.

---

## 📐 Architecture / Swarm Pipeline

```
                     [User Task / Prompt]
                              │
                              ▼
                ┌───────────────────────────┐
                │     Step 1: Architect     │ (Designs plan & unit tests in language L)
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │  Step 2: Developers (||)  │ (Concurrently write draft code in L)
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
                │    Step 4: Synthesizer    │ (Blends best designs into final)
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │  Step 5: Test Execution   │ (Runs native test command for language L)
                └─────────────┬─────────────┘
                              │
                    ┌─────────┴─────────┐
             Tests Failed         Tests Passed
                    │                   │
                    ▼                   ▼
        ┌───────────────────────┐  [Completed Code & Tests]
        │   Step 6: Debugger    │
        └───────────┬───────────┘
                    ▲ (Fixes code and retries)
```

---

## 💻 Installation & Requirements

Ensure you have Python 3.8+ and at least one or more of the following CLI tools installed and authenticated:
1. **Gemini CLI** (`gemini`)
2. **Codex CLI** (`codex`)
3. **Claude Code** (`claude`)

### Installation (as a local package):
```bash
pip install -e .
```

---

## ⚙️ Usage

You can execute the swarm using the local `run_swarm.py` runner or via the installed package command `multicliswarm`.

### Python Example:
```bash
./run_swarm.py \
  --task "Write a python class to calculate the nth Fibonacci number using memoization, with validation." \
  --language "python" \
  --developer-engines "gemini,codex"
```

### JavaScript Example:
```bash
./run_swarm.py \
  --task "Write a JavaScript function to format money in cents to currency, with custom symbol placement." \
  --language "javascript" \
  --developer-engines "gemini,codex"
```

### 🔌 Registering Custom CLI Engines (e.g., Ollama or custom scripts)

You can register *any* CLI command dynamically! If your command template has `{prompt}`, it will be formatted. Otherwise, the prompt is automatically piped to the command's standard input (`stdin`).

**Ollama Example:**
```bash
./run_swarm.py \
  --register-engine "local_llama=ollama run llama3" \
  --developer-engines "gemini,local_llama" \
  --task "Write a bubble sort in Python"
```

**Custom API Wrapper / curl Example:**
```bash
./run_swarm.py \
  --register-engine "my_api=curl -s -X POST http://localhost:11434/api/generate -d '{\"model\": \"llama3\", \"prompt\": \"{prompt}\", \"stream\": false}' | jq -r .response" \
  --developer-engines "gemini,my_api" \
  --task "Write a binary search in Go"
```

---

## 🔌 Integrating as an SDK

Because **Multi-CLI Swarm** is structured as a standard Python package, other backend services (like FastAPI) can easily import and run it:

```python
from multicliswarm import SwarmOrchestrator, register_custom_engine

# 1. Dynamically register any custom/local CLI engine programmatically
register_custom_engine("ollama_llama", "ollama run llama3")

# 2. Setup callback to receive real-time streaming updates
def my_status_callback(level, message):
    print(f"[{level.upper()}] {message}")

# 3. Initialize and run
orchestrator = SwarmOrchestrator(
    architect_engine="gemini",
    developer_engines=["gemini", "ollama_llama"],
    callback=my_status_callback
)

result = orchestrator.run(
    task="Create a secure JWT authentication middleware in Go",
    language="go"
)

if result["success"]:
    print(f"Generated File: {result['filename']}")
```

---

## 🧠 Scientific Foundations

1. **Condorcet's Jury Theorem (Wisdom of the Crowd):**
   When multiple independent estimators (models) each have an accuracy greater than $0.5$, the probability that a majority vote yields the correct solution increases towards $1.0$ as the number of estimators increases. By generating drafts in parallel, we prevent the "first-thought bias" or "anchoring bias."
2. **Asymmetric Minimax Game (Peer Review):**
   In software development, finding bugs is mathematically less computationally complex (for an LLM) than drafting a solution from scratch. We play a cooperative game where independent reviewer agents attempt to "break" the developers' drafts, establishing a stable Nash Equilibrium where the final code has no obvious bugs.
3. **Self-Healing Loop (Local Execution Environment):**
   A major flaw of LLMs is hallucinations. We anchor the models to reality by executing the generated test cases locally and returning real runtime exception tracebacks back to a debugger agent, achieving absolute structural soundness.
