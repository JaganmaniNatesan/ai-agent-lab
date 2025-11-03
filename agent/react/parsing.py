"""
Model output normalization: strip fences, repair placeholders, and extract JSON.
"""

import re


def strip_noise(text: str) -> str:
    """Remove ```json fences and 'TOOL CALL:' prefixes the model may add."""
    t = re.sub(r"```json\s*|\s*```", "", text, flags=re.IGNORECASE).strip()
    t = re.sub(r"^\s*TOOL\s+CALL\s*:?:?\s*", "", t, flags=re.IGNORECASE).strip()
    return t


def quote_bare_placeholders(raw: str) -> str:
    """Fix common invalid output: {"text":<last_result>} → {"text":"<last_result>"}."""
    return re.sub(r'("text"\s*:\s*)(<[^>]+>)', r'\1"\2"', raw)


def extract_first_json(text: str) -> str | None:
    """Return the first top-level {...} block or None if not found."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None
