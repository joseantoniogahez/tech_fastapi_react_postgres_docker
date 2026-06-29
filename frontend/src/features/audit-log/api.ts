import { apiRequest } from "@/shared/api/http";
import { parseAuditLogEntryList, type AuditLogEntry } from "@/features/audit-log/contracts";

export const AUDIT_LOG_ENDPOINT_PATH = "/audit-log";

export const readAuditLogEntries = (): Promise<AuditLogEntry[]> =>
  apiRequest<AuditLogEntry[]>(AUDIT_LOG_ENDPOINT_PATH, {
    parse: parseAuditLogEntryList,
  });
