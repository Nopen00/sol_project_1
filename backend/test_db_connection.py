
from sqlalchemy import text
from app.core.database import get_session


def test_connection():
    session = get_session()

    try:
        result = session.execute(
            text("SELECT USER FROM DUAL")
        )

        user = result.scalar_one()

        print("Oracle DB 연결 성공!")
        print("현재 접속 계정:", user)

    except Exception as e:
        print("Oracle DB 연결 실패")
        print("오류:", e)

    finally:
        session.close()


if __name__ == "__main__":
    test_connection()
