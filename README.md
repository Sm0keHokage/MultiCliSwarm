# Multi-CLI Swarm (TPROrchestrator)

Multi-CLI Swarm is a professional, **universal (language-agnostic)** implementation of the **MARE (Multi-Agent Refinement & Evaluation)** algorithm. It orchestrates a cooperative team of localized AI CLI models (`gemini`, `codex`, and optionally `claude`) using the principles of **Theory of Decision Making (TTPR)**, **Game Theory (Minimax peer review)**, and **Condorcet's Jury Theorem (Wisdom of the Crowd)**.

This framework is built as a **modular Python package (SDK)**, allowing seamless integration into any external system, web service, IDE, or CI/CD pipeline.

---

## 🚀 Deep Engineering Features (v0.7.0)

With the release of v0.7.0, Multi-CLI Swarm shifts focus from feature-breadth to deep engineering stability and cost-efficiency:

* **💉 Surgical Patching:** The Debugger now generates minimal **Search/Replace blocks** (Unified Diffs) instead of rewriting entire files. This reduces token consumption by up to 90% and prevents "forgetting" bugs in large files.
* **🛡️ Resilient Failover & Retries:** Every CLI engine is now wrapped with **Exponential Backoff retries**. If an engine hits a rate limit or network error, the Swarm automatically fails over to a secondary engine (e.g., failing over from Claude to Gemini) without aborting the session.
* **🎯 CoT Prompt Determinism:** All prompts now use strict **Chain-of-Thought (CoT)** reasoning encapsulated in `<thinking>` XML tags. This forces the model to "plan" before outputting JSON, leading to nearly 100% deterministic schema adherence.
* **🧪 Framework Unit Tests:** The SDK itself is now covered by a comprehensive **Pytest suite**, ensuring that RAG, SQLite persistence, and surgical patching work flawlessly across all versions.
* **🛠️ Self-Evolving Tools:** The Swarm can write its own Python CLI tools on-the-fly and register them as engines!
* **🤖 Pair Programming Mode:** Driver -> Navigator interactive coding between two models.
* **🔁 CI/CD Autopilot (GitHub Actions):** Automatically fix GitHub issues labeled `swarm-autofix`.
* **👁️ Visual QA (Headless Vision):** Playwright screenshots + Vision models for frontend verification.
* **📦 Autonomous Package Management:** Auto-detects and installs dependencies inside Docker.
* **🌐 Web Search RAG:** Pulls real-time API docs from DuckDuckGo.
* **🐙 Git Autopilot:** Automated branching and Semantic Commits.
* **🧠 Smart Codebase RAG:** Scans local projects to integrate new features into legacy code.
* **🔀 Dynamic Smart Routing:** Automatically assigns cheap models for drafting and expensive models for architecture.
* **🖋️ Interactive Web Diff-Editor:** Visually compare and tweak AI drafts in the browser.

---

## 📐 Swarm Pipeline

```
          [User Task] + [RAG Context] + [Web Search Docs]
                              │
                              ▼
                ┌───────────────────────────┐
                │     Step 1: Architect     │ (Designs plan, CoT Thinking, Pydantic Schema)
                └─────────────┬─────────────┘
                              │
                        [ 👤 HITL Approval ]
                              │
                              ▼
                ┌───────────────────────────┐
                │  Step 2: Developers       │ (Pair Programming OR Parallel Drafting)
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │     Step 3: Reviewer      │ (Critiques drafts, finds edge cases)
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
        ┌───────────────────────┐  [ 🐙 Git Autopilot ] (Auto Branch, Commit, PR)
        │   Step 6: Debugger    │           │
        │  (Surgical Patching)  │           ▼
        └───────────┬───────────┘    [Completed Project] (Traced with OpenTelemetry)
                    ▲                       │
                    └──(Fixes code and retries)
```

---

## 💻 Installation & Requirements

```bash
# Clone the repo and install with dev dependencies
git clone https://github.com/Sm0keHokage/MultiCliSwarm.git
cd MultiCliSwarm
pip install -e .[dev]

# Run internal tests
PYTHONPATH=src pytest tests/
```

---

## ⚙️ Usage Modes

### 1. Terminal CLI Mode
```bash
multicliswarm \
  --task "Add a delete method to the User model." \
  --language "python" \
  --auto-route \
  --telemetry \
  --context-dir "./src"
```

### 2. Team Spaces Web UI Dashboard
```bash
multicliswarm-ui
```

---

## 🔌 Reliable Failover Configuration

You can provide multiple engines separated by commas. The Swarm will try them in order if one fails:
```bash
multicliswarm --architect-engine "claude,gemini" --task "..."
```
