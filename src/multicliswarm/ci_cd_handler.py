import os
import sys
import logging
import argparse
from github import Github

logger = logging.getLogger("multicliswarm.ci")

def handle_issue(issue_number: int, repo_name: str, token: str):
    """
    Called by GitHub Actions when a new issue with a specific label is created.
    """
    g = Github(token)
    repo = g.get_repo(repo_name)
    issue = repo.get_issue(issue_number)
    
    logger.info(f"CI/CD Autopilot: Received Issue #{issue.number}: {issue.title}")
    
    task_desc = f"Fix GitHub Issue #{issue.number}: {issue.title}\n\nDescription:\n{issue.body}"
    
    # We run the swarm as a subprocess to keep the environment clean
    cmd = [
        "multicliswarm",
        "-t", task_desc,
        "--language", "python", # Ideally inferred from repo
        "--auto-route",
        "--auto-packages",
        "--use-docker",
        "--git-autopilot"
    ]
    
    try:
        # In a real environment, we'd use subprocess and stream the output back to the PR
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Swarm completed successfully. A PR should be created by git-autopilot.")
        
        # Add a comment to the issue
        issue.create_comment(f"🤖 **MultiCliSwarm Autopilot** has successfully processed this issue. A Pull Request has been created with the fix and tests.")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Swarm failed: {e.stderr}")
        issue.create_comment(f"🤖 **MultiCliSwarm Autopilot** attempted to fix this but encountered an error:\n```\n{e.stderr[-1000:]}\n```")

def main():
    parser = argparse.ArgumentParser(description="MultiCliSwarm CI/CD Autopilot")
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--repo", type=str, required=True)
    parser.add_argument("--token", type=str, required=True)
    
    args = parser.parse_args()
    handle_issue(args.issue, args.repo, args.token)

if __name__ == "__main__":
    main()
