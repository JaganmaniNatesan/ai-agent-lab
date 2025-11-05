# agent/long_memory/faiss_store.py
import json
import os

import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

INDEX_FILE = "index.faiss"
IDS_FILE = "ids.json"
TEXTS_FILE = "texts.json"
VECS_FILE = "vectors.npy"  # still used for non-FAISS (numpy) fallback


class FaissStore:
    """
    Minimal vector store that supports two modes:
      - FAISS backend: uses self.index (faiss.Index / IndexIDMap2)
      - NumPy backend: uses self.vectors (np.ndarray) + self.ids/texts
    """

    def __init__(self, dim: int, use_faiss: bool = True):
        self.dim = dim
        self.use_faiss = use_faiss and (faiss is not None)
        self.ids: list[str] = []
        self.texts: list[str] = []

        if self.use_faiss:
            # IP for cosine-normalised vectors; wrap with ID map so we persist our ids
            base = faiss.IndexFlatIP(dim)
            self.index = faiss.IndexIDMap2(base)
            self.vectors = None  # not used
        else:
            self.index = None
            self.vectors = np.zeros((0, dim), dtype="float32")

    # --- add vectors ---
    def add(self, vecs: np.ndarray, ids: list[str], texts: list[str]):
        vecs = vecs.astype("float32")
        assert vecs.shape[0] == len(ids) == len(texts)
        self.ids.extend(ids)
        self.texts.extend(texts)

        if self.use_faiss:
            # map custom integer ids for FAISS (use positional indices)
            int_ids = np.arange(len(self.ids) - len(ids), len(self.ids)).astype("int64")
            self.index.add_with_ids(vecs, int_ids)
        else:
            self.vectors = np.vstack([self.vectors, vecs])

    # --- search ---
    def search(self, q: np.ndarray, k: int = 5):
        q = q.astype("float32")
        if self.use_faiss:
            scores, int_ids = self.index.search(q, k)
            # translate back to our string ids/texts by position
            results = []
            for row, row_ids in zip(scores, int_ids):
                row_result = []
                for pos, score in zip(row_ids, row):
                    if pos == -1:
                        continue
                    # our ids/texts are positional
                    row_result.append((self.ids[pos], self.texts[pos], float(score)))
                results.append(row_result)
            return results
        else:
            # naive cosine using numpy
            norms = np.linalg.norm(self.vectors, axis=1, keepdims=True) + 1e-8
            base = self.vectors / norms
            qn = q / (np.linalg.norm(q, axis=1, keepdims=True) + 1e-8)
            sims = qn @ base.T
            topk = np.argpartition(-sims, kth=min(k, sims.shape[1] - 1))[:, :k]
            results = []
            for i, idxs in enumerate(topk):
                row = sorted(
                    [(self.ids[j], self.texts[j], float(sims[i, j])) for j in idxs],
                    key=lambda x: x[2],
                    reverse=True
                )
                results.append(row[:k])
            return results

    # --- persistence ---
    def save(self, out_dir: str):
        os.makedirs(out_dir, exist_ok=True)
        # ids/texts always saved
        with open(os.path.join(out_dir, IDS_FILE), "w") as f:
            json.dump(self.ids, f)
        with open(os.path.join(out_dir, TEXTS_FILE), "w") as f:
            json.dump(self.texts, f)

        if self.use_faiss:
            if faiss is None:
                raise RuntimeError("FAISS not installed but use_faiss=True")
            faiss.write_index(self.index, os.path.join(out_dir, INDEX_FILE))
        else:
            # numpy fallback
            np.save(os.path.join(out_dir, VECS_FILE), self.vectors.astype("float32"))

    @classmethod
    def load(cls, in_dir: str, dim: int, use_faiss: bool = True):
        store = cls(dim=dim, use_faiss=use_faiss and (faiss is not None))
        # load ids/texts
        with open(os.path.join(in_dir, IDS_FILE)) as f:
            store.ids = json.load(f)
        with open(os.path.join(in_dir, TEXTS_FILE)) as f:
            store.texts = json.load(f)

        if store.use_faiss:
            store.index = faiss.read_index(os.path.join(in_dir, INDEX_FILE))
        else:
            store.vectors = np.load(os.path.join(in_dir, VECS_FILE)).astype("float32")
        return store
