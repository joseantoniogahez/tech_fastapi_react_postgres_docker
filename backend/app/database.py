from pydantic import ValidationError
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.const.settings import LOCAL_DB_ENV_FILE, DatabaseSettings, LocalDatabaseSettings


class CustomDatabaseException(Exception):
    pass


def _build_postgres_url(db_settings: DatabaseSettings) -> URL:
    return URL.create(
        drivername=db_settings.DB_TYPE,
        username=db_settings.DB_USER,
        password=db_settings.DB_PASSWORD,
        host=db_settings.DB_HOST,
        port=db_settings.DB_PORT,
        database=db_settings.DB_NAME,
    )


def _build_sqlite_url(local_settings: LocalDatabaseSettings) -> URL:
    return URL.create(drivername=local_settings.DB_TYPE, database=local_settings.DB_NAME)


def build_database_url() -> URL:
    try:
        return _build_postgres_url(DatabaseSettings())
    except ValidationError:
        try:
            return _build_sqlite_url(LocalDatabaseSettings())
        except ValidationError as exc:
            raise CustomDatabaseException(f"Could not load local DB settings from file {LOCAL_DB_ENV_FILE}") from exc


def build_engine(database_url: URL) -> AsyncEngine:
    return create_async_engine(url=database_url)


DATABASE_URL = build_database_url()
engine = build_engine(DATABASE_URL)

AsyncSessionDatabase = async_sessionmaker(bind=engine)

Base = declarative_base()
