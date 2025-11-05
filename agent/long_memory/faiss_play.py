# agent/long_memory/faiss_play.py
from __future__ import annotations

import argparse
import os
from typing import List, Tuple

from .chunker import chunk_text
from .embeddings import embed_query, embed_texts, resolved_model_name
from .faiss_store import FaissStore

INDEX_DIR = "storage/faiss_demo"


def _sample_corpus() -> List[str]:
    # You can replace this with loading from a docs folder if you like.
    return [
        "Apple is a red fruit.",
        "Banana is a yellow fruit.",
        "A car has four wheels.",
        "Doctors help people get healthy.",
        "The apple cultivars vary widely by taste and color.",
        "Tires are essential for cars to move.",
        "Fruits like banana and mango are rich in potassium.",
        "Nurses work in hospitals and assist doctors caring for patients."
    ]


def _docs_to_chunks(docs: List[str]) -> Tuple[List[str], List[dict]]:
    texts: List[str] = []
    metas: List[dict] = []
    for i, d in enumerate(docs):
        for j, ch in enumerate(chunk_text(d, max_chars=256, overlap=32)):
            texts.append(ch)
            metas.append({"doc_id": f"doc_{i}", "chunk_id": j})
    return texts, metas


def build_index():
    docs = _sample_corpus()
    chunks, metas = _docs_to_chunks(docs)
    vecs = embed_texts(chunks)
    store = FaissStore(dim=vecs.shape[1])
    store.build(vecs, chunks, metas)
    store.save(INDEX_DIR)
    print(f"[build] Saved FAISS index → {INDEX_DIR}")


def query_once(q: str, top_k: int = 3):
    store = FaissStore.load(INDEX_DIR)
    qv = embed_query(q)
    hits = store.search(qv, top_k=top_k)
    print(f"loading embedding model: {resolved_model_name()} …")
    for sc, text, meta, ix in hits:
        print(f"{sc:0.3f}  {meta.get('doc_id', '?'):>5}  {text}")


def main():
    ap = argparse.ArgumentParser(description="FAISS demo: build / query")
    ap.add_argument("mode", choices=["build", "query"], help="build or query")
    ap.add_argument("query", nargs="?", default="", help="query text when mode=query")
    ap.add_argument("--topk", type=int, default=5)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(INDEX_DIR), exist_ok=True)

    if args.mode == "build":
        build_index()
    else:
        if not args.query:
            raise SystemExit("Provide a query string, e.g.  python -m agent.long_memory.faiss_play query 'red fruit'")
        query_once(args.query, top_k=args.topk)


if __name__ == "__main__":
    main()
