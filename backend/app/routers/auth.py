from fastapi import APIRouter, HTTPException, status

from app.schemas.user import UserSignup, UserSignupResponse,TokenResponse,UserLogin
from app.services.auth import signup_user,login_user


router = APIRouter()


@router.post(
    "/auth/signup",
    response_model=UserSignupResponse,
    status_code=status.HTTP_201_CREATED
)
def signup(data: UserSignup):
    try:
        return signup_user(
            username=data.username,
            password=data.password
        )

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        )

@router.post(
    "/auth/login",
    response_model=TokenResponse
)
def login(data: UserLogin):
    result = login_user(
        username=data.username,
        password=data.password
    )

    if result is None:
        raise HTTPException(
            status_code=401,
            detail="아이디 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result    