"""Shared SQLAlchemy engine and session factory for Oracle."""
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

_engine = None
_Session = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        settings.require_database()
        url = URL.create(
            'oracle+oracledb',
            username=settings.DB_USER,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            query={'service_name': settings.DB_SERVICE},
        )
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine


def get_session():
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _Session()
