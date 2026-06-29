import asyncio
from datetime import UTC, datetime
from unittest.mock import MagicMock

from app.features.audit_log.models import AuditLogEntry
from app.features.audit_log.repository import AuditLogRepository
from utils.testing_support.repositories import build_session_mock


def _scalar_result(rows: list[object]) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    return result


def test_audit_log_repository_lists_recent_entries_by_newest_first() -> None:
    session = build_session_mock()
    repository = AuditLogRepository(session=session)
    session.execute.return_value = _scalar_result(
        [
            AuditLogEntry(
                id=2,
                actor_user_id=1,
                action="user.updated",
                resource_type="user",
                resource_id="3",
                summary="Updated user reader_user",
                created_at=datetime(2026, 5, 1, 12, 5, tzinfo=UTC),
                updated_at=datetime(2026, 5, 1, 12, 5, tzinfo=UTC),
            ),
            AuditLogEntry(
                id=1,
                actor_user_id=1,
                action="user.created",
                resource_type="user",
                resource_id="3",
                summary="Created user reader_user",
                created_at=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
                updated_at=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
            ),
        ]
    )

    async def run_test() -> None:
        entries = await repository.list_recent_entries(limit=50)

        assert [entry.id for entry in entries] == [2, 1]
        assert entries[0].action == "user.updated"
        session.execute.assert_awaited_once()
        query = session.execute.await_args.args[0]
        assert "ORDER BY audit_log_entries.created_at DESC, audit_log_entries.id DESC" in str(query)
        assert "LIMIT" in str(query)

    asyncio.run(run_test())
