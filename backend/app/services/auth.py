from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from pwdlib import PasswordHash

from app.core.database import get_session

from dotenv import load_dotenv
import os
from datetime import datetime,timedelta,timezone

import jwt
from sqlalchemy import text

load_dotenv()

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


def create_access_token(user_id: int):
    secret_key = os.environ.get("JWT_SECRET_KEY")

    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY가 설정되지 않았습니다.")

    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")

    expire_minutes = int(
        os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm=algorithm,
    )


def login_user(username: str, password: str):
    session = get_session()

    try:
        user = session.execute(
            text("""
                SELECT
                    USER_ID,
                    USERNAME,
                    PASSWORD_HASH
                FROM USERS
                WHERE USERNAME = :username
            """),
            {"username": username}
        ).mappings().first()

        if user is None:
            return None

        stored_hash = user["password_hash"]

        # 기존 테스트용 dummy_hash_only 등은
        # 실제 Argon2 해시가 아니므로 인증하지 않음
        if not stored_hash or not stored_hash.startswith("$argon2"):
            return None

        if not password_hash.verify(password, stored_hash):
            return None

        token = create_access_token(user["user_id"])

        return {
            "access_token": token,
            "token_type": "bearer",
        }

    finally:
        session.close()        