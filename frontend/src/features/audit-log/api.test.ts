import { buildApiUrl } from "@/shared/api/env";
import { readAuditLogEntries } from "@/features/audit-log/api";
import { setAccessToken } from "@/shared/auth/storage";

describe("audit log API client", () => {
  it("reads audit log entries through the protected endpoint", async () => {
    setAccessToken("audit-token");
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          {
            id: 1,
            actor_user_id: null,
            action: "system.seeded",
            resource_type: "rbac",
            resource_id: null,
            summary: "Seeded RBAC catalog",
            created_at: "2026-05-01T12:00:00Z",
          },
        ]),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    const entries = await readAuditLogEntries();

    expect(entries).toHaveLength(1);
    const [entry] = entries;
    expect(entry).toBeDefined();
    if (!entry) {
      throw new Error("Expected audit log entry");
    }
    expect(entry.action).toBe("system.seeded");
    const [url, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(buildApiUrl("/audit-log"));
    expect(request.method).toBeUndefined();
    expect(new Headers(request.headers).get("Authorization")).toBe("Bearer audit-token");
  });
});
