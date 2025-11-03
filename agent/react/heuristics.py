"""
Loop heuristics: math terminal op, greet/transform early exit.
"""

from .intents import wants_multi_step
from .utils import is_number


def terminal_op_for(prompt: str) -> str | None:
    p = prompt.lower()
    if "divide" in p or "/" in p:
        return "divide"
    if "multiply" in p or "times" in p or "*" in p:
        return "multiply"
    if "add" in p or "+" in p:
        return "add_numbers"
    return None


def maybe_finalize_greet(intent: str, norm: str, result) -> str | None:
    if intent == "greet" and norm == "greeting" and isinstance(result, str) and result:
        return f"Final Answer: {result}"
    return None


def maybe_finalize_transform(intent: str, norm: str, result) -> str | None:
    if intent == "transform" and norm == "to_uppercase" and isinstance(result, str) and result:
        return f"Final Answer: {result}"
    return None


def maybe_finalize_math(intent: str, prompt: str, norm: str, result) -> str | None:
    if intent != "math":
        return None

    # Single-step math: finalize on first numeric result.
    if is_number(result) and not wants_multi_step(prompt):
        return f"Final Answer: {result}"

    # Multi-step: finalize when terminal op appears with a numeric output.
    term = terminal_op_for(prompt)
    if wants_multi_step(prompt) and is_number(result) and term and norm == term:
        return f"Final Answer: {result}"

    return None
