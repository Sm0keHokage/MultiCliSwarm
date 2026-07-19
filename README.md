# Multi-CLI Swarm (TPROrchestrator)

Multi-CLI Swarm is a professional, **universal (language-agnostic)** implementation of the **MARE (Multi-Agent Refinement & Evaluation)** algorithm. It orchestrates a cooperative team of localized AI CLI models (`gemini`, `codex`, and optionally `claude`) using the principles of **Theory of Decision Making (TTPR)**, **Game Theory (Minimax peer review)**, and **Condorcet's Jury Theorem (Wisdom of the Crowd)**.

---

## 🚀 The Elite Suite (v1.2.0) - Ascension

Version 1.2.0 is the definitive release, elevating Multi-CLI Swarm to an elite, enterprise-ready software engineering ecosystem:

* **🛡️ Security Shield (SAST):** Automatically run security audits (e.g., `bandit`, `npm audit`) on generated code. The Swarm identifies and fixes vulnerabilities (SQLi, XSS, insecure dependencies) before they ever reach production.
* **🗺️ Architecture Visualizer:** Explore your project's soul. The Web UI now features an interactive D3.js dependency graph, showing how files and modules interact.
* **💬 Live Collaboration Chat:** Don't just watch—intervene! Send real-time instructions to the Swarm during any phase to adjust architecture or change implementation details on-the-fly.
* **📚 Self-Healing Documentation:** Automatically generate professional documentation portals (MkDocs, Swagger/OpenAPI) for every project.
* **🏎️ Performance Benchmarking:** Automated profiling and benchmarking ensure your code isn't just correct, but highly optimized.
* **🤝 Consensus Protocol:** Committee-based peer review for mission-critical code reliability.
* **⚡ Semantic RAG & Caching:** Hyper-efficient indexing with ChromaDB and up to 40% cost reduction via semantic reasoning reuse.
* **🌿 Session Branching:** Non-destructive experimentation with state snapshots and rollbacks.
* **🐙 CI/CD & Git Autopilot:** Seamless integration into GitHub Actions with automated branching and PRs.
* **👁️ Visual Vision QA:** Headless Playwright browser testing with multimodal UI critique.

---

## 📐 Pipeline Lifecycle

```
          [User Task] + [Semantic RAG] + [Web Search Docs]
                              │
                    [ 💬 Live Chat Intervention ]
                              │
                ┌───────────────────────────┐
                │     Step 1: Architect     │ (Designs plan, Thinking, Schema)
                └─────────────┬─────────────┘
                              │
                        [ 👤 HITL Approval ]
                              │
                              ▼
                ┌───────────────────────────┐
                │  Step 2: Developers       │ (Driver/Navigator Pair Programming)
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │     Step 3: Reviewer      │ (🤝 Multi-Reviewer Consensus)
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │    Step 4: Synthesizer    │ (Blends best designs)
                └─────────────┬─────────────┘
                              │
                  [ 🖋️ Monaco Diff-Editor Approval ]
                              │
                     [ ✨ Auto-Formatting ]
                              │
                              ▼
                ┌───────────────────────────┐
                │  Step 5: Test Execution   │ (DOCKER Sandbox)
                └─────────────┬─────────────┘
                              │
                    ┌─────────┴─────────┐
             Tests Failed         Tests Passed
                    │                   │
                    ▼                   ▼
        ┌───────────────────────┐  [ 🏎️ Performance Benchmark ]
        │   Step 6: Debugger    │           │
        │  (Surgical Patching)  │  [ 🛡️ Security SAST Audit ]
        └───────────┬───────────┘           │
                    ▲              [ 📚 Self-Healing Docs ]
                    └──(Retries)            │
                                   [ 🐙 Git Autopilot ] (PR)
```

---

## 💻 Elite Installation

```bash
git clone https://github.com/Sm0keHokage/MultiCliSwarm.git
cd MultiCliSwarm
pip install -e .[dev]
```

### 🐳 The One-Command Cloud
```bash
docker-compose up --build
```

---

## ⚙️ Elite Usage

### Launch the Dashboard
```bash
multicliswarm-ui
```
Open your browser to http://127.0.0.1:8080 to experience the **Live Collaboration Chat** and **Architecture Visualizer**.

### Production CLI
```bash
multicliswarm \
  --task "Implement a zero-trust auth microservice." \
  --language "go" \
  --security-audit \
  --performance-bench \
  --auto-docs \
  --telemetry
```
