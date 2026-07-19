import subprocess
import logging

logger = logging.getLogger("multicliswarm.git_autopilot")

def run_git_command(cmd: str, cwd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {result.stderr}")
    return result.stdout.strip()

def create_branch_and_commit(workspace_dir: str, branch_name: str, commit_message: str) -> bool:
    """
    Automates creating a new branch, staging all changes, and committing them.
    """
    try:
        # Check if inside a git repo
        subprocess.run("git status", shell=True, check=True, capture_output=True, cwd=workspace_dir)
        
        logger.info(f"Git Autopilot: Creating branch '{branch_name}'")
        run_git_command(f"git checkout -b {branch_name}", workspace_dir)
        
        logger.info("Git Autopilot: Staging files")
        run_git_command("git add .", workspace_dir)
        
        logger.info(f"Git Autopilot: Committing with message '{commit_message}'")
        safe_msg = commit_message.replace('"', '\\"')
        run_git_command(f'git commit -m "{safe_msg}"', workspace_dir)
        
        return True
    except subprocess.CalledProcessError:
        logger.warning("Directory is not a git repository. Skipping Git Autopilot.")
        return False
    except Exception as e:
        logger.error(f"Git Autopilot failed: {e}")
        return False
