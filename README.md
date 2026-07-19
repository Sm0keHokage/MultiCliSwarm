# Multi-CLI Swarm (TPROrchestrator)

Multi-CLI Swarm is a production-grade, autonomous software engineering ecosystem powered by the **MARE (Multi-Agent Refinement & Evaluation)** algorithm.

---

## 🚀 Production Release (v2.0.0)

Version 2.0.0 moves the ecosystem beyond a prototype into a robust, scalable, and resilient engineering platform:

* **🏗️ Async State Machine:** The Orchestrator is now a non-blocking state machine. It persists the session state (`architecting`, `developing`, `verifying`) to SQLite after every phase, enabling seamless recovery from crashes or restarts.
* **⚡ Concurrent Web API:** The Web Dashboard and API now handle long-running swarm tasks in background threads, keeping the UI responsive and allowing real-time status polling.
* **🛡️ Enterprise Hardening:** Centralized environment-driven configuration via `pydantic-settings`, structured JSON logging for production observability, and a hardened Docker image with non-root execution.
* **💉 Surgical Patching & Semantic RAG:** Precise code modifications using Search/Replace blocks and intelligent codebase indexing via ChromaDB.
* **🤝 Consensus Protocol:** Mission-critical reliability through committee-based peer review.
* **👁️ Visual QA & Performance Benchmarking:** Multimodal frontend testing and automated profiling for high-performance code.

---

## 📐 Production Pipeline

1. **Context & Search:** Real-time Web Search + Semantic RAG indexing.
2. **State: Architecting:** CoT planning with schema validation.
3. **HITL Approval:** Human confirmation of the multi-file architecture.
4. **State: Developing:** Driver/Navigator pair programming or parallel drafting.
5. **State: Reviewing:** Multi-reviewer consensus and synthesis.
6. **State: Verifying:** Docker-sandboxed testing, Surgical Patching, and SAST Security Audit.
7. **State: Completed:** Final Benchmarking, Documentation (MkDocs), and Cloud Deployment.

---

## 💻 Enterprise Installation

```bash
git clone https://github.com/Sm0keHokage/MultiCliSwarm.git
cd MultiCliSwarm
pip install -e .
```

### 🐳 Production Deployment
Launch the hardened production stack with persistent volumes and health checks:
```bash
docker-compose up -d --build
```

---

## ⚙️ Configuration
Multi-CLI Swarm is fully configurable via environment variables or a `.env` file:
- `DB_PATH`: Path to the SQLite session database.
- `STORAGE_DIR`: Base directory for indexes and cache.
- `ENVIRONMENT`: `production` or `development`.
- `LOG_LEVEL`: `INFO`, `DEBUG`, `WARNING`.

---

## 🔌 Reliable Failover
The system is built for 100% uptime. Configure multiple engines for any role:
```bash
multicliswarm --architect-engine "claude,gemini" --task "..."
```
The swarm will automatically retry with exponential backoff and failover to the next engine if rate limits are hit.
