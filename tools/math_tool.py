def add_numbers(a: float, b: float) -> float:
    return a + b

def divide(a: float, b: float) -> float | str:
    """Safe division. Returns a/b or an error string if b==0."""
    try:
        a = float(a)
        b = float(b)
    except Exception:
        return "[tool_error] divide expects numeric 'a' and 'b'"
    if b == 0.0:
        return "[tool_error] division by zero"
    return a / b

# (optional) simple aliases if the model tries variants
def divide_by(a: float, b: float) -> float | str:
    return divide(a, b)

def divide_by_int(a: float, b: float) -> float | str:
    # if you want integer semantics, uncomment:
    # try: return int(a) // int(b)
    # except Exception: return "[tool_error] divide_by_int expects integers"
    return divide(a, b)


def multiply(a: float, b: float) -> float:
    return a* b