from fastapi import APIRouter ,HTTPException,status
from app.schemas.board import BoardResponse,BoardCreate,BoardDetailResponse,BoardUpdate
from app.services.board import list_boards ,create_board,get_board_by_id,update_board,delete_board

router = APIRouter()

# 1. 게시글 목록 조회 
@router.get("/boards", response_model=list[BoardResponse])
def get_boards():
    return list_boards()

# 2. 게시글 작성 
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
# 3. 게시글 상세 조회
@router.get(
    "/boards/{board_id}",
    response_model=BoardDetailResponse
)
def get_board_detail(board_id: int):
    board = get_board_by_id(board_id)

    if board is None:
        raise HTTPException(
            status_code=404,
            detail="게시글을 찾을 수 없습니다."
        )

    return board    

# 4. 게시글 수정
@router.put("/boards/{board_id}")
def put_board(board_id: int, data: BoardUpdate):
    result = update_board(
        board_id=board_id,
        title=data.title,
        content=data.content,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="게시글을 찾을 수 없습니다.",
        )

    return result

# 5. 게시글 삭제
@router.delete("/boards/{board_id}")
def remove_board(board_id: int):
    result = delete_board(board_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="게시글을 찾을 수 없습니다."
        )

    return result
