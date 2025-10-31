import subprocess

def run_reasoning_model_old(prompt: str) -> str:
    """
    ReAct-style reasoning model: it can either call a tool (JSON)
    or give a final answer when done.
    """
    system_prompt = (
        "You are an intelligent ReAct agent. "
        "You can reason, decide when to use tools, and when you have the final answer. "
        "At each turn, respond with EXACTLY ONE of the following formats:\n"
        "1. A JSON object: {\"tool\": \"<tool_name>\", \"args\": {...}}\n"
        "2. A line beginning with: Final Answer: <your concise answer>\n\n"
        "Rules:\n"
        "- NEVER include code blocks or ``` markers.\n"
        "- If you already have enough information, end with 'Final Answer: ...'."
    )

    cmd = ["ollama", "run", "mistral", f"{system_prompt}\nUser: {prompt}"]
    try:
        result = subprocess.run(
            cmd, text=True, check=True, capture_output=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"[error] model call failed: {e.stderr.strip()}"


def run_reasoning_model(prompt: str) -> str:
    import subprocess
    print(f"\n[LLM call] prompt start >>>\n{prompt[:500]}\n<<< end prompt")
    cmd = ["ollama", "run", "mistral", prompt]
    result = subprocess.run(cmd, text=True, capture_output=True)
    print(f"[LLM raw output]\n{result.stdout.strip()}\n")
    return result.stdout.strip()
