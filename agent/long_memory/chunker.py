# agent/long_memory/chunker.py
from typing import List


def simple_paragraphs(text: str) -> List[str]:
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    return parts or ([text.strip()] if text.strip() else [])


def sliding_window(tokens: List[str], size: int = 120, stride: int = 60) -> List[str]:
    out = []
    i = 0
    while i < len(tokens):
        chunk = tokens[i:i + size]
        if not chunk: break
        out.append(" ".join(chunk))
        i += stride
    return out


def chunk_text(text: str, method: str = "para") -> List[str]:
    if method == "para":
        return simple_paragraphs(text)
    # token-ish split (very rough)
    toks = text.replace("\n", " ").split()
    return sliding_window(toks, 120, 60)
