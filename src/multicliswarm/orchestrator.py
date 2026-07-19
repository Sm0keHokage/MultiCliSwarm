import os
import sys
import json
import re
import subprocess
import logging
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor

from .engines import get_engine, BaseEngine

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

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Safely extracts JSON from model text, discarding markdown code block wrappers."""
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
    """Strips markdown code wrappers (e.g. ```python, ```js, etc.) if present."""
    lang_clean = language.lower().strip()
    # Match any code block like ```python, ```javascript, ```go, etc.
    match = re.search(r'```(?:[a-zA-Z0-9+#-]+)?\s*(.*?)\s*```', code, re.DOTALL)
    if match:
        return match.group(1).strip()
    return code.strip()


class SwarmOrchestrator:
    """Core SDK orchestrator for the Multi-CLI agent swarm supporting any language."""
    
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
        callback: Optional[Callable[[str, str], None]] = None
    ):
        self.architect_engine = get_engine(architect_engine, architect_model)
        self.developer_engines_names = developer_engines or ["gemini", "codex"]
        self.reviewer_engine = get_engine(reviewer_engine, reviewer_model)
        self.synthesizer_engine = get_engine(synthesizer_engine, synthesizer_model)
        self.debugger_engine = get_engine(debugger_engine, debugger_model)
        self.max_debug_cycles = max_debug_cycles
        self.callback = callback

    def _log(self, message: str, level: str = "info"):
        """Internal logger that triggers logging and user-provided callback."""
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

    def run(
        self,
        task: str,
        language: str = "python",
        output_dir: str = ".",
        override_filename: Optional[str] = None,
        test_cmd: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs the 5-phase MARE pipeline for the specified programming language and task."""
        lang_norm = language.lower().strip()
        self._log(f"Starting Multi-CLI Swarm for language: '{language}' and task: '{task}'")
        
        # --- 1. ARCHITECT ---
        self._log(f"Phase 1: Architect (Designing {language} system and tests)", "step")
        architect_prompt = f"""
        You are the Lead Architect in a cooperative software engineering swarm.
        Your task is to design a complete development plan and specification for the following request in {language}:
        "{task}"
        
        You must output a single JSON object. The JSON object MUST contain exactly these keys:
        1. "specification": A detailed markdown description of the components, function/class signatures, error handling, and expected behaviors.
        2. "test_code": Complete, fully working unit test code in {language} designed to verify the correct behavior of the implementation. The tests must import/include the generated implementation file.
        3. "filename": The recommended filename in {language} where the implementation should be saved.
        
        Ensure your output is valid JSON. Wrap the JSON object in a markdown json block if you prefer.
        """
        
        arch_output_raw = self.architect_engine.execute(architect_prompt)
        spec_data = extract_json_from_text(arch_output_raw)
        
        spec = spec_data.get("specification", "")
        test_code = spec_data.get("test_code", "")
        filename = override_filename or spec_data.get("filename", f"implementation{DEFAULT_EXTENSIONS.get(lang_norm, '.txt')}")
        
        # Determine test filename
        ext = os.path.splitext(filename)[1]
        base = os.path.splitext(filename)[0]
        test_filename = f"test_{base}{ext}"
        if lang_norm == "go":
            test_filename = f"{base}_test.go"
        elif lang_norm == "rust":
            test_filename = f"tests.rs" # typical or custom
            
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
                code = engine.execute(dev_prompt)
                code = clean_code(code, language)
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
        final_code = clean_code(final_code_raw, language)
        
        # Save implementation to target directory
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
        
        # Build test command
        raw_test_cmd = test_cmd or DEFAULT_TEST_CMDS.get(lang_norm, "echo 'No test command specified'")
        cmd_to_run = raw_test_cmd.format(test_filename=test_filename, filename=filename)
        
        tests_passed = False
        for cycle in range(1, self.max_debug_cycles + 1):
            self._log(f"Validation Cycle {cycle} of {self.max_debug_cycles}...")
            self._log(f"Running test command: {cmd_to_run}")
            
            test_result = subprocess.run(
                cmd_to_run,
                shell=True,
                capture_output=True,
                text=True,
                cwd=output_dir
            )
            
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
                    final_code = clean_code(fixed_code_raw, language)
                    with open(final_file_path, "w") as f:
                        f.write(final_code)
                    self._log(f"Saved debugged code iteration to {final_file_path}.", "success")
                except Exception as e:
                    self._log(f"Debugger execution failed: {e}. Exiting debug loop.", "error")
                    break

        return {
            "success": tests_passed,
            "filename": filename,
            "code": final_code,
            "test_filename": test_filename,
            "test_code": test_code_clean,
            "specification": spec,
            "review": review_feedback
        }
