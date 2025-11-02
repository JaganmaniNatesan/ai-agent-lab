# agent/memory_adaptor.py
from typing import List, Tuple
from memory.short_memory import get_recent_messages, save_message

def load_context(session_id: str, limit: int = 6) -> List[Tuple[str, str]]:
    """
    Returns last N messages as (role, content), chronological order.
    """
    return get_recent_messages(session_id, limit=limit)

def persist_turn(session_id: str, user_text: str, assistant_text: str) -> None:
    """
    Save both sides of the conversation turn.
    """
    save_message(session_id, "user", user_text)
    save_message(session_id, "assistant", assistant_text)