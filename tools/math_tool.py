def add_numbers(a, b):
    try:
        return float(a) + float(b)
    except Exception as e:
        return f"[tool_error] Bad args for 'add_numbers': {e}"


def multiply(a, b):
    try:
        return float(a) * float(b)
    except Exception as e:
        return f"[tool_error] Bad args for 'multiply': {e}"


def divide(a, b):
    try:
        bf = float(b)
        if bf == 0:
            return "[tool_error] divide by zero"
        return float(a) / bf
    except Exception as e:
        return f"[tool_error] Bad args for 'divide': {e}"


# (optional) simple aliases if the model tries variants
def divide_by(a: float, b: float) -> float | str:
    return divide(a, b)


def divide_by_int(a: float, b: float) -> float | str:
    # if you want integer semantics, uncomment:
    # try: return int(a) // int(b)
    # except Exception: return "[tool_error] divide_by_int expects integers"
    return divide(a, b)
