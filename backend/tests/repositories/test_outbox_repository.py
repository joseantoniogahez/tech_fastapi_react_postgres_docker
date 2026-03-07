import asyncio
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.core.errors.repositories import RepositoryError
from app.features.outbox.models import OutboxEvent
from app.features.outbox.repository import OutboxRepository
from app.features.outbox.schemas import OutboxEventRecord
from utils.testing_support.repositories import build_session_mock


def _scalar_result(rows: list[object]) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    return result


def test_outbox_repository_create_event_persists_outbox_record() -> None:
    session = build_session_mock()
    repository = OutboxRepository(session=session)
    expected_occurred_at = datetime(2026, 3, 5, 12, 0, tzinfo=UTC)

    async def refresh(entity: OutboxEvent) -> None:
        entity.id = 101
        entity.occurred_at = expected_occurred_at
        entity.published_at = None

    session.refresh.side_effect = refresh

    async def run_test() -> None:
        event = await repository.create_event(
            aggregate_type="book",
            aggregate_id="42",
            event_type="book.updated",
            payload={"book_id": 42},
        )

        assert isinstance(event, OutboxEventRecord)
        assert event.id == 101
        assert event.aggregate_type == "book"
        assert event.aggregate_id == "42"
        assert event.event_type == "book.updated"
        assert event.payload == {"book_id": 42}
        assert event.occurred_at == expected_occurred_at
        assert event.published_at is None
        session.add.assert_called_once()
        session.flush.assert_awaited_once()
        session.refresh.assert_awaited_once()

    asyncio.run(run_test())


def test_outbox_repository_create_event_preserves_explicit_occurred_at() -> None:
    session = build_session_mock()
    repository = OutboxRepository(session=session)
    explicit_occurred_at = datetime(2026, 3, 5, 9, 45, tzinfo=UTC)

    async def refresh(entity: OutboxEvent) -> None:
        entity.id = 202
        entity.published_at = None

    session.refresh.side_effect = refresh

    async def run_test() -> None:
        event = await repository.create_event(
            aggregate_type="book",
            aggregate_id="202",
            event_type="book.created",
            payload={"book_id": 202},
            occurred_at=explicit_occurred_at,
        )

        assert event.id == 202
        assert event.occurred_at == explicit_occurred_at

    asyncio.run(run_test())


def test_outbox_repository_list_pending_filters_unpublished_events() -> None:
    session = build_session_mock()
    repository = OutboxRepository(session=session)
    pending_event = OutboxEvent(
        id=7,
        aggregate_type="book",
        aggregate_id="7",
        event_type="book.created",
        payload={"book_id": 7},
        occurred_at=datetime(2026, 3, 5, 12, 30, tzinfo=UTC),
        published_at=None,
    )
    session.execute.return_value = _scalar_result([pending_event])

    async def run_test() -> None:
        events = await repository.list_pending(limit=25)

        assert len(events) == 1
        assert events[0].aggregate_type == pending_event.aggregate_type
        assert events[0].aggregate_id == pending_event.aggregate_id
        assert events[0].event_type == pending_event.event_type
        assert events[0].payload == pending_event.payload
        assert events[0].occurred_at == pending_event.occurred_at
        session.execute.assert_awaited_once()
        query = session.execute.await_args.args[0]
        query_text = str(query)
        assert "outbox_events.published_at IS NULL" in query_text
        assert "ORDER BY outbox_events.occurred_at ASC, outbox_events.id ASC" in query_text
        assert "LIMIT :param_1" in query_text

    asyncio.run(run_test())


def test_outbox_repository_get_event_returns_none_when_event_is_missing() -> None:
    session = build_session_mock()
    repository = OutboxRepository(session=session)
    session.get.return_value = None

    async def run_test() -> None:
        event = await repository.get_event(999)

        assert event is None
        session.get.assert_awaited_once_with(repository.model, 999)

    asyncio.run(run_test())


def test_outbox_repository_get_event_returns_record_when_event_exists() -> None:
    session = build_session_mock()
    repository = OutboxRepository(session=session)
    outbox_event_model = OutboxEvent(
        id=303,
        aggregate_type="book",
        aggregate_id="303",
        event_type="book.updated",
        payload={"book_id": 303},
        occurred_at=datetime(2026, 3, 5, 13, 0, tzinfo=UTC),
        published_at=None,
    )
    session.get.return_value = outbox_event_model

    async def run_test() -> None:
        event = await repository.get_event(303)

        assert event is not None
        assert event.id == 303
        assert event.aggregate_id == "303"

    asyncio.run(run_test())


def test_outbox_repository_list_pending_rejects_invalid_limit() -> None:
    session = build_session_mock()
    repository = OutboxRepository(session=session)

    async def run_test() -> None:
        with pytest.raises(RepositoryError, match="Limit must be greater than or equal to 1"):
            await repository.list_pending(limit=0)

        session.execute.assert_not_awaited()

    asyncio.run(run_test())


def test_outbox_repository_mark_published_updates_timestamp() -> None:
    session = build_session_mock()
    repository = OutboxRepository(session=session)
    outbox_event_model = OutboxEvent(
        id=11,
        aggregate_type="book",
        aggregate_id="11",
        event_type="book.deleted",
        payload={"book_id": 11},
        occurred_at=datetime(2026, 3, 5, 11, 0, tzinfo=UTC),
        published_at=None,
    )
    outbox_event = OutboxEventRecord.from_domain(outbox_event_model)
    expected_published_at = datetime(2026, 3, 5, 12, 0, tzinfo=UTC)
    session.get.return_value = outbox_event_model
    session.merge.return_value = outbox_event_model

    async def run_test() -> None:
        marked_event = await repository.mark_published(
            outbox_event,
            published_at=expected_published_at,
        )

        assert marked_event.id == outbox_event.id
        assert marked_event.published_at == expected_published_at
        assert outbox_event_model.published_at == expected_published_at
        session.get.assert_awaited_once()
        session.merge.assert_awaited_once_with(outbox_event_model)
        session.flush.assert_awaited_once()
        session.refresh.assert_awaited_once_with(outbox_event_model)

    asyncio.run(run_test())


def test_outbox_repository_mark_published_raises_when_event_is_missing() -> None:
    session = build_session_mock()
    repository = OutboxRepository(session=session)
    missing_event = OutboxEventRecord(
        id=404,
        aggregate_type="book",
        aggregate_id="404",
        event_type="book.deleted",
        payload={"book_id": 404},
        occurred_at=datetime(2026, 3, 5, 15, 0, tzinfo=UTC),
        published_at=None,
    )
    session.get.return_value = None

    async def run_test() -> None:
        with pytest.raises(RepositoryError, match="Outbox event 404 not found"):
            await repository.mark_published(missing_event)

    asyncio.run(run_test())
