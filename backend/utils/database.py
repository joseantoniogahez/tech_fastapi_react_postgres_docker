import os
import pathlib
from typing import Any, AsyncGenerator, Dict, List

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeMeta

from app.database import database_manager


class MockDatabase:
    def __init__(self, path: str, echo: bool = False):
        default_database_url = database_manager.build_database_url()
        self.sql_file = str(pathlib.Path(path) / str(default_database_url.database))
        test_database = self.sql_file.replace("\\", "/")
        test_database_url = URL.create(drivername=default_database_url.drivername, database=test_database)
        self.delete_sqlite()
        self.engine = create_async_engine(url=test_database_url, echo=echo)
        self.Session = async_sessionmaker(bind=self.engine, expire_on_commit=False)

    async def setup(self, Base: DeclarativeMeta) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def load_rows(self, Model: Any, data: List[Dict[str, Any]]) -> None:
        async with self.Session() as session:
            async with session.begin():
                session.add_all([Model(**row) for row in data])

    async def get_db_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.Session() as session:
            yield session

    def delete_sqlite(self) -> None:
        if pathlib.Path(self.sql_file).exists():
            os.remove(self.sql_file)

    async def close(self) -> None:
        await self.engine.dispose()

    def __del__(self) -> None:
        self.delete_sqlite()
