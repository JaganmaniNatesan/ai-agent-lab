def to_uppercase(text: str) -> str:
    return text.upper()


def greeting(name: str) -> str:
    return f"Hello {name}"


from num2words import num2words  # add to requirements if you choose this


def number_to_words_upper(n):
    try:
        w = num2words(float(n)).replace("-", " ")
        return w.upper()
    except Exception as e:
        return f"[tool_error] Bad args for 'number_to_words_upper': {e}"
