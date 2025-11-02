# agent/react_agent.py
import json
import re
import difflib
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

# --- Pre-loop helper logic for "remember/identity/summary" ---
def _extract_name_from_prompt(text: str) -> str | None:
    t = text.strip()
    m = re.search(r"\bmy name is\s+([A-Za-z][A-Za-z .'-]{0,40})\b", t, flags=re.IGNORECASE)
    return m.group(1).strip() if m else None

def _find_name_in_history(pairs: List[Tuple[str, str]]) -> str | None:
    # look for "My name is ..." from user or a greeting like "Hello Jagan"
    for role, content in reversed(pairs):
        if role == "user":
            n = _extract_name_from_prompt(content)
            if n:
                return n
        if role == "assistant":
            m = re.search(r"\bHello\s+([A-Za-z][A-Za-z .'-]{0,40})\b", content, flags=re.IGNORECASE)
            if m:
                return m.group(1).strip()
    return None

def _summarize_one_line(pairs: List[Tuple[str, str]]) -> str:
    # crude one-liner from last 6 turns
    bullets = []
    for role, content in pairs[-6:]:
        c = content.replace("\n", " ").strip()
        if role == "user":
            bullets.append(f"user: {c}")
        else:
            bullets.append(f"assistant: {c[:60]}{'…' if len(c)>60 else ''}")
    line = "; ".join(bullets)
    return line[:220] + ("…" if len(line) > 220 else "")

def _is_identity_query(text: str) -> bool:
    return bool(re.search(r"\bwho am i\??$", text.strip(), flags=re.IGNORECASE))

def _is_summary_query(text: str) -> bool:
    return bool(re.search(r"\bwhat (did we|have we) (talked|talked about) so far|one line|summar(y|ise|ize)", text, flags=re.IGNORECASE))

def _is_remember_name(text: str) -> bool:
    t = text.lower()
    return "remember my name" in t or bool(re.search(r"\bremember that my name is\b", t))

def run_react(prompt: str, session_id: str, max_steps: int = 10) -> str:
    # Build controller prompt with system prompt + memory + user
    history = load_context(session_id, limit=6)
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

        # 5) Greeting safety (name may be "", null, or "?")
        if norm == "greeting":
            if not isinstance(args, dict):
                args = {}
            if not args.get("name"):
                args["name"] = "User"

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