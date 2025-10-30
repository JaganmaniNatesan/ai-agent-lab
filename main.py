from fastapi import FastAPI

from models.llm import run_local_model, run_tool_request
from models.stream_llm import stream_local_model
from schemas.prompt import Prompt
from agent.react_agent import run_react

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

