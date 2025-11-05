# tools/knowledge_tool.py
import os
from typing import Dict, Any, List
from agent.long_memory.embeddings import load_embedder, embed_texts
from agent.long_memory.faiss_store import VectorStore, INDEX_DIR

# Simple in-process cache
_store = None
_key = None
_model = None

def _ensure_loaded():
    global _store, _key, _model
    if _store is not None:
        return
    _key, _model = load_embedder()
    _store = VectorStore(dim=384)  # will be overwritten by load()
    _store.load(INDEX_DIR)

def knowledge_search(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Args:
      { "query": str, "k": int=5 }
    Returns:
      { "matches": [ { "text": str, "score": float }, ... ] }
    """
    _ensure_loaded()
    q = str(args.get("query", "")).strip()
    k = int(args.get("k", 5))
    if not q:
        return {"error": "query is required"}
    qvec = embed_texts(_model, [q], _key, mode="query")
    hits = _store.search(qvec, k=k)
    return {"matches": [{"text": h.text, "score": h.score} for h in hits]}