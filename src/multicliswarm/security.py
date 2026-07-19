import subprocess
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger("multicliswarm.security")

# Map languages to SAST security audit commands
SECURITY_AUDIT_CMDS = {
    "python": "bandit -r . -f json",
    "javascript": "npm audit --json",
    "typescript": "npm audit --json",
    "go": "go list -m all | xargs go list -json" # Basic dep check, ideally govulncheck
}

def run_security_audit(language: str, project_dir: str) -> Dict[str, Any]:
    """
    Runs a static analysis security test (SAST) and returns issues.
    """
    lang_clean = language.lower().strip()
    cmd = SECURITY_AUDIT_CMDS.get(lang_clean)
    
    if not cmd:
        logger.info(f"No security audit tool defined for {language}. Skipping.")
        return {"status": "skipped", "issues": []}
        
    try:
        logger.info(f"Running security audit: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=project_dir)
        
        # Note: result.returncode might be non-zero if issues are found
        # We parse the output (assuming JSON for bandit/npm audit)
        import json
        try:
            report = json.loads(result.stdout)
            return {"status": "completed", "report": report}
        except:
            return {"status": "completed", "raw_output": result.stdout + "\n" + result.stderr}
            
    except Exception as e:
        return {"status": "failed", "error": str(e)}
