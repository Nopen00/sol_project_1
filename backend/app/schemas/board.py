from datetime import datetime
from pydantic import BaseModel ,Field


class BoardResponse(BaseModel):
    board_id: int
    user_id: int
    title: str
    view_count: int
    created_at: datetime | None


class BoardCreate(BaseModel):
    user_id: int
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)    