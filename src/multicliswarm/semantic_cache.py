import logging
from typing import Optional
import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger("multicliswarm.semantic_cache")

class SemanticCache:
    def __init__(self, persist_directory: str = ".multicliswarm_cache"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(
            name="responses", 
            embedding_function=self.emb_fn
        )

    def get(self, prompt: str, threshold: float = 0.15) -> Optional[str]:
        """
        Retrieves a cached response if a semantically similar prompt exists.
        Threshold: distance where 0 is identical.
        """
        results = self.collection.query(query_texts=[prompt], n_results=1)
        
        if results['distances'] and results['distances'][0]:
            distance = results['distances'][0][0]
            if distance < threshold:
                logger.info(f"Semantic Cache Hit (distance: {distance:.4f})")
                return results['documents'][0][0]
        
        return None

    def set(self, prompt: str, response: str):
        """Stores a prompt-response pair in the cache."""
        import uuid
        self.collection.upsert(
            ids=[str(uuid.uuid4())],
            documents=[response],
            metadatas=[{"prompt": prompt[:500]}] # Metadata for debugging
        )
