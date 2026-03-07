import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.observability import log_layer_event
from app.core.db.repository_base import BaseRepository
from app.core.errors.repositories import RepositoryError
from app.features.outbox.models import OutboxEvent
from app.features.outbox.schemas import OutboxEventRecord

logger = logging.getLogger("app.outbox")


class OutboxRepository(BaseRepository[OutboxEvent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, OutboxEvent, default_record_type=OutboxEventRecord)

    async def create_event(
        self,
        *,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, object],
        occurred_at: datetime | None = None,
    ) -> OutboxEventRecord:
        event_data = {
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "event_type": event_type,
            "payload": payload,
            "occurred_at": occurred_at,
        }
        outbox_event = await self.create(**event_data)
        log_layer_event(
            logger,
            layer="infrastructure",
            event="outbox_event_persisted",
            outbox_event_id=outbox_event.id,
            aggregate_type=outbox_event.aggregate_type,
            event_type=outbox_event.event_type,
        )
        return self._to_record(outbox_event)

    async def list_pending(self, *, limit: int = 100) -> list[OutboxEventRecord]:
        if limit < 1:
            raise RepositoryError("Limit must be greater than or equal to 1")

        query = (
            select(OutboxEvent)
            .where(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.occurred_at.asc(), OutboxEvent.id.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        outbox_events = list(result.scalars().all())
        return self._to_records(outbox_events)

    async def get_event(self, event_id: int) -> OutboxEventRecord | None:
        outbox_event = await self.get(event_id)
        if outbox_event is None:
            return None
        return self._to_record(outbox_event)

    async def mark_published(
        self,
        event: OutboxEventRecord,
        *,
        published_at: datetime | None = None,
    ) -> OutboxEventRecord:
        persisted_event = await self.get(event.id)
        if persisted_event is None:
            raise RepositoryError(f"Outbox event {event.id} not found")

        outbox_event = await self.update(
            persisted_event,
            published_at=published_at or datetime.now(UTC),
        )
        log_layer_event(
            logger,
            layer="infrastructure",
            event="outbox_event_marked_published",
            outbox_event_id=outbox_event.id,
        )
        return self._to_record(outbox_event)
