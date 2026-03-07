import logging
from typing import Protocol

from app.core.common.observability import log_layer_event
from app.core.db.ports import UnitOfWorkPort
from app.features.outbox.schemas import EnqueueOutboxEventCommand, OutboxEventResult
from app.integrations.outbox import OutboxPersistencePort

logger = logging.getLogger("app.outbox")

OutboxRepositoryPort = OutboxPersistencePort


class OutboxServicePort(Protocol):
    async def enqueue(self, event: EnqueueOutboxEventCommand) -> OutboxEventResult: ...

    async def list_pending(self, *, limit: int = 100) -> list[OutboxEventResult]: ...

    async def mark_published(self, event_id: int) -> OutboxEventResult | None: ...


class OutboxService:
    def __init__(
        self,
        outbox_repository: OutboxRepositoryPort,
        unit_of_work: UnitOfWorkPort,
    ):
        self.outbox_repository = outbox_repository
        self.unit_of_work = unit_of_work

    async def enqueue(self, event: EnqueueOutboxEventCommand) -> OutboxEventResult:
        async with self.unit_of_work:
            outbox_event = await self.outbox_repository.create_event(
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                event_type=event.event_type,
                payload=event.payload,
            )
        log_layer_event(
            logger,
            layer="integration",
            event="outbox_event_enqueued",
            outbox_event_id=outbox_event.id,
            aggregate_type=outbox_event.aggregate_type,
            event_type=outbox_event.event_type,
        )
        return OutboxEventResult.from_domain(outbox_event)

    async def list_pending(self, *, limit: int = 100) -> list[OutboxEventResult]:
        outbox_events = await self.outbox_repository.list_pending(limit=limit)
        log_layer_event(
            logger,
            layer="integration",
            event="outbox_pending_listed",
            pending_count=len(outbox_events),
            limit=limit,
        )
        return OutboxEventResult.from_domain_list(outbox_events)

    async def mark_published(self, event_id: int) -> OutboxEventResult | None:
        async with self.unit_of_work:
            outbox_event = await self.outbox_repository.get_event(event_id)
            if outbox_event is None:
                log_layer_event(
                    logger,
                    layer="integration",
                    event="outbox_publish_mark_missing",
                    outbox_event_id=event_id,
                )
                return None
            outbox_event = await self.outbox_repository.mark_published(outbox_event)
        log_layer_event(
            logger,
            layer="integration",
            event="outbox_publish_marked",
            outbox_event_id=outbox_event.id,
        )
        return OutboxEventResult.from_domain(outbox_event)
