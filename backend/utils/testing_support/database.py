import contextlib
import os
import pathlib
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeMeta


class MockDatabase:
    SQLITE_ASYNC_DRIVER = "sqlite+aiosqlite"
    SQLITE_TMP_SUFFIXES = ("", "-shm", "-wal")

    def __init__(self, path: str, database_name: str = "test.db", echo: bool = False):
        self.sql_file = str(pathlib.Path(path) / database_name)
        test_database = self.sql_file.replace("\\", "/")
        test_database_url = URL.create(drivername=self.SQLITE_ASYNC_DRIVER, database=test_database)
        self.delete_sqlite()
        self.engine = create_async_engine(url=test_database_url, echo=echo)
        self.Session = async_sessionmaker(bind=self.engine, expire_on_commit=False)

    async def setup(self, base: DeclarativeMeta) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(base.metadata.create_all)

    async def load_rows(self, model: Any, data: list[dict[str, Any]]) -> None:
        async with self.Session() as session, session.begin():
            session.add_all([model(**row) for row in data])

    async def get_db_session(self) -> AsyncGenerator[AsyncSession]:
        async with self.Session() as session:
            yield session

    def delete_sqlite(self) -> None:
        for suffix in self.SQLITE_TMP_SUFFIXES:
            tmp_file = pathlib.Path(f"{self.sql_file}{suffix}")
            if tmp_file.exists():
                os.remove(tmp_file)

    async def close(self) -> None:
        await self.engine.dispose()
        self.delete_sqlite()

    def __del__(self) -> None:
        with contextlib.suppress(OSError):
            self.delete_sqlite()
