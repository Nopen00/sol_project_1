from fastapi import APIRouter, HTTPException, status

from app.schemas.user import UserSignup, UserSignupResponse
from app.services.auth import signup_user


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