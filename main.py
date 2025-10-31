from fastapi import FastAPI

from models.llm import run_local_model, run_tool_request
from models.stream_llm import stream_local_model
from schemas.prompt import Prompt
from agent.react_agent import run_react
from memory.short_memory import save_message, get_recent_messages, clear_memory
from schemas.memory import MemorySaveRequest , MemoryQueryRequest

api = FastAPI(title="Local AI Agent")




@api.get("/")
def read_root():
    return "API Server is live"


@api.post("/ask")
def ask_agent(request: Prompt):
    reply = run_local_model(request.prompt)
    return {"response": run_tool_request(reply)}


@api.post("/ask/stream")
def ask_stream_agent(requests: Prompt):
    return stream_local_model(requests.prompt)

@api.post("/agent/react")
def ask_agent_react(request: Prompt):
    result = run_react(request.prompt)
    return {"response", result}

# 🧠 Save message
@api.post("/memory/save")
def save_to_memory(req: MemorySaveRequest):
    save_message(req.session_id, req.role, req.content)
    return {"status": "saved"}

# 🧠 Get recent messages
@api.post("/memory/recent")
def get_recent(req: MemoryQueryRequest):
    messages = get_recent_messages(req.session_id, req.limit)
    return {"messages": [{"role": r, "content": c} for r, c in messages]}

# 🧹 Clear memory
@api.delete("/memory/clear/{session_id}")
def clear_session(session_id: str):
    clear_memory(session_id)
    return {"status": f"memory cleared for session {session_id}"}