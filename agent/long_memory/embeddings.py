# agent/long_memory/embeddings.py
from __future__ import annotations

import os
from functools import lru_cache
from typing import Iterable, List

import numpy as np

# -----------------------------
# Model selection (local only)
# -----------------------------
# USE_MODEL env values:
#   minilm  -> sentence-transformers/all-MiniLM-L6-v2 (384 dims)
#   bge     -> BAAI/bge-small-en-v1.5                    (512 dims)
#   e5      -> intfloat/e5-small-v2                      (384 dims)
#
# Example:
#   USE_MODEL=bge python -m agent.long_memory.faiss_play build
#

_MODEL_ALIASES = {
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",
    "bge": "BAAI/bge-small-en-v1.5",
    "e5": "intfloat/e5-small-v2",
}


def _selected_alias() -> str:
    raw = (os.getenv("USE_MODEL") or "minilm").strip().lower()
    return raw if raw in _MODEL_ALIASES else "minilm"


def resolved_model_name() -> str:
    return _MODEL_ALIASES[_selected_alias()]


@lru_cache(maxsize=1)
def _load_model():
    name = resolved_model_name()
    print(f"[embeddings] loading: {name} ({_selected_alias()})")
    from sentence_transformers import SentenceTransformer

    # For BGE/e5, pooling/normalization handled the same way as MiniLM here.
    model = SentenceTransformer(name)
    return model


def _to_array(vectors: List[List[float]]) -> np.ndarray:
    arr = np.asarray(vectors, dtype="float32")
    # Normalize for cosine (so dot == cosine)
    norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
    return arr / norms


def embed_texts(texts: Iterable[str]) -> np.ndarray:
    """Batch embed a list of strings -> normalized float32 (n, d)."""
    model = _load_model()
    vectors = model.encode(list(texts), batch_size=64, convert_to_numpy=True, show_progress_bar=False)
    return _to_array(vectors.tolist())


def embed_query(text: str) -> np.ndarray:
    """Embed a single query string -> normalized (1, d)."""
    return embed_texts([text])
