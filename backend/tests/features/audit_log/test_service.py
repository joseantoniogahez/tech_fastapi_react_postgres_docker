import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.features.audit_log.service import DEFAULT_AUDIT_LOG_LIMIT, AuditLogService


def test_audit_log_service_lists_recent_entries_with_default_limit() -> None:
    repository = MagicMock()
    repository.list_recent_entries = AsyncMock(return_value=[])
    service = AuditLogService(audit_log_repository=repository)

    async def run_test() -> None:
        entries = await service.list_recent_entries()

        assert entries == []
        repository.list_recent_entries.assert_awaited_once_with(limit=DEFAULT_AUDIT_LOG_LIMIT)

    asyncio.run(run_test())
