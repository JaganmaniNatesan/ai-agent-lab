"""
ReAct controller: builds the prompt, runs the loop, and applies heuristics.
"""

import json
from typing import List, Tuple

from agent.memory_adaptor import load_context, persist_turn
from agent.system_prompt import SYSTEM_PROMPT
from models.reason_llm import run_reasoning_model
from tools.registry import run_tool, resolve_tool

from .intents import classify_intent, wants_multi_step
from .parsing import strip_noise, quote_bare_placeholders, extract_first_json
from .prehandlers import (
    handle_preloops,
    is_identity_query,
    is_first_calc_query,
    is_summary_query,
    is_goodbye_query,
)
from .heuristics import maybe_finalize_greet, maybe_finalize_transform, maybe_finalize_math
from .utils import (
    format_memory,
    fill_placeholders,
    closest_tool_hint,
    find_name_in_history,
)


def run_react(prompt: str, session_id: str, max_steps: int = 10) -> str:
    """Execute a ReAct loop with small pre-loop short-circuits and guardrails."""
    # Fetch a wider window when name/summary/goodbye need prior context.
    base_limit = 6
    need_more = any((
        is_identity_query(prompt),
        is_first_calc_query(prompt),
        is_summary_query(prompt),
        is_goodbye_query(prompt),
    ))
    history: List[Tuple[str, str]] = load_context(session_id, limit=(20 if need_more else base_limit))
    memory_block = format_memory(history)

    controller = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Conversation so far:\n{memory_block}\n\n"
        f"USER: {prompt}\n"
        f"Thought:"
    )

    intent = classify_intent(prompt)
    step_limit = 10 if wants_multi_step(prompt) else min(max_steps, 4)

    print("\n=== 🧠 ReAct Debug Start ===")
    print(f"USER PROMPT: {prompt}")
    print(f"SESSION: {session_id}")
    print(f"INTENT: {intent} | STEP_LIMIT: {step_limit}")
    print("============================")


    # Pre-loop short-circuits (return final answer if applicable)
    pre = handle_preloops(prompt, history, persist_turn, session_id)
    if pre is not None:
        return pre

    last_result = None
    used_repair = False
    last_action_key: tuple | None = None
    repeat_count = 0

    for step in range(1, step_limit + 1):
        print(f"\n--- Step {step} ---")
        model_out = (run_reasoning_model(controller) or "").strip()
        print(f"[Model out]\n{model_out}\n")

        # Direct final answer string
        if model_out.startswith("Final Answer:"):
            final = model_out
            persist_turn(session_id, prompt, final)
            return final

        # Parse a JSON tool call
        cleaned = quote_bare_placeholders(strip_noise(model_out))
        json_block = extract_first_json(cleaned)

        if not json_block:
            if not used_repair:
                used_repair = True
                controller += (
                    "\nObservation: Your last output was invalid (expected a JSON tool call). "
                    "Respond ONLY with a valid JSON tool call as specified.\n"
                    "Guidance: Output exactly ONE JSON tool call next.\nThought:"
                )
                print("⚠️ No JSON detected. Issuing repair hint…")
                continue
            persist_turn(session_id, prompt, "Reached max reasoning steps without final answer.")
            return "Reached max reasoning steps without final answer."

        try:
            data = json.loads(json_block)
            tool = data.get("tool")
            args = data.get("args", {})
        except Exception as e:
            if not used_repair:
                used_repair = True
                controller += (
                    f"\nObservation: Invalid JSON ({e}). Output ONLY a corrected JSON tool call.\n"
                    "Guidance: Output exactly ONE JSON tool call next.\nThought:"
                )
                print(f"⚠️ JSON parse error: {e}. Issuing repair hint…")
                continue
            persist_turn(session_id, prompt, "Invalid JSON from model.")
            return "Invalid JSON from model."

        # Some models return a fake tool 'FINAL ANSWER'
        norm = resolve_tool(tool)
        if norm == "__final_answer__":
            text = (data.get("text") if isinstance(data, dict) else None)                            or (args or {}).get("text")                            or (str(last_result) if last_result is not None else "")
            final = f"Final Answer: {text}".strip()
            persist_turn(session_id, prompt, final)
            return final

        # Replace placeholders using the last observation
        args = fill_placeholders(args, last_result)

        # Greeting safety: prefer remembered name over generic placeholders
        if norm == "greeting":
            if not isinstance(args, dict):
                args = {}
            if not args.get("name") or str(args.get("name")).lower() in {"?", "user", "you"}:
                remembered = find_name_in_history(history)
                args["name"] = remembered or "User"

        # Execute the tool
        result = run_tool(norm, args)
        print(f"🧰 Tool call: {norm}({args}) -> {result}")
        last_result = result

        # Fail-safe: if user said goodbye but the model invoked 'greeting', convert to goodbye
        from .prehandlers import is_goodbye_query as _is_goodbye
        if _is_goodbye(prompt) and norm == "greeting":
            name = (args.get("name") if isinstance(args, dict) else None) or find_name_in_history(history) or "Friend"
            final = f"Final Answer: Goodbye {name}!"
            persist_turn(session_id, prompt, final)
            print("🛑 Auto-finalized: converted greeting to goodbye.")
            return final

        # Repeat detection: same tool + same args twice → finalize with current result
        import json as _json
        action_key = (norm, _json.dumps(args, sort_keys=True, ensure_ascii=False))
        if action_key == last_action_key:
            repeat_count += 1
        else:
            repeat_count = 1
            last_action_key = action_key
        if repeat_count >= 2:
            final = f"Final Answer: {last_result}"
            persist_turn(session_id, prompt, final)
            print("🛑 Auto-finalized: repeated same tool call twice.")
            return final

        # Heuristic early-stops
        for finalize in (
            lambda: maybe_finalize_greet(intent, norm, result),
            lambda: maybe_finalize_transform(intent, norm, result),
            lambda: maybe_finalize_math(intent, prompt,norm, result),
        ):
            msg = finalize()
            if msg:
                persist_turn(session_id, prompt, msg)
                print("🛑 Auto-finalized: heuristic satisfied.")
                return msg

        # Continue loop with observation
        controller += (
            f"\n{json_block}\nObservation: {result}\n"
            "Guidance: If the user's request is satisfied, output 'Final Answer: <text>' now. "
            "Otherwise, output exactly ONE next JSON tool call.\nThought:"
        )

    persist_turn(session_id, prompt, "Reached max reasoning steps without final answer.")
    return "Reached max reasoning steps without final answer."
