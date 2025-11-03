"""
General helpers: memory formatting, name extraction, numeric checks, hints, summary.
"""

import difflib
import re
from typing import Any, List, Tuple

# Placeholders some models emit to reference previous tool output.
PLACEHOLDERS = {
    "<last_result>", "<previous_result>", "<previous_answer>",
    "<LAST_ANSWER>", "<last_answer>"
}


def format_memory(pairs: List[Tuple[str, str]]) -> str:
    """Render (role, content) pairs to a readable transcript block."""
    return "\n".join([
        ("User: " if role == "user" else "Assistant: ") + content
        for role, content in pairs
    ])


def is_number(x: Any) -> bool:
    if isinstance(x, (int, float)):
        return True
    if isinstance(x, str):
        try:
            float(x.strip())
            return True
        except Exception:
            return False
    return False


def fill_placeholders(args: dict, last_result):
    """Replace placeholder strings in args with the last_result (stringified)."""
    if last_result is None or not isinstance(args, dict):
        return args
    out = {}
    for k, v in args.items():
        out[k] = str(last_result) if isinstance(v, str) and v in PLACEHOLDERS else v
    return out


def closest_tool_hint(bad_name: str, valid: list[str]) -> str:
    """Suggest the closest valid tool name."""
    matches = difflib.get_close_matches(bad_name or "", valid, n=1, cutoff=0.6)
    return matches[0] if matches else ""


# ---- Name extraction & summary ------------------------------------------------

_NAME_PATTERNS = [
    r"\bmy name is ([A-Z][a-zA-Z]+)\b",
    r"\bi am ([A-Z][a-zA-Z]+)\b",
    r"\bi'm ([A-Z][a-zA-Z]+)\b",
    r"\bcall me ([A-Z][a-zA-Z]+)\b",
    r"\bhello ([A-Z][a-zA-Z]+)\b",
    r"\bhi ([A-Z][a-zA-Z]+)\b",
]


def extract_name_from_prompt(text: str) -> str | None:
    m = re.search(r"\bmy name is\s+([A-Za-z][A-Za-z .'-]{0,40})\b", text, flags=re.IGNORECASE)
    return m.group(1).strip() if m else None


def find_name_in_history(pairs: List[Tuple[str, str]]) -> str | None:
    """Look backwards for a stated or greeted name and return it normalized."""
    for role, content in reversed(pairs):
        t = content.strip()
        for pat in _NAME_PATTERNS:
            m = re.search(pat, t, flags=re.IGNORECASE)
            if m:
                name = m.group(1).strip()
                return name[0].upper() + name[1:].lower()
    return None


def summarize_one_line(pairs: List[Tuple[str, str]]) -> str:
    """Produce a single, natural sentence summarizing the last few turns."""
    recent = pairs[-6:]
    name = find_name_in_history(recent)

    did_math = False
    math_vals: list[str] = []
    did_transform = False

    for role, content in recent:
        if role != "assistant":
            continue
        m = re.search(r"Final Answer:\s*([-+]?\d+(?:\.\d+)?)\b", content)
        if m:
            did_math = True
            math_vals.append(m.group(1))
        if "Final Answer:" in content and re.search(r"[A-Z]{3,}", content):
            did_transform = True

    bits: list[str] = []
    bits.append(f"greeted you as {name}" if name else "exchanged a greeting")
    if did_math and math_vals:
        bits.append(f"did some math ending at {math_vals[-1]}")
    if did_transform:
        bits.append("applied an uppercase transform")

    last_user = next((c for r, c in reversed(recent) if r == "user"), None)
    if last_user:
        import re as _re
        last_user = _re.sub(r"\s+", " ", last_user).strip().rstrip(".")
        bits.append(f'and you asked: "{last_user}"')

    sent = ", ".join(bits)
    return sent[0].upper() + sent[1:] + "."
