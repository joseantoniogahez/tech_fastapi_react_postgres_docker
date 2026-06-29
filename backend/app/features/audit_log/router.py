from fastapi import APIRouter

from app.core.setup.dependencies import AuditLogServiceDependency
from app.features.audit_log.dependencies import AuditLogReadAuth
from app.features.audit_log.openapi import GET_AUDIT_LOG_ENTRIES_DOC
from app.features.audit_log.schemas.api import AuditLogEntryResponse

router = APIRouter(
    prefix="/audit-log",
    tags=["audit-log"],
)


@router.get("", response_model=list[AuditLogEntryResponse], **GET_AUDIT_LOG_ENTRIES_DOC)
async def list_audit_log_entries(
    audit_log_service: AuditLogServiceDependency,
    _authorized_user: AuditLogReadAuth,
) -> list[AuditLogEntryResponse]:
    entries = await audit_log_service.list_recent_entries()
    return [AuditLogEntryResponse.model_validate(entry) for entry in entries]
