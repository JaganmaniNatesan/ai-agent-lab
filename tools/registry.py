from typing import Callable
from tools.math_tool import add_numbers
from tools.text_tool import to_upper_case

TOOLS_REGISTRY: dict[str, Callable] = {
    "add_numbers" : add_numbers,
    "to_upper_case" : to_upper_case,
}

def run_tool(tool_name: str, args: dict):
    if tool_name not in TOOLS_REGISTRY:
        return f"{tool_name} not in tools registry"

    try:
        return TOOLS_REGISTRY[tool_name](**args)
    except Exception as e:
        return f"tool exception {e}"


