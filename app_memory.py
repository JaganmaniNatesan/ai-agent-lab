import subprocess

import redis
from fastapi import FastAPI
from pydantic import BaseModel


api = FastAPI(title=" Local AI Agent API with memory")

conversation_history = []  # list of {role, content}

r = redis.Redis(host='localhost', port=6379, db=0)


class Prompt(BaseModel):
    prompt: str


def run_model(prompt: str):
    """Run local mistral via ollama"""
    cmd = ['ollama', 'run', 'mistral', prompt]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


@api.post('/ask')
def ask_agent(data: Prompt):
    global conversation_history

    conversation_history.append({"role": "assistant", "content": data.prompt})

    context = "\n".join(
        [f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation_history[-6:]]
    )

    context += "\nAssistant:"
    print(context)
    response_text = run_model(context)
    conversation_history.append({'role': 'assistant', 'content': response_text})
    return {
        "response": response_text,
        "memory_length": len(conversation_history)
    }


@api.get('/memory')
def get_memory():
    """View current chat history"""
    return conversation_history


@api.delete("/memory")
def clear_memory():
    """Reset memory"""
    conversation_history.clear()
    return {"message": "Memory cleared"}
