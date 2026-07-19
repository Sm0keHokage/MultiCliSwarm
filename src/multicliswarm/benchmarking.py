import subprocess
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger("multicliswarm.benchmarking")

# Commands to run performance benchmarks per language
BENCHMARK_CMDS = {
    "python": "python3 -m pytest {test_filename} --benchmark-only",
    "go": "go test -bench=.",
    "rust": "cargo bench",
    "javascript": "node {test_filename} --bench"
}

def run_performance_test(language: str, test_filename: str, output_dir: str) -> Optional[str]:
    """
    Executes a performance benchmark and returns the stdout result.
    """
    lang_clean = language.lower().strip()
    cmd_template = BENCHMARK_CMDS.get(lang_clean)
    
    if not cmd_template:
        logger.info(f"No benchmark command defined for {language}. Skipping.")
        return None
        
    cmd = cmd_template.format(test_filename=test_filename)
    
    try:
        logger.info(f"Running performance benchmark: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=output_dir, timeout=60)
        return result.stdout + "\n" + result.stderr
    except subprocess.TimeoutExpired:
        return "Benchmark timed out. Code may be extremely inefficient."
    except Exception as e:
        return f"Benchmark failed: {str(e)}"
