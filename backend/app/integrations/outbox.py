from typing import Protocol

from app.features.outbox.schemas import OutboxEventRecord


class OutboxPersistencePort(Protocol):
    async def create_event(
        self,
        *,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, object],
    ) -> OutboxEventRecord: ...

    async def list_pending(self, *, limit: int = 100) -> list[OutboxEventRecord]: ...

    async def get_event(self, event_id: int) -> OutboxEventRecord | None: ...

    async def mark_published(self, event: OutboxEventRecord) -> OutboxEventRecord: ...
