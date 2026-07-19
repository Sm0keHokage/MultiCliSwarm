import os
import re
import networkx as nx
import logging
from typing import Dict, List, Any

logger = logging.getLogger("multicliswarm.visualizer")

def generate_dependency_graph(project_dir: str) -> Dict[str, Any]:
    """
    Analyzes imports in files to build a dependency graph.
    Returns a JSON-serializable structure of nodes and edges.
    """
    G = nx.DiGraph()
    
    # Common import regexes
    python_import = re.compile(r'^(?:from\s+(\S+)\s+import|import\s+(\S+))')
    js_import = re.compile(r'(?:import|from)\s+[\'"](.+?)[\'"]')
    
    files = []
    for root, _, filenames in os.walk(project_dir):
        for f in filenames:
            if f.endswith(('.py', '.js', '.ts', '.go', '.java')):
                files.append(os.path.relpath(os.path.join(root, f), project_dir))
                
    for f in files:
        G.add_node(f, type="file")
        full_path = os.path.join(project_dir, f)
        
        try:
            with open(full_path, "r", encoding="utf-8") as file_handle:
                content = file_file_handle.read()
                
                # Check for imports (simplified)
                # In a real app, we'd use language-specific parsers
                if f.endswith('.py'):
                    matches = python_import.findall(content)
                    for m in matches:
                        imp = m[0] or m[1]
                        # Try to resolve local imports
                        # This is a heuristic
                        G.add_edge(f, imp)
                elif f.endswith(('.js', '.ts')):
                    matches = js_import.findall(content)
                    for m in matches:
                        G.add_edge(f, m)
        except:
            continue
            
    # Convert to serializable format
    nodes = [{"id": n, "label": n} for n in G.nodes()]
    edges = [{"source": u, "target": v} for u, v in G.edges()]
    
    return {"nodes": nodes, "links": edges}
