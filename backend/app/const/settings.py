from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LOCAL_DB_ENV_FILE = Path(__file__).resolve().parents[2] / "local_db.env"


class ApiSettings(BaseSettings):
    API_PATH: str = ""
    API_CORS_ORIGINS: str = ""
    LOG_LEVEL: str = "INFO"


class AuthSettings(BaseSettings):
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, gt=0)


class DatabaseSettings(BaseSettings):
    DB_TYPE: str = Field(..., min_length=1)
    DB_USER: str = Field(..., min_length=1)
    DB_PASSWORD: str = Field(..., min_length=1)
    DB_HOST: str = Field(..., min_length=1)
    DB_PORT: int = Field(..., gt=0)
    DB_NAME: str = Field(..., min_length=1)


class LocalDatabaseSettings(BaseSettings):
    DB_TYPE: str = Field(..., min_length=1)
    DB_NAME: str = Field(..., min_length=1)

    model_config = SettingsConfigDict(env_file=str(LOCAL_DB_ENV_FILE), env_file_encoding="utf-8")
