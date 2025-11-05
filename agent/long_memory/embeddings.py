# agent/long_memory/embeddings.py
import os
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_ALIASES = {
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",  # 384d
    "bge": "BAAI/bge-base-en-v1.5",  # 768d (add prefixes)
    "e5": "intfloat/e5-base-v2",  # 768d (add prefixes)
    "nomic": "nomic-ai/nomic-embed-text-v1",  # 768d
}


def _resolve_model_name() -> tuple[str, str]:
    key = (os.getenv("EMBED_MODEL") or "minilm").lower()
    return key, MODEL_ALIASES.get(key, MODEL_ALIASES["minilm"])


def load_embedder():
    key, name = _resolve_model_name()
    print(f"[embeddings] loading: {name} ({key})")
    model = SentenceTransformer(name)
    return key, model


def _maybe_prefix(texts: List[str], model_key: str, mode: str) -> List[str]:
    # Asymmetric models benefit from query/passages prefixes
    if model_key in {"bge", "e5"}:
        prefix = "query: " if mode == "query" else "passage: "
        return [prefix + t for t in texts]
    return texts


def embed_texts(model: SentenceTransformer, texts: List[str], model_key: str, mode: str) -> np.ndarray:
    texts = _maybe_prefix(texts, model_key, mode)
    vecs = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return vecs.astype("float32")
