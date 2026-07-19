import sys
import argparse
import logging
from .orchestrator import SwarmOrchestrator
from .engines import register_custom_engine

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

def main():
    parser = argparse.ArgumentParser(description="Multi-CLI Swarm (Universal MARE Algorithm)")
    
    parser.add_argument("--task", "-t", type=str, required=True, help="Description of the coding task.")
    parser.add_argument("--language", "-l", type=str, default="python", help="Target programming language (e.g. python, javascript, go, rust).")
    parser.add_argument("--file-name", "-f", type=str, help="Output target filename. If not provided, Architect decides.")
    
    # Engines
    parser.add_argument("--architect-engine", type=str, default="gemini", help="CLI engine for Architect role.")
    parser.add_argument("--developer-engines", type=str, default="gemini,codex", help="Comma-separated CLI engines for parallel Developer roles (e.g. gemini,codex).")
    parser.add_argument("--reviewer-engine", type=str, default="gemini", help="CLI engine for Reviewer role.")
    parser.add_argument("--synthesizer-engine", type=str, default="gemini", help="CLI engine for Synthesizer role.")
    parser.add_argument("--debugger-engine", type=str, default="gemini", help="CLI engine for Debugger role.")
    
    # Custom Engines Registration
    parser.add_argument(
        "--register-engine", "-r",
        type=str,
        action="append",
        default=[],
        help="Register a custom CLI engine. Format: 'name=command_template'. Example: -r 'ollama=ollama run llama3.1'"
    )
    
    # Options
    parser.add_argument("--test-cmd", type=str, help="Command to run unit tests. Injected variables: {test_filename}, {filename}.")
    parser.add_argument("--max-debug-cycles", type=int, default=3, help="Maximum number of test-debug-fix cycles.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose library logging.")
    
    args = parser.parse_args()
    
    if args.verbose:
        setup_logging()
        
    # Process custom engine registrations
    for reg_str in args.register_engine:
        if "=" not in reg_str:
            print(f"{Colors.FAIL}[ERROR] Invalid custom engine format: '{reg_str}'. Must be 'name=command_template'{Colors.ENDC}")
            sys.exit(1)
        name, template = reg_str.split("=", 1)
        register_custom_engine(name, template)
        
    dev_engines = [e.strip() for e in args.developer_engines.split(",")]
    
    # Beautiful CLI status printing callback
    def cli_callback(level: str, message: str):
        if level == "step":
            print(f"\n{Colors.HEADER}{Colors.BOLD}=== {message} ==={Colors.ENDC}")
        elif level == "success":
            print(f"{Colors.GREEN}[SUCCESS]{Colors.ENDC} {message}")
        elif level == "warning":
            print(f"{Colors.WARNING}[WARNING]{Colors.ENDC} {message}")
        elif level == "error":
            print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {message}")
        else:
            print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {message}")

    try:
        orchestrator = SwarmOrchestrator(
            architect_engine=args.architect_engine,
            developer_engines=dev_engines,
            reviewer_engine=args.reviewer_engine,
            synthesizer_engine=args.synthesizer_engine,
            debugger_engine=args.debugger_engine,
            max_debug_cycles=args.max_debug_cycles,
            callback=cli_callback
        )
        
        result = orchestrator.run(
            task=args.task,
            language=args.language,
            override_filename=args.file_name,
            test_cmd=args.test_cmd
        )
        
        if result["success"]:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Success! Code generated and fully verified.{Colors.ENDC}")
        else:
            print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️ Completed, but tests did not pass completely.{Colors.ENDC}")
            
        print(f"Implementation: {result['filename']}")
        print(f"Unit Tests: {result['test_filename']}")
        
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}[FATAL ERROR] {e}{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
