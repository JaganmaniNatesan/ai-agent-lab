from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import json

app = FastAPI(title=' Local  AI agent API')


class Prompt(BaseModel):
    prompt: str


@app.post("/ask")
def ask_agent(data: Prompt):
    cmd = ["ollama", "run", "mistral", data.prompt]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    response_text = result.stdout.strip()
    return {"response": response_text}
