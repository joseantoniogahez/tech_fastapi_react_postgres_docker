import { useQuery } from "@tanstack/react-query";

import { readAuditLogEntries } from "@/features/audit-log/api";
import { type AuditLogEntry } from "@/features/audit-log/contracts";
import { formatAuditLogTimestamp } from "@/features/audit-log/format";
import { t } from "@/shared/i18n/ui-text";
import {
  ADMIN_CARD_CLASS_NAME,
  ADMIN_MUTED_TEXT_CLASS_NAME,
  ADMIN_PAGE_CLASS_NAME,
  ADMIN_TITLE_CLASS_NAME,
  AdminErrorPanel,
} from "@/shared/rbac/ui";
import { CenteredMessage } from "@/shared/ui/CenteredMessage";

const AUDIT_LOG_QUERY_KEY = ["audit-log", "entries"] as const;

const formatAuditLogActor = (entry: AuditLogEntry): string =>
  entry.actor_user_id === null ? t("admin.auditLog.actor.system") : String(entry.actor_user_id);

const formatAuditLogResource = (entry: AuditLogEntry): string =>
  entry.resource_id === null ? entry.resource_type : `${entry.resource_type} #${entry.resource_id}`;

export const AuditLogPage = () => {
  const entriesQuery = useQuery({
    queryKey: AUDIT_LOG_QUERY_KEY,
    queryFn: readAuditLogEntries,
  });

  if (entriesQuery.isPending) {
    return <CenteredMessage title={t("admin.common.loading")} />;
  }

  const entries = entriesQuery.data ?? [];

  return (
    <main className={ADMIN_PAGE_CLASS_NAME}>
      <header>
        <h1 className={ADMIN_TITLE_CLASS_NAME}>{t("admin.auditLog.title")}</h1>
        <p className={`mt-2 ${ADMIN_MUTED_TEXT_CLASS_NAME}`}>{t("admin.auditLog.subtitle")}</p>
      </header>

      <AdminErrorPanel error={entriesQuery.error} />

      {entriesQuery.isError ? null : (
        <section className={ADMIN_CARD_CLASS_NAME}>
          {entries.length === 0 ? (
            <p className={ADMIN_MUTED_TEXT_CLASS_NAME}>{t("admin.auditLog.empty")}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[780px] border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-[var(--app-border)]">
                    <th className="px-2 py-2 font-semibold">{t("admin.auditLog.columns.createdAt")}</th>
                    <th className="px-2 py-2 font-semibold">{t("admin.auditLog.columns.actor")}</th>
                    <th className="px-2 py-2 font-semibold">{t("admin.auditLog.columns.action")}</th>
                    <th className="px-2 py-2 font-semibold">{t("admin.auditLog.columns.resource")}</th>
                    <th className="px-2 py-2 font-semibold">{t("admin.auditLog.columns.summary")}</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry) => (
                    <tr className="border-b border-[var(--app-border)]" key={entry.id}>
                      <td className="px-2 py-3">
                        <time dateTime={entry.created_at}>{formatAuditLogTimestamp(entry.created_at)}</time>
                      </td>
                      <td className="px-2 py-3">{formatAuditLogActor(entry)}</td>
                      <td className="px-2 py-3 font-medium">{entry.action}</td>
                      <td className="px-2 py-3">{formatAuditLogResource(entry)}</td>
                      <td className="px-2 py-3">{entry.summary}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </main>
  );
};
