"""Centralized backend configuration; reads backend/.env without overriding OS env."""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / '.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False,
    )

    DB_USER: str = ''
    DB_PASSWORD: str = ''
    DB_HOST: str = '127.0.0.1'
    DB_PORT: int = 11522
    DB_SERVICE: str = ''
    VWORLD_API_KEY: str = ''
    VWORLD_DOMAIN: str = 'http://localhost:5173'
    CORS_ORIGINS: str = 'http://localhost:5500,http://localhost:5173'

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]

    def require_database(self) -> None:
        missing = [key for key in ('DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_SERVICE') if not getattr(self, key)]
        if missing:
            raise RuntimeError('Missing Oracle environment variables: ' + ', '.join(missing))


@lru_cache
def get_settings() -> Settings:
    return Settings()
