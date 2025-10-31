from typing import List, Tuple
from memory.short_memory import save_message, get_recent_messages


def load_context(session_id: str, limit=6) -> List[Tuple[str, str]]:
    """Return [(role, content),....] in chronological order."""
    return get_recent_messages(session_id, limit)


def persist_turn(session_id: str, user_text: str, final_text: str) -> None:
    """Persist the user input and the model final output.   """
    save_message(session_id, "user", user_text)
    save_message(session_id, "assistant", final_text)
