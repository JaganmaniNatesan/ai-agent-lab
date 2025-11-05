# agent/long_memory/play_embedding.py
from __future__ import annotations

from typing import List

import numpy as np

from .embeddings import embed_texts, resolved_model_name


def cosine_sim(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # a: (n, d), b: (m, d) – both assumed normalized
    return a @ b.T


def pretty_pairwise(texts: List[str]):
    vecs = embed_texts(texts)  # normalized already
    print(f"Loaded local embedding model: {resolved_model_name()} …")

    # Print the first element’s first 5 dims (for sanity)
    print(f"vector for {texts[0]} first 5 dimensions {vecs[0, :5][0]}")

    sims = cosine_sim(vecs, vecs)  # (n, n)
    for i, t1 in enumerate(texts):
        for j, t2 in enumerate(texts):
            print(f"{t1:>10}  vs  {t2:<10} → {sims[i, j]:.3f}")
        print("-" * 50)


def main():
    # Simple probe set
    texts = ["apple", "red fruit", "car", "doctor", "banana","hospital", "nurse"]
    pretty_pairwise(texts)


if __name__ == "__main__":
    # Select model with env var USE_MODEL (minilm|bge|e5), e.g.:
    #   USE_MODEL=bge python -m agent.long_memory.play_embedding
    main()
