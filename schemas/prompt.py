# schemas/prompt.py
from pydantic import BaseModel, Field

class Prompt(BaseModel):
    prompt: str = Field(..., description="User's request")
    session_id: str = Field(..., description="Conversation/session id", examples=["sess_123"])
