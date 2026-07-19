# Multi-CLI Swarm (TPROrchestrator)

Multi-CLI Swarm is a professional, **universal (language-agnostic)** implementation of the **MARE (Multi-Agent Refinement & Evaluation)** algorithm. It orchestrates a cooperative team of localized AI CLI models (`gemini`, `codex`, and optionally `claude`) using the principles of **Theory of Decision Making (TTPR)**, **Game Theory (Minimax peer review)**, and **Condorcet's Jury Theorem (Wisdom of the Crowd)**.

This framework is built as a **modular Python package (SDK)**, allowing seamless integration into any external system, web service, IDE, or CI/CD pipeline.

---

## 🚀 Production Release (v1.0.0)

Version 1.0.0 marks the transition to a high-performance, enterprise-ready autonomous developer ecosystem:

* **⚡ Semantic RAG (ChromaDB):** Efficiently indexes massive codebases and retrieves only the most relevant functions and files for each task using vector search.
* **💎 Semantic Caching:** Saves up to 40% on token costs by caching and reusing AI reasonings for similar tasks using semantic similarity.
* **🌿 Session Branching & Snapshots:** Non-destructive experimentation! Create snapshots of your session, try different architectures, and rollback instantly if a path leads to a dead end.
* **💉 Surgical Patching:** Debugger generates minimal **Search/Replace blocks** (Unified Diffs) instead of rewriting files, ensuring precision in large projects.
* **🛡️ Resilient Failover:** Automatic exponential backoff and engine-hopping (e.g., failing over from Claude to Gemini) for 100% uptime.
* **🛠️ Self-Evolving Tools:** The Swarm writes its own Python CLI tools on-the-fly to solve complex environmental problems.
* **🤖 Pair Programming Mode:** Driver -> Navigator interactive coding paradigm between AI agents.
* **🔁 CI/CD Autopilot:** GitHub Action to automatically fix repo issues via labels.
* **👁️ Visual QA:** Playwright-powered headless vision testing for frontend verification.
* **🐙 Git Autopilot:** Fully automated branching, staging, and Semantic Commits.
* **🌐 Web Search RAG:** Real-time API documentation retrieval from DuckDuckGo.
* **👥 Team Spaces Web UI:** Multi-session dashboard with persistent history and interactive Monaco Editor.
* **🛡️ Secure Docker Sandboxing:** Tests run in isolated Alpine containers.

---

## 📐 Swarm Pipeline

```
          [User Task] + [Semantic RAG Context] + [Web Search Docs]
                              │
                              ▼
                ┌───────────────────────────┐
                │     Step 1: Architect     │ (Semantic Cache Lookup -> CoT Thinking)
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
                │    Step 4: Synthesizer    │ (Blends designs -> [💾 Auto Snapshot])
                └─────────────┬─────────────┘
                              │
                  [ 🖋️ Web Diff-Editor Approval ]
                              │
                     [ ✨ Auto-Formatting ]
                              │
                              ▼
                ┌───────────────────────────┐
                │  Step 5: Test Execution   │ (Auto-Package Install -> DOCKER Sandbox)
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

## 💻 Installation

```bash
# Clone the repo and install
git clone https://github.com/Sm0keHokage/MultiCliSwarm.git
cd MultiCliSwarm
pip install -e .
```

### Docker Deployment
Run the entire ecosystem (Web UI + Services) with one command:
```bash
docker-compose up --build
```

---

## ⚙️ Usage

### Terminal CLI
```bash
multicliswarm \
  --task "Implement a secure rate-limiter middleware in Go." \
  --language "go" \
  --auto-route \
  --semantic-rag \
  --telemetry
```

### Team Dashboard
```bash
multicliswarm-ui
```
