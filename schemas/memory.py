# schemas/memory.py
from pydantic import BaseModel, Field

class MemorySaveRequest(BaseModel):
    session_id: str = Field(..., description="Unique session ID", examples=["session_123"])
    role: str = Field(..., pattern="^(user|assistant)$", description="Message role", examples=["user"])
    content: str = Field(..., description="Message text content", examples=["Hello, how are you?"])

class MemoryQueryRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to query", examples=["session_123"])
    limit: int = Field(default=5, description="Number of messages to retrieve", examples=[5])
