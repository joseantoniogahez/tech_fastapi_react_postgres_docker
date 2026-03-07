from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import BaseModel


class OutboxEvent(BaseModel):
    __tablename__ = "outbox_events"
    __table_args__ = (Index("ix_outbox_events_published_at_id", "published_at", "id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aggregate_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(150), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
