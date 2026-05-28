import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List
import logging

_model = SentenceTransformer("all-MiniLM-L6-v2")
logger = logging.getLogger(__name__)

class DocumentIndex:
    def __init__(self):
        self.chunks = []
        self.index = None

    def build(self, structured_chunks: List[dict]):
        """Pass in the chunks list from DocumentProcessor.process_file()"""
        if not structured_chunks:
            raise ValueError("No chunks provided for indexing.")
        self.chunks = structured_chunks
        texts = [c["text"] for c in structured_chunks]
        
        embeddings = np.array(_model.encode(texts, show_progress_bar=False), dtype="float32")
        
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)
        logger.info("FAISS index built: chunks=%s", len(self.chunks))

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        if self.index is None:
            raise ValueError("Index not built. Call build() first.")
        query_vec = np.array(_model.encode([query]), dtype="float32")
        k = min(top_k, len(self.chunks))
        distances, indices = self.index.search(query_vec, k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= len(self.chunks):
                continue
            # Convert L2 distance to a bounded similarity-like score.
            similarity = 1.0 / (1.0 + float(dist))
            chunk = self.chunks[idx]
            results.append(
                {
                    "chunk_id": chunk["id"],
                    "chunk": chunk["text"],
                    "chunk_index": int(idx),
                    "score": float(dist),
                    "similarity": similarity,
                    "metadata": chunk.get("metadata", {}),
                }
            )
        logger.info("Retrieval complete: query='%s' top_k=%s hits=%s", query, top_k, len(results))
        return results