# agent/long_memory/chunker.py
from __future__ import annotations
from typing import List


def chunk_text(text: str, max_chars: int = 256, overlap: int = 32) -> List[str]:
    """
    Split a long string into overlapping chunks.
    Works for documents, transcripts, Markdown, etc.

    Example:
        chunks = chunk_text(long_doc, max_chars=300, overlap=50)

    Returns list[str] with no chunk larger than `max_chars`,
    and each chunk overlaps the next by `overlap` characters.
    """
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    end = max_chars

    while start < len(text):
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap
        end = start + max_chars

    return chunks