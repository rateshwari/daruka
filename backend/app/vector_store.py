"""
FAISS-backed retrieval over the seed corpus — Section 3.3 of the architecture doc.

Retrieval is metric-filtered THEN similarity-ranked: we first narrow to
chunks whose metric_affected overlaps the metrics the reasoning engine
flagged as relevant, then rank that subset by embedding similarity.
Pure semantic search alone tends to surface plausible-but-wrong-biome
evidence — filtering first fixes that.
"""
from __future__ import annotations
from typing import List, Optional
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from .seed_sources import SOURCE_CHUNKS

_MODEL_NAME = "all-MiniLM-L6-v2"


class VectorStore:
    def __init__(self):
        self.model = SentenceTransformer(_MODEL_NAME)
        self.chunks = SOURCE_CHUNKS
        texts = [c["text"] for c in self.chunks]
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        self.dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(self.dim)  # cosine sim via normalized IP
        self.index.add(np.array(embeddings, dtype="float32"))

    def retrieve(
        self,
        query: str,
        relevant_metrics: Optional[List[str]] = None,
        biome: Optional[str] = None,
        k: int = 4,
    ) -> List[dict]:
        # Step 1: filter by metric + biome applicability
        candidates = self.chunks
        if relevant_metrics:
            candidates = [
                c for c in candidates
                if set(c["metric_affected"]) & set(relevant_metrics)
            ]
        if biome:
            candidates = [c for c in candidates if biome in c["biome_applicability"]] or candidates

        if not candidates:
            candidates = self.chunks  # fallback: don't return nothing

        # Step 2: rank filtered candidates by embedding similarity to query
        idx_map = [self.chunks.index(c) for c in candidates]
        q_emb = self.model.encode([query], normalize_embeddings=True)
        cand_embs = np.array(
            [self.index.reconstruct(i) for i in idx_map], dtype="float32"
        )
        sims = cand_embs @ q_emb[0]
        ranked = sorted(zip(candidates, sims), key=lambda x: -x[1])
        return [c for c, _ in ranked[:k]]


_store: Optional[VectorStore] = None


def get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
