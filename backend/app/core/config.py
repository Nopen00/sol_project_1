# 프로젝트 환경설정 파일
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    DB_host: str = Field(alias="DB_HOST")
    DB_port: str = Field(alias="DB_PORT")
    DB_service: str = Field(alias="DB_SERVICE")
    DB_user: str = Field(alias="DB_USER")
    DB_password: str = Field(alias="DB_PASSWORD")

    yt_api: str = Field(alias="YOUTUBE_API_KEY")


settings = Settings()