from pydantic_settings import BaseSettings


class ApiSettings(BaseSettings):
    API_PATH: str = ""
    API_CORS_ORIGINS: str = ""


class DatabaseSettings(BaseSettings):
    DB_TYPE: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = ""
    DB_PORT: int = 0
    DB_NAME: str = ""


class LocalDatabaseSettings(BaseSettings):
    DB_TYPE: str = ""
    DB_NAME: str = ""

    class Config:
        env_file = "local_db.env"
        env_file_encoding = "utf-8"
