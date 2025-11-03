"""
Pre-loop controller actions that can finalize immediately:
- remember name
- who am I?
- one-line summary
- first calculation result
- goodbye (personalized)
"""

import re
from typing import List, Tuple

from .utils import extract_name_from_prompt, find_name_in_history, summarize_one_line


# --- Query recognizers ---------------------------------------------------------

def is_identity_query(prompt: str) -> bool:
    return bool(re.search(r"\bwho am i\??$", prompt.strip(), flags=re.IGNORECASE))


def is_summary_query(prompt: str) -> bool:
    return bool(re.search(
        r"\b(what (did|have) we (talked|talked about) so far|one line|summary|summarise|summarize)\b",
        prompt,
        flags=re.IGNORECASE,
    ))


def is_remember_name(prompt: str) -> bool:
    t = prompt.lower()
    return "remember my name" in t or bool(re.search(r"\bremember that my name is\b", t))


def is_first_calc_query(prompt: str) -> bool:
    return bool(re.search(r"\b(first|1st)\s+calculation\b", prompt, flags=re.IGNORECASE))


def is_goodbye_query(prompt: str) -> bool:
    return bool(re.search(
        r"(?:^|\b)(good\s*bye|goodbye|bye|see\s+you|see\s+ya|later)(?:[.!?]|\b|$)",
        prompt,
        flags=re.IGNORECASE,
    ))


# --- Extractors ----------------------------------------------------------------

def find_first_numeric_answer(pairs: List[Tuple[str, str]]) -> str | None:
    """Return the earliest assistant 'Final Answer: <number>' or earliest bare numeric."""
    import re
    for role, content in pairs:
        if role != "assistant":
            continue
        m = re.search(r"Final Answer:\s*([-+]?\d+(?:\.\d+)?)\b", content)
        if m:
            return m.group(1)
    for role, content in pairs:
        if role != "assistant":
            continue
        m = re.search(r"\b([-+]?\d+(?:\.\d+)?)\b", content)
        if m:
            return m.group(1)
    return None


# --- Dispatcher ----------------------------------------------------------------

def handle_preloops(prompt: str, history: List[Tuple[str, str]], persist_turn, session_id: str) -> str | None:
    """Return a final answer string if a pre-loop handler applies, otherwise None."""

    # Remember my name
    if is_remember_name(prompt):
        name = extract_name_from_prompt(prompt) or find_name_in_history(history) or "you"
        final = f"Final Answer: Got it — I’ll remember your name: {name}."
        persist_turn(session_id, prompt, final)
        return final

    # Who am I?
    if is_identity_query(prompt):
        name = find_name_in_history(history)
        final = f"Final Answer: You are {name}." if name else (
            "Final Answer: I don’t have your name yet — tell me “My name is …” and I’ll remember."
        )
        persist_turn(session_id, prompt, final)
        return final

    # Conversation summary
    if is_summary_query(prompt):
        final = f"Final Answer: {summarize_one_line(history)}"
        persist_turn(session_id, prompt, final)
        return final

    # First calculation result
    if is_first_calc_query(prompt):
        n = find_first_numeric_answer(history)
        final = f"Final Answer: {n}" if n is not None else (
            "Final Answer: I couldn't find a prior calculation in this session."
        )
        persist_turn(session_id, prompt, final)
        return final

    # Polite goodbye (personalized if we know a name)
    if is_goodbye_query(prompt):
        name = find_name_in_history(history)
        final = f"Final Answer: Goodbye {name}!" if name else "Final Answer: Goodbye!"
        persist_turn(session_id, prompt, final)
        return final

    return None
