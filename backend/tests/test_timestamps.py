from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime
from sqlalchemy.dialects import postgresql

from app.models.author import Author
from app.models.book import Book
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


class _ModelWithTable(Protocol):
    __table__: Any


def _timestamp_columns(model: type[_ModelWithTable]) -> tuple[Any, Any]:
    table: Any = model.__table__
    return table.c.created_at, table.c.updated_at


def test_timestamp_columns_are_timezone_aware_with_defaults() -> None:
    for model in (Author, Book, User, Role, Permission):
        created_at, updated_at = _timestamp_columns(model)

        assert isinstance(created_at.type, DateTime)
        assert created_at.type.timezone is True
        assert isinstance(updated_at.type, DateTime)
        assert updated_at.type.timezone is True

        assert "TIMESTAMP WITH TIME ZONE" in created_at.type.compile(dialect=postgresql.dialect()).upper()
        assert "TIMESTAMP WITH TIME ZONE" in updated_at.type.compile(dialect=postgresql.dialect()).upper()

        assert created_at.server_default is not None
        assert updated_at.server_default is not None
        assert updated_at.onupdate is not None


class _TimestampPayload(BaseModel):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


def test_timestamp_serialization_keeps_utc_offset() -> None:
    timestamp = datetime(2026, 2, 25, 10, 0, 0, tzinfo=UTC)
    author = Author(name="Test Author", created_at=timestamp, updated_at=timestamp)

    payload = _TimestampPayload.model_validate(author).model_dump(mode="json")

    created_at = datetime.fromisoformat(payload["created_at"].replace("Z", "+00:00"))
    updated_at = datetime.fromisoformat(payload["updated_at"].replace("Z", "+00:00"))

    assert created_at.tzinfo is not None
    assert updated_at.tzinfo is not None
    assert created_at.utcoffset() == timedelta(0)
    assert updated_at.utcoffset() == timedelta(0)
