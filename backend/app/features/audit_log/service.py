from typing import Protocol

from app.features.audit_log.schemas.app import AuditLogEntryResult

DEFAULT_AUDIT_LOG_LIMIT = 50
MAX_AUDIT_LOG_LIMIT = 100


class AuditLogRepositoryPort(Protocol):
    async def list_recent_entries(self, *, limit: int) -> list[AuditLogEntryResult]: ...


class AuditLogServicePort(Protocol):
    async def list_recent_entries(self) -> list[AuditLogEntryResult]: ...


class AuditLogService:
    def __init__(self, audit_log_repository: AuditLogRepositoryPort):
        self.audit_log_repository = audit_log_repository

    async def list_recent_entries(self) -> list[AuditLogEntryResult]:
        return await self.audit_log_repository.list_recent_entries(
            limit=min(DEFAULT_AUDIT_LOG_LIMIT, MAX_AUDIT_LOG_LIMIT)
        )
