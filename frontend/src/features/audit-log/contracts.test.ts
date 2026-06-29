import { ApiContractError } from "@/shared/api/contracts";
import { parseAuditLogEntry, parseAuditLogEntryList } from "@/features/audit-log/contracts";

describe("audit log contracts", () => {
  it("parses audit log entries with nullable actor and resource fields", () => {
    expect(
      parseAuditLogEntry({
        id: 1,
        actor_user_id: null,
        action: "system.seeded",
        resource_type: "rbac",
        resource_id: null,
        summary: "Seeded RBAC catalog",
        created_at: "2026-05-01T12:00:00Z",
      }),
    ).toEqual({
      id: 1,
      actor_user_id: null,
      action: "system.seeded",
      resource_type: "rbac",
      resource_id: null,
      summary: "Seeded RBAC catalog",
      created_at: "2026-05-01T12:00:00Z",
    });

    expect(
      parseAuditLogEntryList([
        {
          id: 2,
          actor_user_id: 1,
          action: "user.updated",
          resource_type: "user",
          resource_id: "3",
          summary: "Updated user reader_user",
          created_at: "2026-05-01T12:05:00Z",
        },
      ]),
    ).toHaveLength(1);
  });

  it("rejects invalid audit log entry payloads", () => {
    expect(() =>
      parseAuditLogEntry({
        id: 1,
        actor_user_id: "admin",
        action: "user.updated",
        resource_type: "user",
        resource_id: "3",
        summary: "Updated user reader_user",
        created_at: "2026-05-01T12:05:00Z",
      }),
    ).toThrowError(new ApiContractError("AuditLogEntry: invalid nullable number 'actor_user_id'"));

    expect(() => parseAuditLogEntryList({})).toThrowError(
      new ApiContractError("AuditLogEntryList: expected array payload"),
    );
  });
});
