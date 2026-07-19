import os
import sys
import json
import re
import subprocess
import logging
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor

from pydantic import ValidationError
from .engines import get_engine, BaseEngine
from .schemas import ArchitectResponse, estimate_cost

logger = logging.getLogger("multicliswarm.orchestrator")

DEFAULT_TEST_CMDS = {
    "python": "python3 -m unittest {test_filename}",
    "javascript": "node {test_filename}",
    "typescript": "ts-node {test_filename}",
    "go": "go test -v",
    "rust": "cargo test",
}

DEFAULT_EXTENSIONS = {
    "python": ".py",
    "javascript": ".js",
    "typescript": ".ts",
    "go": ".go",
    "rust": ".rs",
    "c++": ".cpp",
    "java": ".java",
    "ruby": ".rb",
    "php": ".php"
}

# Supported docker images for safe execution
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

def run_in_docker(language: str, test_cmd: str, output_dir: str) -> subprocess.CompletedProcess:
    """Executes the test command securely inside a Docker container."""
    lang_clean = language.lower().strip()
    image = DOCKER_IMAGES.get(lang_clean)
    
    if not image:
        # Fallback to local if docker isn't configured for this language
        logger.warning(f"No Docker image configured for '{language}'. Running locally.")
        return subprocess.run(test_cmd, shell=True, capture_output=True, text=True, cwd=output_dir)
        
    abs_dir = os.path.abspath(output_dir)
    docker_cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", "512m",
        "--cpus", "1.0",
        "-v", f"{abs_dir}:/workspace:ro",
        "-w", "/workspace",
        image,
        "sh", "-c", test_cmd
    ]
    
    return subprocess.run(docker_cmd, capture_output=True, text=True)


class SwarmOrchestrator:
    """Core SDK orchestrator for the Multi-CLI agent swarm supporting any language and safe execution."""
    
    def __init__(
        self,
        architect_engine: str = "gemini",
        architect_model: Optional[str] = None,
        developer_engines: List[str] = None,
        reviewer_engine: str = "gemini",
        reviewer_model: Optional[str] = None,
        synthesizer_engine: str = "gemini",
        synthesizer_model: Optional[str] = None,
        debugger_engine: str = "gemini",
        debugger_model: Optional[str] = None,
        max_debug_cycles: int = 3,
        use_docker: bool = False,
        callback: Optional[Callable[[str, str], None]] = None
    ):
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
        self.callback = callback
        
        # Financial tracking
        self.total_cost = 0.0

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

    def _track_cost(self, engine_name: str, prompt: str, response: str):
        """Rudimentary token cost estimator (approx 4 chars = 1 token)."""
        in_tokens = len(prompt) // 4
        out_tokens = len(response) // 4
        cost = estimate_cost(engine_name, in_tokens, out_tokens)
        self.total_cost += cost

    def run(
        self,
        task: str,
        language: str = "python",
        output_dir: str = ".",
        override_filename: Optional[str] = None,
        test_cmd: Optional[str] = None
    ) -> Dict[str, Any]:
        lang_norm = language.lower().strip()
        self._log(f"Starting Multi-CLI Swarm for language: '{language}' and task: '{task}'")
        self.total_cost = 0.0
        
        # --- 1. ARCHITECT ---
        self._log(f"Phase 1: Architect (Designing {language} system and tests)", "step")
        schema_json = ArchitectResponse.model_json_schema()
        architect_prompt = f"""
        You are the Lead Architect in a cooperative software engineering swarm.
        Your task is to design a complete development plan and specification for the following request in {language}:
        "{task}"
        
        You MUST output a valid JSON object matching this schema exactly:
        {json.dumps(schema_json, indent=2)}
        """
        
        arch_output_raw = self.architect_engine.execute(architect_prompt)
        self._track_cost(self.architect_engine_name, architect_prompt, arch_output_raw)
        
        raw_dict = extract_json_from_text(arch_output_raw)
        
        try:
            # Pydantic Phase 1 Validation
            arch_response = ArchitectResponse(**raw_dict)
        except ValidationError as e:
            self._log(f"Architect JSON validation failed: {e}", "error")
            raise RuntimeError(f"Architect returned invalid schema: {e}")
            
        spec = arch_response.specification
        test_code = arch_response.test_code
        filename = override_filename or arch_response.filename
        
        # Determine test filename
        ext = os.path.splitext(filename)[1]
        base = os.path.splitext(filename)[0]
        test_filename = f"test_{base}{ext}"
        if lang_norm == "go":
            test_filename = f"{base}_test.go"
        elif lang_norm == "rust":
            test_filename = f"tests.rs"
            
        self._log(f"Architect generated specification. Filename target: {filename}", "success")

        # --- 2. PARALLEL DEVELOPERS ---
        self._log(f"Phase 2: Developers (Running {len(self.developer_engines_names)} in parallel)", "step")
        
        def run_developer(index: int, engine_name: str) -> Dict[str, Any]:
            dev_prompt = f"""
            You are a highly skilled Senior Software Engineer in a cooperative swarm.
            Based on the following system specification, write the complete, optimal {language} implementation:
            
            {spec}
            
            Requirements:
            1. Write the code to be saved in '{filename}'.
            2. Ensure proper imports, robust error handling, and logical flow.
            3. Output ONLY the raw {language} code. Do not write explanation, introductory text, or markdown code blocks. Just return the runnable code.
            """
            self._log(f"Developer {index+1} ({engine_name}) starting...")
            try:
                engine = get_engine(engine_name)
                code_raw = engine.execute(dev_prompt)
                code = clean_code(code_raw, language)
                self._track_cost(engine_name, dev_prompt, code_raw)
                self._log(f"Developer {index+1} ({engine_name}) finished.", "success")
                return {"index": index, "engine": engine_name, "code": code}
            except Exception as e:
                self._log(f"Developer {index+1} ({engine_name}) failed: {e}", "error")
                return {"index": index, "engine": engine_name, "code": None, "error": str(e)}

        drafts = []
        with ThreadPoolExecutor(max_workers=len(self.developer_engines_names)) as executor:
            futures = [
                executor.submit(run_developer, i, eng_name) 
                for i, eng_name in enumerate(self.developer_engines_names)
            ]
            for fut in futures:
                drafts.append(fut.result())
                
        successful_drafts = [d for d in drafts if d["code"]]
        if not successful_drafts:
            raise RuntimeError("All developer agents failed to generate code.")
            
        self._log(f"Gathered {len(successful_drafts)} successful draft solutions.", "success")

        # --- 3. PEER REVIEWER ---
        self._log("Phase 3: Peer Reviewer (Analyzing and finding edge cases)", "step")
        review_context = ""
        for sd in successful_drafts:
            review_context += f"### Draft {sd['index'] + 1} (Engine: {sd['engine']})\n```{lang_norm}\n{sd['code']}\n```\n\n"
            
        reviewer_prompt = f"""
        You are the Quality Assurance lead and Peer Reviewer in a cooperative swarm.
        Your task is to analyze these {len(successful_drafts)} alternative draft solutions created in {language} for the specification.
        
        Specification:
        {spec}
        
        Drafts:
        {review_context}
        
        Analyze:
        1. Which solution has the most robust implementation and why?
        2. Are there any edge cases, performance issues, or security flaws in any draft?
        3. How can we integrate the best features of each draft into a single, flawless master code?
        
        Output a detailed review and synthesis guideline.
        """
        
        review_feedback = self.reviewer_engine.execute(reviewer_prompt)
        self._track_cost(self.reviewer_engine_name, reviewer_prompt, review_feedback)
        self._log("Reviewer completed analysis.", "success")

        # --- 4. SYNTHESIZER ---
        self._log("Phase 4: Synthesizer (Combining best approaches)", "step")
        synth_prompt = f"""
        You are the Master Code Integrator in a cooperative swarm.
        Your task is to write the absolute best, final {language} code for '{filename}' by integrating the best design choices from the draft solutions and incorporating the reviewer's feedback.
        
        Specification:
        {spec}
        
        Drafts:
        {review_context}
        
        Reviewer Feedback:
        {review_feedback}
        
        Requirements:
        1. Produce a complete, working {language} implementation.
        2. Output ONLY the raw {language} code. Absolutely no markdown blocks, no markdown wrappers, and no commentary. The output must be directly writable to a file and run.
        """
        
        final_code_raw = self.synthesizer_engine.execute(synth_prompt)
        self._track_cost(self.synthesizer_engine_name, synth_prompt, final_code_raw)
        final_code = clean_code(final_code_raw, language)
        
        final_file_path = os.path.join(output_dir, filename)
        with open(final_file_path, "w") as f:
            f.write(final_code)
        self._log(f"Final synthesized code saved to {final_file_path}.", "success")

        # --- 5. VERIFICATION & AUTO-DEBUGGING LOOP ---
        self._log("Phase 5: Verification & Auto-Debugging Loop", "step")
        test_file_path = os.path.join(output_dir, test_filename)
        test_code_clean = clean_code(test_code, language)
        with open(test_file_path, "w") as f:
            f.write(test_code_clean)
        self._log(f"Unit tests saved to {test_file_path}.", "success")
        
        raw_test_cmd = test_cmd or DEFAULT_TEST_CMDS.get(lang_norm, "echo 'No test command specified'")
        cmd_to_run = raw_test_cmd.format(test_filename=test_filename, filename=filename)
        
        tests_passed = False
        for cycle in range(1, self.max_debug_cycles + 1):
            self._log(f"Validation Cycle {cycle} of {self.max_debug_cycles}...")
            self._log(f"Running test command: {cmd_to_run} (Docker: {self.use_docker})")
            
            if self.use_docker:
                test_result = run_in_docker(language, cmd_to_run, output_dir)
            else:
                test_result = subprocess.run(cmd_to_run, shell=True, capture_output=True, text=True, cwd=output_dir)
            
            if test_result.returncode == 0:
                self._log(f"All tests PASSED successfully in cycle {cycle}!", "success")
                tests_passed = True
                break
            else:
                self._log(f"Tests FAILED in cycle {cycle} (Exit Code: {test_result.returncode})", "warning")
                
                if cycle == self.max_debug_cycles:
                    self._log("Reached maximum debug cycles. Verification failed.", "error")
                    break
                    
                self._log("Invoking Debugger to repair the implementation...")
                debug_prompt = f"""
                You are an expert Test-Driven Developer and Debugger.
                The {language} implementation file '{filename}' failed its unit tests '{test_filename}'.
                
                Current Implementation Code:
                ```{lang_norm}
                {final_code}
                ```
                
                Unit Test Code:
                ```{lang_norm}
                {test_code_clean}
                ```
                
                Test Failure / Traceback Output:
                {test_result.stderr or test_result.stdout}
                
                Your Task:
                Identify the precise bugs causing the failures and fix them. Return the complete corrected {language} code.
                Output ONLY the raw {language} code. Absolutely no markdown backticks, no explanations, and no headers.
                """
                
                try:
                    fixed_code_raw = self.debugger_engine.execute(debug_prompt)
                    self._track_cost(self.debugger_engine_name, debug_prompt, fixed_code_raw)
                    final_code = clean_code(fixed_code_raw, language)
                    with open(final_file_path, "w") as f:
                        f.write(final_code)
                    self._log(f"Saved debugged code iteration to {final_file_path}.", "success")
                except Exception as e:
                    self._log(f"Debugger execution failed: {e}. Exiting debug loop.", "error")
                    break

        self._log(f"Total Swarm Cost Estimate: ${self.total_cost:.5f} USD", "info")

        return {
            "success": tests_passed,
            "filename": filename,
            "code": final_code,
            "test_filename": test_filename,
            "test_code": test_code_clean,
            "specification": spec,
            "review": review_feedback,
            "cost_usd": self.total_cost
        }
