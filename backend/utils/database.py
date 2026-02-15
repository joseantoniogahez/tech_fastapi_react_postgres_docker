import os
import pathlib
from typing import Any, AsyncGenerator, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeMeta

SQLITE_DATABASE_URL = "sqlite+aiosqlite:///{db_path}"


class MockDatabase:
    def __init__(self, db_name: str, path: str):
        self.sql_file = str(pathlib.Path(path) / db_name)
        self.delete_sqlite()
        database_url = SQLITE_DATABASE_URL.format(db_path=self.sql_file.replace("\\", "/"))
        self.engine = create_async_engine(database_url, echo=True)
        self.Session = async_sessionmaker(bind=self.engine)

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
