from fastapi import FastAPI
from pydantic import BaseModel

api = FastAPI(title='Testing Api ')

class Prompt(BaseModel):
    prompt: str

@api.get("/")
def read_root():
    return {"message" : "API server is live"}

@api.post("/agent")
def ask_agent(request: Prompt):
    return  {"response" : f"Thinking about... {request.prompt}"}



