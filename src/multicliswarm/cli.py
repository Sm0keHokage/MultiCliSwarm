import sys
import argparse
import logging
from .orchestrator import SwarmOrchestrator
from .engines import register_custom_engine
from .schemas import ArchitectResponse
from .telemetry import init_telemetry
from .db import list_snapshots

# ANSI colors for pretty terminal prints
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def ask_approval_cli(task: str, arch_response: ArchitectResponse) -> bool:
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== HUMAN-IN-THE-LOOP APPROVAL ==={Colors.ENDC}")
    print(f"{Colors.BLUE}Task:{Colors.ENDC} {task}")
    print(f"\n{Colors.CYAN}Files to generate:{Colors.ENDC}")
    for f in arch_response.files:
        print(f"  - {f.filepath} (Test: {f.is_test}): {f.description}")
    
    if arch_response.custom_tools:
        print(f"\n{Colors.CYAN}Custom Tools to evolve:{Colors.ENDC}")
        for t in arch_response.custom_tools:
            print(f"  - {t.tool_name}")

    print(f"\n{Colors.WARNING}Do you approve this architecture plan? (y/n): {Colors.ENDC}", end="")
    choice = sys.stdin.readline().strip().lower()
    return choice == 'y' or choice == 'yes'

def main():
    parser = argparse.ArgumentParser(description="Multi-CLI Swarm (Production Ecosystem v1.0.0)")
    
    parser.add_argument("--task", "-t", type=str, required=True, help="Description of the coding task.")
    parser.add_argument("--language", "-l", type=str, default="python", help="Target programming language.")
    parser.add_argument("--resume", type=str, help="Resume a previous session ID.")
    parser.add_argument("--snapshot", type=str, help="Resume from a specific snapshot ID.")
    parser.add_argument("--list-snapshots", action="store_true", help="List available snapshots for a session.")
    parser.add_argument("--context-dir", type=str, help="Path to existing codebase.")
    
    # Engines
    parser.add_argument("--architect-engine", type=str, default="gemini", help="CLI engine(s) for Architect.")
    parser.add_argument("--developer-engines", type=str, default="gemini,codex", help="Comma-separated CLI engines for parallel Developers.")
    
    # Production Features
    parser.add_argument("--semantic-rag", action="store_true", help="Enable ChromaDB vector search for context.")
    parser.add_argument("--semantic-cache", action="store_true", help="Enable semantic caching of AI responses.")
    parser.add_argument("--use-docker", action="store_true", help="Run tests safely in isolated Docker containers.")
    parser.add_argument("--auto-packages", action="store_true", help="Autonomous Package Management.")
    parser.add_argument("--auto-route", action="store_true", help="Enable dynamic model routing.")
    parser.add_argument("--web-search", action="store_true", help="Enable real-time Web Search RAG.")
    parser.add_argument("--visual-qa", action="store_true", help="Enable Visual QA via Vision models.")
    parser.add_argument("--git-autopilot", action="store_true", help="Enable Git Autopilot.")
    parser.add_argument("--pair-programming", action="store_true", help="Enable interactive Pair Programming mode.")
    
    parser.add_argument("--telemetry", action="store_true", help="Enable OpenTelemetry tracing.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging.")
    
    args = parser.parse_args()
    
    if args.verbose:
        setup_logging()
    if args.telemetry:
        init_telemetry(enable_console=True)
        
    if args.list_snapshots and args.resume:
        snaps = list_snapshots(args.resume)
        print(f"\n{Colors.BOLD}Snapshots for session {args.resume}:{Colors.ENDC}")
        for s in snaps:
            print(f" - {s['id']} [{s['date']}]: {s['label']}")
        sys.exit(0)

    try:
        orchestrator = SwarmOrchestrator(
            architect_engine=args.architect_engine,
            developer_engines=[e.strip() for e in args.developer_engines.split(",")],
            use_docker=args.use_docker,
            auto_route=args.auto_route,
            web_search=args.web_search,
            visual_qa=args.visual_qa,
            auto_packages=args.auto_packages,
            git_autopilot=args.git_autopilot,
            pair_programming=args.pair_programming,
            semantic_rag=args.semantic_rag,
            semantic_cache=args.semantic_cache,
            callback=lambda level, message: print(f"{Colors.BLUE}[{level.upper()}]{Colors.ENDC} {message}"),
            ask_approval=ask_approval_cli
        )
        
        result = orchestrator.run(
            task=args.task,
            language=args.language,
            resume_session_id=args.resume,
            resume_snapshot_id=args.snapshot,
            context_dir=args.context_dir
        )
        
        if result.get("status") == "cancelled":
            sys.exit(0)
            
        if result["success"]:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Success! v1.0.0 Swarm completed verified production deployment.{Colors.ENDC}")
        
        print(f"\nSession ID: {result['session_id']}")
            
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}[FATAL ERROR] {e}{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
