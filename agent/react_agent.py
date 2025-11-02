# agent/react_agent.py
import difflib
import json
import re
from typing import List, Tuple, Any

from agent.memory_adaptor import load_context, persist_turn
from agent.system_prompt import SYSTEM_PROMPT
from models.reason_llm import run_reasoning_model
from tools.registry import run_tool, resolve_tool

# Placeholders the model might emit for "use last observation"
PLACEHOLDERS = {
    "<last_result>", "<previous_result>", "<previous_answer>",
    "<LAST_ANSWER>", "<last_answer>"
}


# --- Very light intent classifier for early-stop heuristics ---
def _classify_intent(user_text: str) -> str:
    """
    Returns: 'greet' | 'math' | 'transform' | 'unknown'
    """
    t = user_text.lower().strip()
    if re.search(r"\b(hi|hello|hey)\b", t) or "my name is" in t:
        return "greet"
    if re.search(r"\b(add|sum|plus|multiply|times|divide|/|\+|\*|\bx\b)\b", t):
        return "math"
    if re.search(r"\buppercase|lowercase|capitalize|title case\b", t):
        return "transform"
    return "unknown"


def _wants_multi_step(user_text: str) -> bool:
    t = user_text.lower()
    return bool(re.search(r"\b(then|and then|after that|next)\b", t))


def _is_number(x: Any) -> bool:
    if isinstance(x, (int, float)):
        return True
    if isinstance(x, str):
        try:
            float(x.strip())
            return True
        except Exception:
            return False
    return False


def _is_goodbye_query(prompt: str) -> bool:
    return bool(re.search(r"\b(bye|goodbye|see you|later)\b", prompt.lower()))


def _format_memory(pairs: List[Tuple[str, str]]) -> str:
    # pairs: [(role, content), ...] in chronological order
    return "\n".join([("User: " if r == "user" else "Assistant: ") + c for (r, c) in pairs])


def _strip_noise(text: str) -> str:
    # Remove code fences and "TOOL CALL" prefix
    t = re.sub(r"```json\s*|\s*```", "", text, flags=re.IGNORECASE).strip()
    t = re.sub(r"^\s*TOOL\s+CALL\s*:?\s*", "", t, flags=re.IGNORECASE).strip()
    return t


def _extract_first_json(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def _quote_bare_placeholders(raw: str) -> str:
    # Fixes common invalid form: {"text":<last_result>} → {"text":"<last_result>"}
    return re.sub(r'("text"\s*:\s*)(<[^>]+>)', r'\1"\2"', raw)


def _fill_placeholders(args: dict, last_result):
    if last_result is None or not isinstance(args, dict):
        return args
    fixed = {}
    for k, v in args.items():
        if isinstance(v, str) and v in PLACEHOLDERS:
            fixed[k] = str(last_result)
        else:
            fixed[k] = v
    return fixed


def _closest_tool_hint(bad_name: str, valid_names: list[str]) -> str:
    matches = difflib.get_close_matches(bad_name, valid_names, n=1, cutoff=0.6)
    return matches[0] if matches else ""


# --- Pre-loop helper logic for "remember/identity/summary/first calc" ---
def _extract_name_from_prompt(text: str) -> str | None:
    t = text.strip()
    m = re.search(r"\bmy name is\s+([A-Za-z][A-Za-z .'-]{0,40})\b", t, flags=re.IGNORECASE)
    return m.group(1).strip() if m else None



def _find_name_in_history(pairs: List[Tuple[str, str]]) -> str | None:
    """
    Scan recent (role, content) memory for name patterns like:
      - "My name is Jagan"
      - "I'm Alice"
      - "Call me Bob"
      - system-stored: "Final Answer: Hello Jagan"
    Returns the most recent detected name, or None.
    """
    name_patterns = [
        r"\bmy name is ([A-Z][a-zA-Z]+)\b",
        r"\bi am ([A-Z][a-zA-Z]+)\b",
        r"\bi'm ([A-Z][a-zA-Z]+)\b",
        r"\bcall me ([A-Z][a-zA-Z]+)\b",
        r"\bhello ([A-Z][a-zA-Z]+)\b",
        r"\bhi ([A-Z][a-zA-Z]+)\b",
    ]

    for role, content in reversed(pairs):  # newest first
        text = content.strip()
        for pat in name_patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                name = m.group(1).strip()
                # normalize: JAGAN → Jagan
                return name[0].upper() + name[1:].lower()
    return None


def _summarize_one_line(pairs: List[Tuple[str, str]]) -> str:
    """
    Build a single, natural sentence summarizing the last few turns.
    Heuristic: mention greeting/name (if any), math results, transform, and last user intent.
    """
    recent = pairs[-6:]  # last 6 turns
    name = _find_name_in_history(recent)
    did_math = False
    math_vals = []
    did_transform = False

    # scan assistant finals & user intents
    for role, content in recent:
        if role == "assistant":
            m = re.search(r"Final Answer:\s*([-+]?\d+(?:\.\d+)?)\b", content)
            if m:
                did_math = True
                math_vals.append(m.group(1))
            if "Final Answer:" in content and content.strip().endswith("0") is False:
                # detect obvious transform answers like “HELLO JAGAN” or uppercased words/numbers
                if re.search(r"[A-Z]{3,}", content):
                    did_transform = True

    bits = []
    if name:
        bits.append(f"greeted you as {name}")
    else:
        bits.append("exchanged a greeting")

    if did_math and math_vals:
        last_num = math_vals[-1]
        bits.append(f"did some math ending at {last_num}")

    if did_transform:
        bits.append("applied an uppercase transform")

    # pick last user message as the current focus
    last_user = next((c for r, c in reversed(recent) if r == "user"), None)
    if last_user:
        last_user = re.sub(r"\s+", " ", last_user).strip().rstrip(".")
        bits.append(f'and you asked: "{last_user}"')

    sentence = ", ".join(bits)
    return sentence[0].upper() + sentence[1:] + "."


def _is_identity_query(prompt: str) -> bool:
    return bool(re.search(r"\bwho am i\??$", prompt.strip(), flags=re.IGNORECASE))


def _is_summary_query(prompt: str) -> bool:
    return bool(re.search(r"\bwhat (did we|have we) (talked|talked about) so far|one line|summar(y|ise|ize)", prompt,
                          flags=re.IGNORECASE))


def _is_remember_name(prompt: str) -> bool:
    t = prompt.lower()
    return "remember my name" in t or bool(re.search(r"\bremember that my name is\b", t))


def _is_first_calc_query(prompt: str) -> bool:
    return bool(re.search(r"\b(first|1st)\s+calculation\b", prompt, flags=re.IGNORECASE))


def _find_first_numeric_answer(pairs: List[Tuple[str, str]]) -> str | None:
    # Scan chronologically for the first assistant "Final Answer: <number>"
    for role, content in pairs:
        if role != "assistant":
            continue
        m = re.search(r"Final Answer:\s*([-+]?\d+(?:\.\d+)?)\b", content)
        if m:
            return m.group(1)
    # fallback: any bare numeric-looking assistant line
    for role, content in pairs:
        if role != "assistant":
            continue
        m = re.search(r"\b([-+]?\d+(?:\.\d+)?)\b", content)
        if m:
            return m.group(1)
    return None


def run_react(prompt: str, session_id: str, max_steps: int = 10) -> str:
    # Build controller prompt with system prompt + memory + user
    base_limit = 6
    need_more = (
            _is_identity_query(prompt)
            or _is_first_calc_query(prompt)
            or _is_summary_query(prompt)
            or _is_goodbye_query(prompt)
    )
    history = load_context(session_id, limit=(20 if need_more else base_limit))
    memory_block = _format_memory(history)

    controller = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Conversation so far:\n{memory_block}\n\n"
        f"USER: {prompt}\n"
        f"Thought:"
    )
    intent = _classify_intent(prompt)
    # Shorten step budget unless multi-step is clearly requested
    step_limit = 10 if _wants_multi_step(prompt) else min(max_steps, 4)

    print("\n=== 🧠 ReAct Debug Start ===")
    print(f"USER PROMPT: {prompt}")
    print(f"SESSION: {session_id}")
    print(f"INTENT: {intent} | STEP_LIMIT: {step_limit}")
    print("============================")

    # === Pre-loop controller-side stability helpers ===
    # 1) Remember my name (no special tool → acknowledge and persist the turn)
    if _is_remember_name(prompt):
        name = _extract_name_from_prompt(prompt) or _find_name_in_history(history) or "you"
        final = f"Final Answer: Got it — I’ll remember your name: {name}."
        persist_turn(session_id, prompt, final)
        return final

    # 2) Identity query ("Who am I?")
    if _is_identity_query(prompt):
        name = _find_name_in_history(history)
        if name:
            final = f"Final Answer: You are {name}."
        else:
            final = "Final Answer: I don’t have your name yet — tell me “My name is …” and I’ll remember."
        persist_turn(session_id, prompt, final)
        return final

    # 3) Conversation summary request
    if _is_summary_query(prompt):
        summary = _summarize_one_line(history)
        final = f"Final Answer: {summary}"
        persist_turn(session_id, prompt, final)
        return final

    # 4) First calculation result
    if _is_first_calc_query(prompt):
        first_num = _find_first_numeric_answer(history)
        if first_num is not None:
            final = f"Final Answer: {first_num}"
        else:
            final = "Final Answer: I couldn't find a prior calculation in this session."
        persist_turn(session_id, prompt, final)
        return final

    last_result = None
    used_repair = False

    # Repeat-detection (same tool + identical args twice)
    last_action_key = None
    repeat_count = 0

    for step in range(1, step_limit + 1):
        print(f"\n--- Step {step} ---")
        model_out = (run_reasoning_model(controller) or "").strip()
        print(f"[Model out]\n{model_out}\n")

        # 1) Check for correct Final Answer string
        if model_out.startswith("Final Answer:"):
            final = model_out
            persist_turn(session_id, prompt, final)
            return final

        # 2) Try to parse a JSON tool call (repair common issues first)
        cleaned = _strip_noise(model_out)
        cleaned = _quote_bare_placeholders(cleaned)
        json_block = _extract_first_json(cleaned)

        if not json_block:
            # One retry hint to force JSON tool call
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

        # 3) Model sometimes emits a fake tool 'FINAL ANSWER'
        norm = resolve_tool(tool)
        if norm == "__final_answer__":
            # Some models return {"tool":"FINAL ANSWER","text":"..."} at top level (no args)
            top_text = None
            try:
                top_text = data.get("text")
            except Exception:
                pass
            text = top_text or (args or {}).get("text") or (str(last_result) if last_result is not None else "")
            final = f"Final Answer: {text}".strip()
            persist_turn(session_id, prompt, final)
            return final

        # 4) Replace placeholders using last observation
        args = _fill_placeholders(args, last_result)

        # 5) Greeting safety (prefer remembered name over "user")
        if norm == "greeting":
            if not isinstance(args, dict):
                args = {}
            name = args.get("name")
            if not name or str(name).lower() in {"?", "user", "you"}:
                remembered = _find_name_in_history(history)
                args["name"] = remembered or "User"

        # 6) Execute tool + handle errors
        result = run_tool(norm, args)
        print(f"🧰 Tool call: {norm}({args}) -> {result}")
        last_result = result

        # Repeat detection: if same action twice, finalize with last result
        action_key = (norm, json.dumps(args, sort_keys=True, ensure_ascii=False))
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

        # Unknown tool / tool_error handling (teach the model quickly)
        if isinstance(result, str) and result.startswith("[tool_error]"):
            # Try to produce a “did you mean … ?” hint
            m = re.search(r"Available:\s*(.+)$", result)
            if m:
                valid = [x.strip() for x in m.group(1).split(",") if x.strip()]
            else:
                valid = ["add_numbers", "multiply", "divide", "to_uppercase", "greeting"]
            hint_name = _closest_tool_hint(tool or "", valid)
            hint_text = (f" Did you mean '{hint_name}'?" if hint_name else "")
            controller += (
                f"\n{json_block}\nObservation: {result}{hint_text}\n"
                "Guidance: Correct your tool name/args and output exactly ONE JSON tool call.\nThought:"
            )
            continue

        # 7) Early-stop heuristics (prevent wandering)
        if intent == "greet" and norm == "greeting" and isinstance(result, str) and result:
            final = f"Final Answer: {result}"
            persist_turn(session_id, prompt, final)
            print("🛑 Auto-finalized: greeting satisfied.")
            return final

        if intent == "transform" and norm in {"to_uppercase"} and isinstance(result, str) and result:
            final = f"Final Answer: {result}"
            persist_turn(session_id, prompt, final)
            print("🛑 Auto-finalized: transform satisfied.")
            return final

        if intent == "math":
            # Single-step math: finalize on first numeric result
            if _is_number(result) and not _wants_multi_step(prompt):
                final = f"Final Answer: {result}"
                persist_turn(session_id, prompt, final)
                print("🛑 Auto-finalized: math satisfied (single-step).")
                return final
            # Multi-step phrase detected → finalize when "terminal" op is observed
            if _wants_multi_step(prompt) and _is_number(result):
                terminal = None
                p = prompt.lower()
                if "divide" in p or "/" in p:
                    terminal = "divide"
                elif "multiply" in p or "times" in p or "*" in p:
                    terminal = "multiply"
                elif "add" in p or "+" in p:
                    terminal = "add_numbers"
                if terminal and norm == terminal:
                    final = f"Final Answer: {result}"
                    persist_turn(session_id, prompt, final)
                    print(f"🛑 Auto-finalized: math satisfied (terminal op: {terminal}).")
                    return final

        # 8) Normal observation → continue loop (with gentle nudge)
        controller += (
            f"\n{json_block}\nObservation: {result}\n"
            "Guidance: If the user's request is satisfied, output 'Final Answer: <text>' now. "
            "Otherwise, output exactly ONE next JSON tool call.\nThought:"
        )

    persist_turn(session_id, prompt, "Reached max reasoning steps without final answer.")
    return "Reached max reasoning steps without final answer."
