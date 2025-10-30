import subprocess


def run_local_model(prompt: str) -> str:
    """Calls a local Ollama model and returns its response text."""
    system_prompt = (
        "You are a tool-calling assistant. "
        "If the user asks to perform a task, respond ONLY in JSON with keys "
        "'tool' and 'args'. Do not add explanations or code blocks."
    )
    cmd = ["ollama", "run", "llama3.1", f"{system_prompt}\nUser: {prompt}"]
    try:
        result = subprocess.run(cmd,
                                text=True,
                                check=True,
                                capture_output=True
                                )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"[error] model call failed: {e.stderr.strip()}"


def run_tool_request(model_output: str) -> str:
    """
    Detect and execute tool-call JSON blocks even if wrapped in code fences or text.
    """
    import json, re
    from tools.registry import run_tool

    # 1️⃣ remove markdown code fences such as ```json ... ```
    cleaned = re.sub(r"```(?:json)?", "", model_output, flags=re.IGNORECASE).strip()

    # 2️⃣ extract just the JSON substring if embedded in text
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(0)

    # 3️⃣ attempt to parse the cleaned string
    try:
        data = json.loads(cleaned)
        tool = data.get("tool")
        args = data.get("args", {})

        # handle both list and dict args for flexibility
        if isinstance(args, list):
            args = {"text": args[0]} if len(args) == 1 else {"a": args[0], "b": args[1]}

        result = run_tool(tool, args)
        return f"Tools result : {result}"

    except json.JSONDecodeError:
        return model_output
