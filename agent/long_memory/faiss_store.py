# agent/long_memory/faiss_store.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import List, Tuple

import faiss
import numpy as np

INDEX_FILE = "index.faiss"
META_FILE = "meta.json"


@dataclass
class FaissStore:
    """Cosine similarity via inner-product FAISS (requires normalized vectors)."""

    dim: int
    index: faiss.Index = field(init=False)
    texts: List[str] = field(default_factory=list)
    metas: List[dict] = field(default_factory=list)

    def __post_init__(self):
        # Inner product == cosine if inputs are L2-normalized
        self.index = faiss.IndexFlatIP(self.dim)

    # -------- build/add/search --------
    def build(self, vectors: np.ndarray, texts: List[str], metas: List[dict]):
        assert vectors.ndim == 2 and vectors.shape[0] == len(texts) == len(metas)
        assert vectors.dtype == np.float32
        self.index.add(vectors)
        self.texts = list(texts)
        self.metas = list(metas)

    def add(self, vectors: np.ndarray, texts: List[str], metas: List[dict]):
        assert vectors.ndim == 2 and vectors.shape[0] == len(texts) == len(metas)
        self.index.add(vectors.astype("float32"))
        self.texts.extend(texts)
        self.metas.extend(metas)

    def search(self, query_vec: np.ndarray, top_k: int = 5) -> List[Tuple[float, str, dict, int]]:
        """
        Returns list of (score, text, meta, doc_id)
        Scores are cosine similarities in [0, 1+epsilon].
        """
        if query_vec.ndim == 1:
            query_vec = query_vec.reshape(1, -1)
        assert query_vec.shape[1] == self.dim

        scores, ids = self.index.search(query_vec.astype("float32"), top_k)
        out: List[Tuple[float, str, dict, int]] = []
        for sc, ix in zip(scores[0], ids[0]):
            if ix == -1:
                continue
            out.append((float(sc), self.texts[ix], self.metas[ix], int(ix)))
        return out

    # -------- persistence --------
    def save(self, out_dir: str):
        os.makedirs(out_dir, exist_ok=True)
        faiss.write_index(self.index, os.path.join(out_dir, INDEX_FILE))
        with open(os.path.join(out_dir, META_FILE), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "dim": self.dim,
                    "texts": self.texts,
                    "metas": self.metas,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    @staticmethod
    def load(in_dir: str) -> "FaissStore":
        index_path = os.path.join(in_dir, INDEX_FILE)
        meta_path = os.path.join(in_dir, META_FILE)
        if not (os.path.exists(index_path) and os.path.exists(meta_path)):
            raise FileNotFoundError(f"FAISS store not found in {in_dir}")

        index = faiss.read_index(index_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        store = FaissStore(dim=int(meta["dim"]))
        store.index = index
        store.texts = list(meta["texts"])
        store.metas = list(meta["metas"])
        return store
