import os
import sys
import json
import re
import uuid
import subprocess
import logging
import threading
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor

from pydantic import ValidationError
from .engines import get_engine, BaseEngine, register_custom_engine
from .schemas import ArchitectResponse, FileMap, CustomToolRequest, estimate_cost, DebuggerResponse
from .db import save_session, get_session, create_snapshot, load_snapshot
from .rag import get_codebase_context
from .semantic_rag import CodeIndexer
from .semantic_cache import SemanticCache
from .telemetry import get_tracer
from .web_search import search_web_docs
from .visual_qa import take_screenshot_sync
from .git_autopilot import create_branch_and_commit
from .patching import apply_patch
from .benchmarking import run_performance_test
from .deployers import run_deploy
from .security import run_security_audit
from .docs_engine import generate_docs

logger = logging.getLogger("multicliswarm.orchestrator")
tracer = get_tracer()

DEFAULT_TEST_CMDS = {
    "python": "python3 -m unittest discover",
    "javascript": "npm test || node test_*.js",
    "go": "go test -v ./...",
    "rust": "cargo test",
}

FORMATTERS = {
    "python": ["black .", "ruff check --fix ."],
    "javascript": ["prettier --write .", "eslint --fix ."],
    "typescript": ["prettier --write .", "eslint --fix ."],
    "go": ["gofmt -w ."],
    "rust": ["cargo fmt"]
}

DOCKER_IMAGES = {
    "python": "python:3.11-alpine",
    "javascript": "node:18-alpine",
    "go": "golang:1.20-alpine",
}

def extract_json_from_text(text: str) -> Dict[str, Any]:
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        text = match.group(1)
    else:
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            text = match.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON out of text: {text}")
        raise e

def clean_code(code: str, language: str = "python") -> str:
    lang_clean = language.lower().strip()
    match = re.search(r'```(?:[a-zA-Z0-9+#-]+)?\s*(.*?)\s*```', code, re.DOTALL)
    if match:
        return match.group(1).strip()
    return code.strip()

def run_in_docker(language: str, test_cmd: str, output_dir: str, auto_packages: bool = False) -> subprocess.CompletedProcess:
    lang_clean = language.lower().strip()
    image = DOCKER_IMAGES.get(lang_clean)
    
    if not image:
        logger.warning(f"No Docker image configured for '{language}'. Running locally.")
        return subprocess.run(test_cmd, shell=True, capture_output=True, text=True, cwd=output_dir)
        
    abs_dir = os.path.abspath(output_dir)
    
    if auto_packages:
        if lang_clean == "python":
            test_cmd = f"pip install pytest pytest-benchmark bandit requests; [ -f requirements.txt ] && pip install -r requirements.txt; {test_cmd}"
        elif lang_clean == "javascript" or lang_clean == "typescript":
            test_cmd = f"npm init -y; npm install; {test_cmd}"
        elif lang_clean == "go":
            test_cmd = f"go mod tidy; {test_cmd}"
            
    docker_cmd = [
        "docker", "run", "--rm",
        "--network", "host" if auto_packages else "none", 
        "--memory", "512m",
        "--cpus", "1.0",
        "-v", f"{abs_dir}:/workspace:rw",
        "-w", "/workspace",
        image,
        "sh", "-c", test_cmd
    ]
    
    return subprocess.run(docker_cmd, capture_output=True, text=True)


class SwarmOrchestrator:
    def __init__(
        self,
        architect_engine: str = "claude,gemini",
        architect_model: Optional[str] = None,
        developer_engines: List[str] = None,
        reviewer_engine: str = "claude,gemini",
        reviewer_model: Optional[str] = None,
        synthesizer_engine: str = "claude,gemini",
        synthesizer_model: Optional[str] = None,
        debugger_engine: str = "claude,gemini",
        debugger_model: Optional[str] = None,
        max_debug_cycles: int = 3,
        use_docker: bool = False,
        auto_route: bool = False,
        web_search: bool = False,
        visual_qa: bool = False,
        auto_packages: bool = False,
        git_autopilot: bool = False,
        pair_programming: bool = False,
        semantic_rag: bool = False,
        semantic_cache: bool = False,
        performance_bench: bool = False,
        reviewer_consensus: bool = False,
        security_audit: bool = False,
        auto_docs: bool = False,
        callback: Optional[Callable[[str, str], None]] = None,
        ask_approval: Optional[Callable[[str, ArchitectResponse], bool]] = None,
        ask_code_approval: Optional[Callable[[Dict[str, str]], Dict[str, str]]] = None,
        live_chat_interrupt: Optional[Callable[[], Optional[str]]] = None
    ):
        if auto_route:
            developer_engines = ["gemini,mock"] if not developer_engines else developer_engines
            architect_engine = "claude,gemini"
            reviewer_engine = "claude,gemini"
            synthesizer_engine = "claude,gemini"
            debugger_engine = "claude,gemini"

        self.architect_engine_name = architect_engine
        self.architect_engine = get_engine(architect_engine, architect_model)
        self.developer_engines_names = developer_engines or ["gemini", "codex"]
        self.reviewer_engine_name = reviewer_engine
        self.reviewer_engine = get_engine(reviewer_engine, reviewer_model)
        self.synthesizer_engine_name = synthesizer_engine
        self.synthesizer_engine = get_engine(synthesizer_engine, synthesizer_model)
        self.debugger_engine_name = debugger_engine
        self.debugger_engine = get_engine(debugger_engine, debugger_model)
        
        self.max_debug_cycles = max_debug_cycles
        self.use_docker = use_docker
        self.web_search = web_search
        self.visual_qa = visual_qa
        self.auto_packages = auto_packages
        self.git_autopilot = git_autopilot
        self.pair_programming = pair_programming
        self.semantic_rag_enabled = semantic_rag
        self.semantic_cache_enabled = semantic_cache
        self.performance_bench = performance_bench
        self.reviewer_consensus = reviewer_consensus
        self.security_audit_enabled = security_audit
        self.auto_docs_enabled = auto_docs
        
        self.callback = callback
        self.ask_approval = ask_approval
        self.ask_code_approval = ask_code_approval
        self.live_chat_interrupt = live_chat_interrupt
        
        self.total_cost = 0.0
        self.cache = SemanticCache() if semantic_cache else None
        self.indexer = CodeIndexer() if semantic_rag else None

    def _log(self, message: str, level: str = "info"):
        if level == "info":
            logger.info(message)
        elif level == "success":
            logger.info(f"SUCCESS: {message}")
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)
            
        if self.callback:
            self.callback(level, message)

    def _check_interrupts(self) -> str:
        """Checks if a user has sent a mid-process chat message to adjust course."""
        if self.live_chat_interrupt:
            msg = self.live_chat_interrupt()
            if msg:
                self._log(f"Live Intervention Received: '{msg}'", "warning")
                return f"\n[USER INTERVENTION]: {msg}\n"
        return ""

    def _track_cost(self, engine_name: str, prompt: str, response: str):
        in_tokens = len(prompt) // 4
        out_tokens = len(response) // 4
        cost = estimate_cost(engine_name.split(',')[0], in_tokens, out_tokens)
        self.total_cost += cost

    def format_code(self, language: str, output_dir: str):
        lang_clean = language.lower().strip()
        cmds = FORMATTERS.get(lang_clean, [])
        for cmd in cmds:
            self._log(f"Running auto-formatter: {cmd}", "info")
            try:
                subprocess.run(cmd, shell=True, capture_output=True, cwd=output_dir)
            except Exception as e:
                self._log(f"Formatter {cmd} failed: {e}", "warning")

    def _handle_self_evolving_tools(self, tools: List[CustomToolRequest]):
        if not tools: return
        self._log(f"Self-Evolving Tools: Architect requested {len(tools)} custom tools.", "step")
        os.makedirs(".multicliswarm_tools", exist_ok=True)
        for t in tools:
            script_path = os.path.abspath(f".multicliswarm_tools/{t.tool_name}.py")
            with open(script_path, "w") as f:
                f.write(t.python_script)
            os.chmod(script_path, 0o755)
            register_custom_engine(t.tool_name, f"python3 {script_path}")
            self.developer_engines_names.append(t.tool_name)
            self._log(f"Registered evolved tool '{t.tool_name}' dynamically.", "success")

    def run(
        self,
        task: str,
        language: str = "python",
        output_dir: str = ".",
        test_cmd: Optional[str] = None,
        resume_session_id: Optional[str] = None,
        resume_snapshot_id: Optional[str] = None,
        context_dir: Optional[str] = None,
        deploy_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        with tracer.start_as_current_span("SwarmOrchestration") as span:
            span.set_attribute("task", task)
            span.set_attribute("language", language)
            
            lang_norm = language.lower().strip()
            self.total_cost = 0.0
            session_id = resume_session_id or str(uuid.uuid4())
            previous_context = ""
            intervention_context = ""
            
            if resume_snapshot_id:
                snapshot = load_snapshot(resume_snapshot_id)
                if snapshot:
                    self._log(f"Restoring from snapshot {resume_snapshot_id}...", "info")
                    previous_context = f"\nPrevious Specification:\n{snapshot['specification']}\n"
                    for fname, content in snapshot['final_files'].items():
                        previous_context += f"\nPrevious Code for {fname}:\n```{lang_norm}\n{content}\n```\n"
            elif resume_session_id:
                old_session = get_session(resume_session_id)
                if old_session:
                    self._log(f"Resuming session {resume_session_id}...", "info")
                    previous_context = f"\nPrevious Specification:\n{old_session['specification']}\n"
                    for fname, content in old_session['final_files'].items():
                        previous_context += f"\nPrevious Code for {fname}:\n```{lang_norm}\n{content}\n```\n"

            rag_context = ""
            if context_dir:
                self._log(f"Scanning codebase context in {context_dir}...", "info")
                with tracer.start_as_current_span("RAG_Context"):
                    if self.semantic_rag_enabled:
                        self.indexer.index_directory(context_dir)
                        rag_context = self.indexer.query(task)
                    else:
                        rag_context = get_codebase_context(context_dir)
                    if rag_context:
                        rag_context = f"\n=== EXISTING CODEBASE CONTEXT ===\n{rag_context}\n=================================\n"

            web_context = ""
            if self.web_search:
                self._log("Fetching real-time documentation from Web...", "info")
                with tracer.start_as_current_span("Web_Search"):
                    web_context = search_web_docs(task)
                    if web_context:
                        web_context = f"\n{web_context}\n"

            self._log(f"Starting Multi-CLI Swarm (Session: {session_id})", "info")
            
            # --- 1. ARCHITECT ---
            with tracer.start_as_current_span("Phase_1_Architect"):
                self._log(f"Phase 1: Architect (Designing Multi-File {language} system)", "step")
                schema_json = ArchitectResponse.model_json_schema()
                architect_prompt = f"""
                You are the Lead Architect in a cooperative software engineering swarm.
                Your task is to design a complete development plan and multi-file architecture for the following request in {language}:
                "{task}"
                {rag_context}
                {web_context}
                {previous_context}
                
                You MUST use the `<thinking>` tag to reason about the architecture before generating the JSON.
                After thinking, output a valid JSON object matching this exact Pydantic schema:
                {json.dumps(schema_json, indent=2)}
                """
                arch_output_raw = None
                if self.semantic_cache_enabled:
                    arch_output_raw = self.cache.get(architect_prompt)
                if not arch_output_raw:
                    arch_output_raw = self.architect_engine.execute(architect_prompt)
                    if self.semantic_cache_enabled:
                        self.cache.set(architect_prompt, arch_output_raw)
                self._track_cost(self.architect_engine_name, architect_prompt, arch_output_raw)
                raw_dict = extract_json_from_text(arch_output_raw)
                try:
                    arch_response = ArchitectResponse(**raw_dict)
                except ValidationError as e:
                    self._log(f"Architect JSON validation failed: {e}", "error")
                    raise RuntimeError(f"Architect returned invalid schema: {e}")
                spec = arch_response.specification
                files_map = arch_response.files
                self._log(f"Architect mapped {len(files_map)} files to create.", "success")
                if arch_response.custom_tools:
                    self._handle_self_evolving_tools(arch_response.custom_tools)
            
            if self.ask_approval:
                with tracer.start_as_current_span("HITL_Architecture_Approval"):
                    approved = self.ask_approval(task, arch_response)
                    if not approved:
                        self._log("Task cancelled by user.", "warning")
                        return {"success": False, "status": "cancelled"}

            final_files_content = {}
            for fmap in files_map:
                fname = fmap.filepath
                with tracer.start_as_current_span(f"Generate_{fname}"):
                    self._log(f"Generating file: {fname} (Test: {fmap.is_test})", "step")
                    
                    # Mid-process intervention check
                    intervention_context += self._check_interrupts()
                    
                    if self.pair_programming and len(self.developer_engines_names) >= 2:
                        self._log("Pair Programming Mode Active (Driver -> Navigator).", "info")
                        engine_1 = self.developer_engines_names[0]
                        engine_2 = self.developer_engines_names[1]
                        prompt_driver = f"Task: Write {fname}. Spec:\n{spec}\n{intervention_context}\nOutput ONLY raw {language} code."
                        code_driver = get_engine(engine_1).execute(prompt_driver)
                        code_driver = clean_code(code_driver, language)
                        self._track_cost(engine_1, prompt_driver, code_driver)
                        prompt_nav = f"You are pair programming. The Driver wrote this code for {fname}:\n```{lang_norm}\n{code_driver}\n```\nImprove it based on the spec:\n{spec}\n{intervention_context}\nOutput ONLY the final raw {language} code."
                        code_nav = get_engine(engine_2).execute(prompt_nav)
                        code_nav = clean_code(code_nav, language)
                        self._track_cost(engine_2, prompt_nav, code_nav)
                        successful_drafts = [{"index": 0, "engine": "Pair_Programming", "code": code_nav}]
                    else:
                        def run_developer(index: int, engine_name: str) -> Dict[str, Any]:
                            with tracer.start_as_current_span(f"Developer_{engine_name}"):
                                dev_prompt = f"System Specification:\n{spec}\n{intervention_context}\nWrite ONLY the complete {language} code for: '{fname}'.\nDescription: {fmap.description}\nOutput ONLY raw code."
                                self._log(f"Developer {index+1} ({engine_name}) drafting {fname}...")
                                try:
                                    engine = get_engine(engine_name)
                                    code_raw = engine.execute(dev_prompt)
                                    code = clean_code(code_raw, language)
                                    self._track_cost(engine_name, dev_prompt, code_raw)
                                    return {"index": index, "engine": engine_name, "code": code}
                                except Exception as e:
                                    return {"index": index, "engine": engine_name, "code": None, "error": str(e)}
                        drafts = []
                        with ThreadPoolExecutor(max_workers=len(self.developer_engines_names)) as executor:
                            futures = [executor.submit(run_developer, i, eng_name) for i, eng_name in enumerate(self.developer_engines_names)]
                            for fut in futures:
                                drafts.append(fut.result())
                        successful_drafts = [d for d in drafts if d["code"]]

                    if not successful_drafts:
                        raise RuntimeError(f"All developers failed to generate {fname}.")

                    # --- 3. PEER REVIEWER (With Consensus Option) ---
                    with tracer.start_as_current_span("Phase_3_Reviewer"):
                        review_context = "".join([f"### Draft {sd['index'] + 1}\n```{lang_norm}\n{sd['code']}\n```\n" for sd in successful_drafts])
                        reviewer_prompt = f"Analyze these drafts for '{fname}' based on spec:\n{spec}\n{intervention_context}\nDrafts:\n{review_context}\nProvide strict critique and synthesis advice."
                        
                        if self.reviewer_consensus:
                            self._log("Reviewer Consensus Protocol: Gathering multiple opinions...", "info")
                            reviewer_engines = ["claude", "gemini"] # Committee
                            opinions = []
                            for r_eng_name in reviewer_engines:
                                op = get_engine(r_eng_name).execute(reviewer_prompt)
                                self._track_cost(r_eng_name, reviewer_prompt, op)
                                opinions.append(op)
                            
                            debate_prompt = f"We have multiple reviewer opinions on the drafts for {fname}:\n"
                            for i, op in enumerate(opinions): debate_prompt += f"Reviewer {i+1}:\n{op}\n\n"
                            debate_prompt += "Synthesize a final consensus review and synthesis guideline."
                            review_feedback = self.reviewer_engine.execute(debate_prompt)
                            self._track_cost(self.reviewer_engine_name, debate_prompt, review_feedback)
                        else:
                            review_feedback = self.reviewer_engine.execute(reviewer_prompt)
                            self._track_cost(self.reviewer_engine_name, reviewer_prompt, review_feedback)

                    # --- 4. SYNTHESIZER ---
                    with tracer.start_as_current_span("Phase_4_Synthesizer"):
                        synth_prompt = f"Synthesize the absolute best code for '{fname}'.\nSpec:\n{spec}\n{intervention_context}\nDrafts:\n{review_context}\nReviewer Feedback:\n{review_feedback}\nOutput ONLY raw code."
                        final_code_raw = self.synthesizer_engine.execute(synth_prompt)
                        self._track_cost(self.synthesizer_engine_name, synth_prompt, final_code_raw)
                        final_code = clean_code(final_code_raw, language)
                        final_files_content[fname] = final_code
                        self._log(f"Synthesized {fname} successfully.", "success")

            if self.ask_code_approval:
                with tracer.start_as_current_span("HITL_Code_Approval"):
                    self._log("Waiting for user to approve/edit generated code in the UI...", "info")
                    final_files_content = self.ask_code_approval(final_files_content)

            for fname, code in final_files_content.items():
                fpath = os.path.join(output_dir, fname)
                os.makedirs(os.path.dirname(fpath) or ".", exist_ok=True)
                with open(fpath, "w") as f:
                    f.write(code)

            with tracer.start_as_current_span("Auto_Formatting"):
                self.format_code(language, output_dir)
                
            visual_issues = ""
            if self.visual_qa:
                with tracer.start_as_current_span("Visual_QA"):
                    html_files = [fn for fn in final_files_content.keys() if fn.endswith(".html")]
                    for hf in html_files:
                        self._log(f"Running Visual QA for {hf}...", "info")
                        img_path = os.path.join(output_dir, f"{hf}.png")
                        if take_screenshot_sync(os.path.join(output_dir, hf), img_path):
                            vqa_prompt = "You are a Visual QA tester. Look at this screenshot. If bugs, list them. If ok, say 'Looks good'."
                            try:
                                vqa_feedback = self.reviewer_engine.execute(vqa_prompt, images=[img_path])
                                self._track_cost(self.reviewer_engine_name, vqa_prompt, vqa_feedback)
                                if "Looks good" not in vqa_feedback:
                                    visual_issues += f"Visual Issues in {hf}:\n{vqa_feedback}\n"
                            except: pass

            with tracer.start_as_current_span("Phase_5_Verification"):
                self._log("Phase 5: Global Verification & Auto-Debugging", "step")
                raw_test_cmd = test_cmd or DEFAULT_TEST_CMDS.get(lang_norm, "echo 'No tests run'")
                tests_passed = False
                for cycle in range(1, self.max_debug_cycles + 1):
                    with tracer.start_as_current_span(f"Debug_Cycle_{cycle}"):
                        self._log(f"Validation Cycle {cycle} of {self.max_debug_cycles}...")
                        if self.use_docker:
                            test_result = run_in_docker(language, raw_test_cmd, output_dir, self.auto_packages)
                        else:
                            test_result = subprocess.run(raw_test_cmd, shell=True, capture_output=True, text=True, cwd=output_dir)
                        
                        if test_result.returncode == 0 and not visual_issues:
                            self._log(f"All tests PASSED successfully in cycle {cycle}!", "success")
                            tests_passed = True
                            
                            # --- 5.1 Performance Benchmarking ---
                            if self.performance_bench:
                                with tracer.start_as_current_span("Performance_Benchmarking"):
                                    self._log("Running performance benchmarks...", "info")
                                    test_file = next((f for f in final_files_content.keys() if "test" in f), None)
                                    if test_file:
                                        bench_report = run_performance_test(language, test_file, output_dir)
                                        self._log(f"Performance Report:\n{bench_report}", "info")
                                        
                            # --- 5.2 Security Shield (v1.2.0) ---
                            if self.security_audit_enabled:
                                with tracer.start_as_current_span("Security_Shield"):
                                    self._log("Running Security Shield SAST audit...", "step")
                                    audit_result = run_security_audit(language, output_dir)
                                    if audit_result.get("status") == "completed":
                                        self._log(f"Security Audit completed. Report: {json.dumps(audit_result.get('report', audit_result.get('raw_output'))[:1000])}", "info")
                            break
                        else:
                            self._log("Tests FAILED. Invoking Debugger with Surgical Patching...", "warning")
                            if cycle == self.max_debug_cycles: break
                            current_state = "".join([f"### File: {fn}\n```{lang_norm}\n{fc}\n```\n" for fn, fc in final_files_content.items()])
                            debug_schema_json = DebuggerResponse.model_json_schema()
                            debug_prompt = f"Debugger Context:\n{current_state}\nTraceback:\n{test_result.stderr or test_result.stdout}\n{visual_issues}\nProvide SURGICAL PATCHES. Use `<thinking>`.\n{json.dumps(debug_schema_json, indent=2)}"
                            try:
                                fixed_dict_raw = self.debugger_engine.execute(debug_prompt)
                                self._track_cost(self.debugger_engine_name, debug_prompt, fixed_dict_raw)
                                fixed_dict = extract_json_from_text(fixed_dict_raw)
                                debug_resp = DebuggerResponse(**fixed_dict)
                                for p in debug_resp.patches:
                                    if p.filepath in final_files_content:
                                        final_files_content[p.filepath] = apply_patch(final_files_content[p.filepath], p.blocks)
                                        with open(os.path.join(output_dir, p.filepath), "w") as f: f.write(final_files_content[p.filepath])
                                        self._log(f"Debugger surgically patched {p.filepath}.", "success")
                                self.format_code(language, output_dir)
                                visual_issues = ""
                            except Exception as e:
                                self._log(f"Debugger failed: {e}", "error")
                                break

            # --- 6. Cloud Deployment ---
            deploy_url = None
            if deploy_provider and tests_passed:
                with tracer.start_as_current_span(f"Cloud_Deploy_{deploy_provider}"):
                    self._log(f"Deploying to {deploy_provider}...", "step")
                    deploy_url = run_deploy(deploy_provider, output_dir)
                    self._log(f"Deploy Successful! URL: {deploy_url}", "success")
                    
            # --- 7. Auto Documentation (v1.2.0) ---
            if self.auto_docs_enabled and tests_passed:
                with tracer.start_as_current_span("Docs_Generation"):
                    self._log("Phase 7: Generating Self-Healing Documentation", "step")
                    generate_docs(output_dir, language)
                    self._log("Documentation portal generated in ./docs", "success")

            if self.git_autopilot:
                with tracer.start_as_current_span("Git_Autopilot"):
                    branch_name = f"swarm-feat-{session_id[:8]}"
                    msg = f"feat: Autonomous generation for task '{task[:40]}...'"
                    create_branch_and_commit(output_dir, branch_name, msg)

            self._log(f"Total Session Cost: ${self.total_cost:.5f} USD", "info")
            if tests_passed:
                create_snapshot(session_id, f"Auto-save after: {task[:30]}", spec, final_files_content)

            save_session(session_id, task, language, spec, files_map, final_files_content, self.total_cost)

            return {
                "session_id": session_id,
                "success": tests_passed,
                "files": final_files_content,
                "cost_usd": self.total_cost,
                "deploy_url": deploy_url
            }
