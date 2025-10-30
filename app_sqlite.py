import subprocess

import redis
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from db import SessionLocal, Message, init_db

api = FastAPI(title=' Local AI Agent using Sqlite Memory')
r = redis.Redis(host='localhost', port=6379, db=0)
init_db()

conversation_history = []


class Prompt(BaseModel):
    prompt: str
    session_id: str


def run_model(prompt: str):
    """Run local mistral via ollama"""
    cmd = ['ollama', 'run', 'mistral', prompt]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def save_messages(session_id, role, content):
    """Store each message in sqlite"""
    db = SessionLocal()
    msg = Message(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.close()


def load_history(session_id, limit=6):
    """Load last n message for Context"""
    db = SessionLocal()
    msgs = (db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.id.desc())
            .limit(limit)
            .all())
    db.close()
    return [{"role": m.role, "content": m.content} for m in reversed(msgs)]


@api.post("/ask")
def ask_agent(data: Prompt):
    # Step1: Save prompt in data store
    save_messages(data.session_id, "user", data.prompt)

    # Step 2: Retrieve last few messages for context
    history = load_history(data.session_id)

    context = "\n".join(
        [f"{msg['role'].capitalize()}: {msg['content']}" for msg in history]
    ) + "\nAssistant:"
    # Step 3: Run model
    response_text = run_model(context)

    # Step 4: Save assistant response
    save_messages(data.session_id, "assistant", response_text)

    return {
        "response": response_text,
        "memory_length": len(history)
    }


@api.get('/memory/{session_id}')
def get_memory(session_id: str):
    """View stored chat for a session"""
    return load_history(session_id, limit=50)


@api.delete('/memory/{session_id}')
def clear_memory(session_id: str):
    """Clear chat history for a specific user"""
    db = SessionLocal()
    db.query(Message).filter(Message.session_id == session_id).delete()
    db.commit()
    db.close()
    return {"message": f"Memory cleared for session {session_id}"}


if __name__ == "__main__":
    uvicorn.run("app_sqlite:api", host="127.0.0.1", port=8000, reload=True)
