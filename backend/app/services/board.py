from sqlalchemy import text
from app.core.database import get_session


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