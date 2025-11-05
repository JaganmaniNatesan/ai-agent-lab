# agent/long_memory/faiss_play.py
# agent/long_memory/play_embedding.py
import os
import sys

from .faiss_store import FaissStore
from .play_embedding import embed_texts, load_model

DIM = 384  # or your actual embedding dimension
INDEX_DIR = "storage/faiss_demo"

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


def build_index():
    os.makedirs(INDEX_DIR, exist_ok=True)
    texts = [
        "Apple is a red fruit.",
        "Banana is a yellow fruit.",
        "A doctor treats patients.",
        "A car has four wheels.",
    ]

    model = load_model(MODEL_NAME)
    vecs = embed_texts(model, texts)  # np.ndarray [N, DIM] (float32)
    ids = [f"doc_{i}" for i in range(len(texts))]

    store = FaissStore(dim=DIM, use_faiss=True)
    store.add(vecs, ids, texts)
    store.save(INDEX_DIR)
    print(f"[build] Saved FAISS index → {INDEX_DIR}")


def query_once(q: str, k: int = 3):
    from .play_embedding import embed_query
    model = load_model(MODEL_NAME)
    qv = embed_query(model, q)  # np.ndarray [1, DIM]
    store = FaissStore.load(INDEX_DIR, dim=DIM, use_faiss=True)
    results = store.search(qv, k=k)[0]
    for doc_id, text, score in results:
        print(f"{score:.3f}  {doc_id}  {text}")


if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        build_index()
    elif cmd == "query":
        q = " ".join(sys.argv[2:]) or "red fruit"
        query_once(q)
    else:
        print("Usage: python -m agent.long_memory.faiss_play [build|query <text>]")
