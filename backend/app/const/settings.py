from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class ApiSettings(BaseSettings):
    API_PATH: str = ""
    API_CORS_ORIGINS: str = ""
    LOG_LEVEL: str = "WARNING"


class AuthSettings(BaseSettings):
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, gt=0)


class DatabaseSettings(BaseSettings):
    DB_TYPE: str = "sqlite+aiosqlite"
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_NAME: str = "library.db"
