from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from pwdlib import PasswordHash

from app.core.database import get_session


password_hash = PasswordHash.recommended()


def signup_user(username: str, password: str):
    session = get_session()

    try:
        # 아이디 중복 확인
        existing_user = session.execute(
            text("""
                SELECT USER_ID
                FROM USERS
                WHERE USERNAME = :username
            """),
            {"username": username}
        ).first()

        if existing_user is not None:
            raise ValueError("이미 사용 중인 아이디입니다.")

        # 비밀번호 해싱
        hashed_password = password_hash.hash(password)

        # 회원 정보 저장
        session.execute(
            text("""
                INSERT INTO USERS (
                    USERNAME,
                    PASSWORD_HASH
                )
                VALUES (
                    :username,
                    :password_hash
                )
            """),
            {
                "username": username,
                "password_hash": hashed_password,
            }
        )

        session.commit()

        # 생성된 사용자 조회
        user = session.execute(
            text("""
                SELECT USER_ID, USERNAME
                FROM USERS
                WHERE USERNAME = :username
            """),
            {"username": username}
        ).mappings().first()

        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "message": "회원가입이 완료되었습니다."
        }

    except IntegrityError:
        session.rollback()
        raise ValueError("이미 사용 중인 아이디입니다.")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()