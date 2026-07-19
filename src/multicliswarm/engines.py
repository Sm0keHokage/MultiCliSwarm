import os
import json
import subprocess
import tempfile
import logging
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger("multicliswarm.engines")

CUSTOM_ENGINES = {}

class BaseEngine:
    def __init__(self, model=None, name=None):
        self.model = model
        self.name = name

    def execute(self, prompt: str, images: Optional[List[str]] = None) -> str:
        raise NotImplementedError("Subclasses must implement execute()")

class GeminiEngine(BaseEngine):
    def __init__(self, model=None):
        super().__init__(model, "gemini")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(RuntimeError))
    def execute(self, prompt: str, images: Optional[List[str]] = None) -> str:
        cmd = ["gemini", "-p", prompt, "-o", "json"]
        if self.model:
            cmd += ["-m", self.model]
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return data.get("response", "").strip()
        except subprocess.CalledProcessError as e:
            logger.warning(f"gemini CLI invocation failed (retrying): {e.stderr or e.stdout}")
            raise RuntimeError(f"gemini CLI failed: {e.stderr or e.stdout}")
        except json.JSONDecodeError:
            return result.stdout.strip()

class CodexEngine(BaseEngine):
    def __init__(self, model=None):
        super().__init__(model, "codex")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(RuntimeError))
    def execute(self, prompt: str, images: Optional[List[str]] = None) -> str:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_out:
            temp_file_path = temp_out.name
            
        cmd = ["codex", "exec", prompt, "--skip-git-repo-check", "--ephemeral", "-o", temp_file_path]
        if self.model:
            cmd += ["-m", self.model]
        if images:
            for img in images:
                cmd += ["-i", img]
                
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            with open(temp_file_path, "r") as f:
                response = f.read().strip()
            return response
        except subprocess.CalledProcessError as e:
            logger.warning(f"codex CLI invocation failed (retrying): {e.stderr or e.stdout}")
            raise RuntimeError(f"codex CLI failed: {e.stderr or e.stdout}")
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

class ClaudeEngine(BaseEngine):
    def __init__(self, model=None):
        super().__init__(model, "claude")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(RuntimeError))
    def execute(self, prompt: str, images: Optional[List[str]] = None) -> str:
        cmd = ["claude", "-p", prompt]
        if self.model:
            cmd += ["--model", self.model]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.warning(f"claude CLI invocation failed (retrying): {e.stderr or e.stdout}")
            raise RuntimeError(f"claude CLI failed: {e.stderr or e.stdout}")

class GenericCLIEngine(BaseEngine):
    def __init__(self, cmd_template: str, name="custom"):
        super().__init__(None, name)
        self.cmd_template = cmd_template

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5), retry=retry_if_exception_type(RuntimeError))
    def execute(self, prompt: str, images: Optional[List[str]] = None) -> str:
        if "{prompt}" in self.cmd_template:
            cmd = self.cmd_template.replace("{prompt}", prompt)
            stdin_data = None
        else:
            cmd = self.cmd_template
            stdin_data = prompt
            
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, input=stdin_data, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.warning(f"Custom CLI engine execution failed (retrying): {e.stderr or e.stdout}")
            raise RuntimeError(f"Custom CLI engine failed: {e.stderr or e.stdout}")

class FailoverEngine(BaseEngine):
    """Tries a list of engines sequentially if one fails permanently."""
    def __init__(self, engines: List[BaseEngine]):
        super().__init__(None, "failover")
        self.engines = engines

    def execute(self, prompt: str, images: Optional[List[str]] = None) -> str:
        last_exception = None
        for engine in self.engines:
            try:
                logger.info(f"Attempting execution with engine: {engine.name}")
                return engine.execute(prompt, images)
            except Exception as e:
                logger.error(f"Engine {engine.name} completely failed: {e}")
                last_exception = e
                continue
        raise RuntimeError(f"All failover engines failed. Last error: {last_exception}")

def register_custom_engine(name: str, cmd_template: str):
    name_clean = name.lower().strip()
    CUSTOM_ENGINES[name_clean] = GenericCLIEngine(cmd_template, name_clean)
    logger.info(f"Registered custom CLI engine: '{name_clean}' with command: '{cmd_template}'")

def _get_single_engine(name: str, model: str = None) -> BaseEngine:
    name_clean = name.lower().strip()
    if name_clean == "gemini":
        return GeminiEngine(model)
    elif name_clean == "codex":
        return CodexEngine(model)
    elif name_clean == "claude":
        return ClaudeEngine(model)
    elif name_clean in CUSTOM_ENGINES:
        return CUSTOM_ENGINES[name_clean]
    else:
        raise ValueError(f"Unsupported or unregistered engine type: '{name}'")

def get_engine(name: str, model: str = None) -> BaseEngine:
    """
    Returns an engine. If multiple names are provided (e.g. 'claude,gemini'),
    it returns a FailoverEngine that tries them in order.
    """
    if "," in name:
        names = [n.strip() for n in name.split(",") if n.strip()]
        engines = [_get_single_engine(n, model) for n in names]
        return FailoverEngine(engines)
    return _get_single_engine(name, model)
