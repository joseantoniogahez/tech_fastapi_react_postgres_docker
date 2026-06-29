from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.repository_base import BaseRepository
from app.features.audit_log.models import AuditLogEntry
from app.features.audit_log.schemas.app import AuditLogEntryResult


class AuditLogRepository(BaseRepository[AuditLogEntry]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, AuditLogEntry, default_record_type=AuditLogEntryResult)

    async def list_recent_entries(self, *, limit: int) -> list[AuditLogEntryResult]:
        query = select(AuditLogEntry).order_by(AuditLogEntry.created_at.desc(), AuditLogEntry.id.desc()).limit(limit)
        result = await self.session.execute(query)
        return self._to_records(list(result.scalars().all()))
