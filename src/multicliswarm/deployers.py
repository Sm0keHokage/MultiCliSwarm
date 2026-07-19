import subprocess
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger("multicliswarm.deployers")

def deploy_to_vercel(project_dir: str) -> Optional[str]:
    """Deploys the project to Vercel and returns the URL."""
    try:
        logger.info("Deploying to Vercel...")
        result = subprocess.run("vercel --prod --yes", shell=True, capture_output=True, text=True, cwd=project_dir)
        if result.returncode == 0:
            # Extract URL from stdout (usually last line or similar)
            for line in result.stdout.splitlines():
                if "https://" in line:
                    return line.strip()
        return f"Vercel deploy failed: {result.stderr}"
    except Exception as e:
        return f"Vercel error: {str(e)}"

def deploy_to_gh_pages(project_dir: str) -> Optional[str]:
    """Simple gh-pages deployment wrapper."""
    try:
        logger.info("Deploying to GitHub Pages...")
        subprocess.run("npm run build && npx gh-pages -d dist", shell=True, check=True, cwd=project_dir)
        return "Deployed to GitHub Pages successfully."
    except Exception as e:
        return f"GH Pages error: {str(e)}"

DEPLOYERS = {
    "vercel": deploy_to_vercel,
    "gh-pages": deploy_to_gh_pages
}

def run_deploy(provider: str, project_dir: str) -> str:
    provider = provider.lower().strip()
    handler = DEPLOYERS.get(provider)
    if not handler:
        return f"Unknown provider: {provider}"
    return handler(project_dir)
