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

# 상세 조회 응답모델
class BoardDetailResponse(BoardResponse):
    content: str


class BoardUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)    