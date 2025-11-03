"""
Lightweight intent detection and multi-step hinting.
"""

import re


def classify_intent(text: str) -> str:
    """Return one of: 'greet' | 'math' | 'transform' | 'unknown'."""
    t = text.lower()
    if re.search(r"\b(hi|hello|hey)\b", t) or "my name is" in t:
        return "greet"
    if re.search(r"\b(add|sum|\+|multiply|times|\*|x|divide|/)\b", t):
        return "math"
    if re.search(r"\buppercase|lowercase|capitalize|title case\b", t):
        return "transform"
    return "unknown"


def wants_multi_step(text: str) -> bool:
    """True if the user phrasing implies sequential steps (then/and then/after that/next)."""
    return bool(re.search(r"\b(then|and then|after that|next)\b", text.lower()))
