from sqlalchemy import text
from app.core.database import get_session

# 전체 게시글 목록 (select 로 조회)
def list_boards():
    session = get_session()

    try:
        result = session.execute(
            text("""
                SELECT
                    BOARD_ID,
                    USER_ID,
                    TITLE,
                    VIEW_COUNT,
                    CREATED_AT
                FROM BOARDS
                ORDER BY BOARD_ID DESC
            """)
        )

        return [
            dict(row)
            for row in result.mappings()
        ]

    finally:
        session.close()

# 게시글 작성 (userid 조회, insert)
def create_board(user_id: int, title: str, content: str):

    session = get_session()

    try:
        user = session.execute(
            text("""
                SELECT USER_ID
                FROM USERS
                WHERE USER_ID = :user_id
            """),
            {"user_id": user_id}
        ).first()

        if user is None:
            raise ValueError("존재하지 않는 사용자입니다.")

        session.execute(
            text("""
                INSERT INTO BOARDS (
                    USER_ID,
                    TITLE,
                    CONTENT
                )
                VALUES (
                    :user_id,
                    :title,
                    :content
                )
            """),
            {
                "user_id": user_id,
                "title": title,
                "content": content
            }
        )

        session.commit()

        return {"message": "게시글이 등록되었습니다."}

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()    


# 특정 게시글 상세조회 (board_id 조회)
def get_board_by_id(board_id: int):
    session = get_session()

    try:
        result = session.execute(
            text("""
                SELECT
                    BOARD_ID,
                    USER_ID,
                    TITLE,
                    CONTENT,
                    VIEW_COUNT,
                    CREATED_AT
                FROM BOARDS
                WHERE BOARD_ID = :board_id
            """),
            {"board_id": board_id}
        ).mappings().first()

        if result is None:
            return None

        board = dict(result)

        # Oracle CLOB 데이터를 문자열로 변환
        content = board["content"]
        if hasattr(content, "read"):
            board["content"] = content.read()

        return board

    finally:
        session.close()

# 게시글 수정 (board_id 조회, update)
def update_board(board_id: int, title: str, content: str):
    session = get_session()

    try:
        result = session.execute(
            text("""
                UPDATE BOARDS
                SET
                    TITLE = :title,
                    CONTENT = :content,
                    UPDATED_AT = CURRENT_TIMESTAMP
                WHERE BOARD_ID = :board_id
            """),
            {
                "board_id": board_id,
                "title": title,
                "content": content,
            },
        )

        if result.rowcount == 0:
            session.rollback()
            return None

        session.commit()

        return {
            "board_id": board_id,
            "message": "게시글이 수정되었습니다.",
        }

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()        

# 게시글 삭제
def delete_board(board_id: int):
    session = get_session()

    try:
        # 1. 삭제할 게시글이 존재하는지 확인
        board = session.execute(
            text("""
                SELECT BOARD_ID
                FROM BOARDS
                WHERE BOARD_ID = :board_id
            """),
            {"board_id": board_id}
        ).first()

        if board is None:
            return None

        # 2. 게시글에 연결된 댓글 먼저 삭제
        session.execute(
            text("""
                DELETE FROM COMMENTS
                WHERE BOARD_ID = :board_id
            """),
            {"board_id": board_id}
        )

        # 3. 게시글 삭제
        session.execute(
            text("""
                DELETE FROM BOARDS
                WHERE BOARD_ID = :board_id
            """),
            {"board_id": board_id}
        )

        # 4. 변경 사항 저장
        session.commit()

        return {
            "board_id": board_id,
            "message": "게시글이 삭제되었습니다."
        }

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()