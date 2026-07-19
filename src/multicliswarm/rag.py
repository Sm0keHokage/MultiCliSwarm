import os
import pathspec
import logging

logger = logging.getLogger("multicliswarm.rag")

def get_codebase_context(directory: str, max_chars: int = 15000) -> str:
    """
    Scans a directory, respecting .gitignore, and returns a summary 
    of the codebase and contents of key files to act as RAG context.
    """
    if not os.path.exists(directory):
        return ""

    gitignore_path = os.path.join(directory, ".gitignore")
    ignore_patterns = [".git/", "node_modules/", "__pycache__/", "venv/", "env/"]
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            ignore_patterns.extend(f.readlines())

    spec = pathspec.PathSpec.from_lines('gitignore', ignore_patterns)
    
    file_tree = []
    file_contents = []
    current_chars = 0

    for root, dirs, files in os.walk(directory):
        # Filter directories relative to the root directory
        rel_root = os.path.relpath(root, directory)
        if rel_root == ".":
            rel_root = ""
            
        dirs[:] = [d for d in dirs if not spec.match_file(os.path.join(rel_root, d))]
        
        for file in files:
            rel_path = os.path.join(rel_root, file)
            
            if spec.match_file(rel_path):
                continue
                
            # Skip hidden files and common meta files to keep context clean
            if file.startswith(".") or file in ["package-lock.json", "poetry.lock", "yarn.lock"]:
                continue

            file_tree.append(rel_path)
            
            # Try reading the file if we have space
            if current_chars < max_chars:
                try:
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if len(content) < 5000: # Don't inject massive single files
                            file_contents.append(f"--- File: {rel_path} ---\n{content}\n")
                            current_chars += len(content)
                except (UnicodeDecodeError, PermissionError):
                    pass 

    tree_str = "Project Structure:\n" + "\n".join(file_tree)
    content_str = "\n".join(file_contents)
    
    return f"{tree_str}\n\nExisting Code Context:\n{content_str}"
