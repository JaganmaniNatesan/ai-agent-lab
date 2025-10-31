import sqlite3
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Tuple

# ✅ Always resolve paths relative to the project root (not cwd)
BASE_DIR = Path(__file__).resolve().parents[1]   # ai-agent-lab/
DB_DIR   = BASE_DIR / "storage"
DB_PATH  = DB_DIR / "chat_memory.db"

# DB Setup
def init_memory_db():
    """Create memory table if not exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # ✅ fixed
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT CHECK(role IN ('user','assistant')),
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# Save message
def save_message(session_id: str, role: str, content: str):
    """Insert a message into short-term memory."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO memory (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, role, content, datetime.now(UTC)),
        )
        conn.commit()

def get_recent_messages(session_id: str, limit: int = 5) -> List[Tuple[str, str]]:
    """Fetch the most recent N messages for a session."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            SELECT role, content FROM memory
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        )
        messages = cursor.fetchall()[::-1]  # reverse to chronological
    return messages

def clear_memory(session_id: str):
    """Remove all messages for a session."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM memory WHERE session_id = ?", (session_id,))
        conn.commit()

# Run table creation on import
init_memory_db()
