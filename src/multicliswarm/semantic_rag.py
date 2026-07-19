import os
import pathspec
import logging
from typing import List, Dict
import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger("multicliswarm.semantic_rag")

class CodeIndexer:
    def __init__(self, persist_directory: str = ".multicliswarm_index"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        # Using a simple default embedding function
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(
            name="codebase", 
            embedding_function=self.emb_fn
        )

    def index_directory(self, directory: str):
        """Scans and indexes files in the directory."""
        if not os.path.exists(directory):
            return

        gitignore_path = os.path.join(directory, ".gitignore")
        ignore_patterns = [".git/", "node_modules/", "__pycache__/", "venv/", "env/", ".multicliswarm_index/"]
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r") as f:
                ignore_patterns.extend(f.readlines())

        spec = pathspec.PathSpec.from_lines('gitignore', ignore_patterns)
        
        ids = []
        documents = []
        metadatas = []

        for root, dirs, files in os.walk(directory):
            rel_root = os.path.relpath(root, directory)
            if rel_root == ".": rel_root = ""
            dirs[:] = [d for d in dirs if not spec.match_file(os.path.join(rel_root, d))]
            
            for file in files:
                rel_path = os.path.join(rel_root, file)
                if spec.match_file(rel_path) or file.startswith(".") or file in ["package-lock.json", "yarn.lock"]:
                    continue
                
                try:
                    full_path = os.path.join(root, file)
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if content.strip():
                            # We index small chunks or whole files if reasonable
                            # For simplicity, we index files as single documents
                            ids.append(rel_path)
                            documents.append(content)
                            metadatas.append({"path": rel_path})
                except (UnicodeDecodeError, PermissionError):
                    continue

        if ids:
            logger.info(f"Indexing {len(ids)} files into ChromaDB...")
            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def query(self, query_text: str, n_results: int = 5) -> str:
        """Searches for relevant code snippets."""
        results = self.collection.query(query_texts=[query_text], n_results=n_results)
        
        context = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                context.append(f"--- Relevant File: {meta['path']} ---\n{doc}\n")
        
        return "\n".join(context)
