from pydantic import BaseModel
from datetime import datetime


class UserCreate(BaseModel):
    username: str


class UserResponse(BaseModel):
    user_id: int
    username: str
    created_at: datetime