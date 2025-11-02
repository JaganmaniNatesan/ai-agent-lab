# models/reason_llm.py
import os
import re
import subprocess

# Switch models via env var; llama3.1 is most obedient for JSON/tools.
MODEL_NAME = os.environ.get("AGENT_MODEL", "llama3.1:latest")

def _extract_first_json_block(text: str) -> str | None:
    """Return the first balanced {...} object or None."""
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
                return text[start:i+1]
    return None

def run_reasoning_model(prompt: str) -> str:
    print(f"\n[LLM model] {MODEL_NAME}")
    cmd = ["ollama", "run", MODEL_NAME, prompt]

    res = subprocess.run(cmd, text=True, capture_output=True)
    if res.returncode != 0:
        print("[LLM STDERR]\n", res.stderr)
        return ""

    out = (res.stdout or "").strip()
    # Trim common noise early (controller also handles this).
    out_clean = re.sub(r"```json\s*|\s*```", "", out, flags=re.IGNORECASE).strip()
    out_clean = re.sub(r"^\s*TOOL\s+CALL\s*:?\s*", "", out_clean, flags=re.IGNORECASE).strip()

    # If there's JSON, return just the JSON; else return the text (e.g., Final Answer: ...).
    block = _extract_first_json_block(out_clean)
    return block if block else out_clean