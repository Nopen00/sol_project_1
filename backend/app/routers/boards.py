from fastapi import APIRouter ,HTTPException,status
from app.schemas.board import BoardResponse,BoardCreate
from app.services.board import list_boards ,create_board

router = APIRouter()


@router.get("/boards", response_model=list[BoardResponse])
def get_boards():
    return list_boards()


@router.post(
    "/boards",
    status_code=status.HTTP_201_CREATED
)
def post_board(data: BoardCreate):
    try:
        return create_board(
            user_id=data.user_id,
            title=data.title,
            content=data.content
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )