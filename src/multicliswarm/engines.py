import os
import json
import subprocess
import tempfile
import logging
from typing import List, Optional

logger = logging.getLogger("multicliswarm.engines")

CUSTOM_ENGINES = {}

class BaseEngine:
    def __init__(self, model=None):
        self.model = model

    def execute(self, prompt: str, images: Optional[List[str]] = None) -> str:
        raise NotImplementedError("Subclasses must implement execute()")

class GeminiEngine(BaseEngine):
    def execute(self, prompt: str, images: Optional[List[str]] = None) -> str:
        cmd = ["gemini", "-p", prompt, "-o", "json"]
        if self.model:
            cmd += ["-m", self.model]
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return data.get("response", "").strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"gemini CLI invocation failed: {e.stderr or e.stdout}")
            raise RuntimeError(f"gemini CLI failed: {e.stderr or e.stdout}")
        except json.JSONDecodeError:
            return result.stdout.strip()

class CodexEngine(BaseEngine):
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
            logger.error(f"codex CLI invocation failed: {e.stderr or e.stdout}")
            raise RuntimeError(f"codex CLI failed: {e.stderr or e.stdout}")
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

class ClaudeEngine(BaseEngine):
    def execute(self, prompt: str, images: Optional[List[str]] = None) -> str:
        cmd = ["claude", "-p", prompt]
        if self.model:
            cmd += ["--model", self.model]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"claude CLI invocation failed: {e.stderr or e.stdout}")
            raise RuntimeError(f"claude CLI failed: {e.stderr or e.stdout}")

class GenericCLIEngine(BaseEngine):
    def __init__(self, cmd_template: str):
        super().__init__()
        self.cmd_template = cmd_template

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
            logger.error(f"Custom CLI engine execution failed: {e.stderr or e.stdout}")
            raise RuntimeError(f"Custom CLI engine failed: {e.stderr or e.stdout}")

def register_custom_engine(name: str, cmd_template: str):
    name_clean = name.lower().strip()
    CUSTOM_ENGINES[name_clean] = GenericCLIEngine(cmd_template)
    logger.info(f"Registered custom CLI engine: '{name_clean}' with command: '{cmd_template}'")

def get_engine(name: str, model: str = None) -> BaseEngine:
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
