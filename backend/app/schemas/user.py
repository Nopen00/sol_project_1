from pydantic import BaseModel, Field


class UserSignup(BaseModel):
    username: str = Field(min_length=4, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class UserSignupResponse(BaseModel):
    user_id: int
    username: str
    message: str