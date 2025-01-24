from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.const.settings import DatabaseSettings

try:
    vars = DatabaseSettings()
    DATABASE_URL = f"{vars.DB_TYPE}://{vars.DB_USER}:{vars.DB_PASSWORD}@{vars.DB_HOST}:{vars.DB_PORT}/{vars.DB_NAME}"
except ValidationError:
    from app.const.settings import LocalDatabaseSettings

    local_vars = LocalDatabaseSettings()
    DATABASE_URL = f"{local_vars.DB_TYPE}:///{local_vars.DB_NAME}"


engine = create_async_engine(url=DATABASE_URL)

AsyncSessionDatabase = async_sessionmaker(bind=engine)

Base = declarative_base()
