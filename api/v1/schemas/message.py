from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageRequest(BaseModel):
    user_id: int
    session_id: Optional[int] = None
    message: str


class AIResponse(BaseModel):
    ai_response: str
    session_id: Optional[int]


class MessageHistory(BaseModel):
    message_id: int
    session_id: int
    sender: str
    message_text: str
    created_at: datetime