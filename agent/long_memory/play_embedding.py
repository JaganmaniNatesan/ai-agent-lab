# agent/long_memory/play_embedding.py
import os
import sys
from typing import List

import numpy as np

# ---- Model options (pick via CLI or env) ----
# CLI: python play_embedding.py bge
# ENV:  EMBED_MODEL=bge python play_embedding.py
MODEL_ALIASES = {
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",  # 384d
    "bge": "BAAI/bge-base-en-v1.5",  # 768d (asymmetric capable)
    "e5": "intfloat/e5-base-v2",  # 768d (use 'query:'/'passage:')
    "nomic": "nomic-ai/nomic-embed-text-v1",  # 768d
}

DEFAULT_MODEL_KEY = os.getenv("EMBED_MODEL", "").lower() or (sys.argv[1].lower() if len(sys.argv) > 1 else "minilm")
MODEL_NAME = MODEL_ALIASES.get(DEFAULT_MODEL_KEY, MODEL_ALIASES["minilm"])

from sentence_transformers import SentenceTransformer


# --- NEW HELPERS FOR CONSISTENT EMBEDDING ---

def embed_texts(model, texts: list[str]):
    """Embed multiple texts → np.ndarray [N, DIM]"""
    return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)


def embed_query(model, text: str):
    """Embed a single text → np.ndarray [1, DIM]"""
    return model.encode([text], convert_to_numpy=True, normalize_embeddings=True)


def load_model(name: str) -> SentenceTransformer:
    print(f"Loading embedding model: {name} …")
    return SentenceTransformer(name, trust_remote_code=True)


def _maybe_prefix(texts: List[str], model_key: str, mode: str) -> List[str]:
    """
    For asymmetric models (BGE/E5), better quality with prefixes:
    - Queries: 'query: ...'
    - Documents: 'passage: ...'
    mode in {'query','doc'}
    """
    if model_key in ("bge", "e5"):
        prefix = "query: " if mode == "query" else "passage: "
        return [prefix + t for t in texts]
    return texts


def embed_texts(model: SentenceTransformer, texts: List[str]) -> np.ndarray:
    emb = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return emb  # shape: (n, d), L2-normalized so cosine = dot


def cosine_sim_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    # embeddings are normalized → cosine = dot product
    return A @ B.T


def main():
    candidates = ["apple", "red fruit", "car", "doctor", "banana"]
    # Treat all as "documents"; then compare each against all (query side)
    model_key = DEFAULT_MODEL_KEY
    model = load_model(MODEL_NAME)

    docs = _maybe_prefix(candidates, model_key, mode="doc")
    Qs = _maybe_prefix(candidates, model_key, mode="query")

    doc_vecs = embed_texts(model, docs)
    qry_vecs = embed_texts(model, Qs)

    # Sanity: show a peek into one vector
    print(f"vector for {candidates[0]} first dim {doc_vecs[0][0]}")

    sims = cosine_sim_matrix(qry_vecs, doc_vecs)
    # Pretty print a sorted view per anchor term
    for i, t1 in enumerate(candidates):
        for j, t2 in sorted(
                enumerate(candidates),
                key=lambda p: sims[i, p[0]],
                reverse=True
        ):
            print(f"{t1:>10}  vs  {t2:<10} → {sims[i, j]:.3f}")
        print("-" * 50)


if __name__ == "__main__":
    main()
