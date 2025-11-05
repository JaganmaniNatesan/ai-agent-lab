# tools/registry.py
from tools import math_tool, text_tool
from tools.knowledge_tool import knowledge_search

TOOLS = {
    "add_numbers": math_tool.add_numbers,
    "multiply": math_tool.multiply,
    "divide": math_tool.divide,
    "to_uppercase": text_tool.to_uppercase,
    "greeting": text_tool.greeting,
    # optional:
    "number_to_words_upper": text_tool.number_to_words_upper,
    "knowledge_search": knowledge_search,
}

ALIASES = {
    # case/format variants the model sometimes tries
    "Greeting": "greeting",
    "TO_UPPERCASE": "to_uppercase",
    "Divide": "divide",
    "divide_by": "divide",
    "divide_by_int": "divide",

    # hallucination — not a real tool, we convert this in controller
    "FINAL ANSWER": "__final_answer__",
    "FINAL_ANSWER": "__final_answer__",
}


def resolve_tool(name: str) -> str:
    if not name: return ""
    if name in ALIASES: return ALIASES[name]
    lname = name.lower()
    if lname in TOOLS: return lname
    return ALIASES.get(lname, lname)


def run_tool(name: str, args: dict):
    norm = resolve_tool(name)
    if norm == "__final_answer__":
        return "[tool_error] 'FINAL ANSWER' is not a callable tool"
    func = TOOLS.get(norm)
    if not func:
        return f"[tool_error] Unknown tool '{name}'. Available: {', '.join(sorted(TOOLS.keys()))}"
    try:
        return func(**args)
    except TypeError as e:
        return f"[tool_error] Bad args for '{name}': {e}"
    except Exception as e:
        return f"[tool_error] {name} failed: {e}"
