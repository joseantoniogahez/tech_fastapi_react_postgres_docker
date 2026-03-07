import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from app.features.outbox.schemas import EnqueueOutboxEventCommand, OutboxEventRecord
from app.features.outbox.service import OutboxService


def _build_unit_of_work_mock() -> MagicMock:
    unit_of_work = MagicMock()
    unit_of_work.__aenter__ = AsyncMock(return_value=unit_of_work)
    unit_of_work.__aexit__ = AsyncMock(return_value=None)
    return unit_of_work


def _build_outbox_event(*, event_id: int, published_at: datetime | None = None) -> OutboxEventRecord:
    return OutboxEventRecord(
        id=event_id,
        aggregate_type="book",
        aggregate_id=str(event_id),
        event_type="book.updated",
        payload={"book_id": event_id},
        occurred_at=datetime(2026, 3, 5, 10, 0, tzinfo=UTC),
        published_at=published_at,
    )


def test_outbox_service_enqueue_uses_transaction_scope() -> None:
    outbox_repository = MagicMock()
    outbox_repository.create_event = AsyncMock(return_value=_build_outbox_event(event_id=33))
    unit_of_work = _build_unit_of_work_mock()
    service = OutboxService(outbox_repository=outbox_repository, unit_of_work=unit_of_work)
    command = EnqueueOutboxEventCommand(
        aggregate_type="book",
        aggregate_id="33",
        event_type="book.updated",
        payload={"book_id": 33},
    )

    async def run_test() -> None:
        outbox_event = await service.enqueue(command)

        assert outbox_event.id == 33
        outbox_repository.create_event.assert_awaited_once_with(
            aggregate_type="book",
            aggregate_id="33",
            event_type="book.updated",
            payload={"book_id": 33},
        )
        unit_of_work.__aenter__.assert_awaited_once_with()
        unit_of_work.__aexit__.assert_awaited_once_with(None, None, None)

    asyncio.run(run_test())


def test_outbox_service_list_pending_does_not_open_transaction_scope() -> None:
    outbox_repository = MagicMock()
    outbox_repository.list_pending = AsyncMock(return_value=[_build_outbox_event(event_id=44)])
    unit_of_work = _build_unit_of_work_mock()
    service = OutboxService(outbox_repository=outbox_repository, unit_of_work=unit_of_work)

    async def run_test() -> None:
        outbox_events = await service.list_pending(limit=10)

        assert len(outbox_events) == 1
        assert outbox_events[0].id == 44
        outbox_repository.list_pending.assert_awaited_once_with(limit=10)
        unit_of_work.__aenter__.assert_not_awaited()
        unit_of_work.__aexit__.assert_not_awaited()

    asyncio.run(run_test())


def test_outbox_service_mark_published_returns_none_when_event_is_missing() -> None:
    outbox_repository = MagicMock()
    outbox_repository.get_event = AsyncMock(return_value=None)
    outbox_repository.mark_published = AsyncMock()
    unit_of_work = _build_unit_of_work_mock()
    service = OutboxService(outbox_repository=outbox_repository, unit_of_work=unit_of_work)

    async def run_test() -> None:
        result = await service.mark_published(99)

        assert result is None
        outbox_repository.get_event.assert_awaited_once_with(99)
        outbox_repository.mark_published.assert_not_awaited()
        unit_of_work.__aenter__.assert_awaited_once_with()
        unit_of_work.__aexit__.assert_awaited_once_with(None, None, None)

    asyncio.run(run_test())


def test_outbox_service_mark_published_updates_existing_event() -> None:
    existing_event = _build_outbox_event(event_id=50)
    published_event = _build_outbox_event(
        event_id=50,
        published_at=datetime(2026, 3, 5, 11, 0, tzinfo=UTC),
    )
    outbox_repository = MagicMock()
    outbox_repository.get_event = AsyncMock(return_value=existing_event)
    outbox_repository.mark_published = AsyncMock(return_value=published_event)
    unit_of_work = _build_unit_of_work_mock()
    service = OutboxService(outbox_repository=outbox_repository, unit_of_work=unit_of_work)

    async def run_test() -> None:
        result = await service.mark_published(50)

        assert result is not None
        assert result.id == 50
        assert result.published_at == datetime(2026, 3, 5, 11, 0, tzinfo=UTC)
        outbox_repository.get_event.assert_awaited_once_with(50)
        outbox_repository.mark_published.assert_awaited_once_with(existing_event)
        unit_of_work.__aenter__.assert_awaited_once_with()
        unit_of_work.__aexit__.assert_awaited_once_with(None, None, None)

    asyncio.run(run_test())
