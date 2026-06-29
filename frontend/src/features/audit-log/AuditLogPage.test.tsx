import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";

import { createQueryClient } from "@/app/query-client";
import { AUDIT_LOG_ENDPOINT_PATH } from "@/features/audit-log/api";
import { AuditLogPage } from "@/features/audit-log/AuditLogPage";
import { formatAuditLogTimestamp } from "@/features/audit-log/format";
import { buildApiUrl } from "@/shared/api/env";
import { setAccessToken } from "@/shared/auth/storage";
import { t } from "@/shared/i18n/ui-text";

const toRequestUrl = (input: RequestInfo | URL): URL => {
  if (input instanceof URL) {
    return input;
  }
  if (typeof input === "string") {
    return new URL(input);
  }
  return new URL(input.url);
};

const auditLogRequestPathname = new URL(buildApiUrl(AUDIT_LOG_ENDPOINT_PATH)).pathname;

const isAuditLogRequest = (input: RequestInfo | URL): boolean =>
  toRequestUrl(input).pathname === auditLogRequestPathname;

const ASYNC_ROUTE_TIMEOUT = { timeout: 5000 } as const;

const jsonResponse = (status: number, payload: unknown, requestId?: string): Partial<Response> => ({
  ok: status >= 200 && status < 300,
  status,
  statusText: status === 204 ? "No Content" : "OK",
  headers: {
    get: (name: string) => {
      if (name.toLowerCase() !== "x-request-id") {
        return null;
      }
      return requestId ?? null;
    },
  },
  json: () => Promise.resolve(payload),
});

const renderAuditLogPage = () => {
  const queryClient = createQueryClient();

  render(
    <QueryClientProvider client={queryClient}>
      <AuditLogPage />
    </QueryClientProvider>,
  );
};

describe("AuditLogPage", () => {
  it("renders audit entries with stable labels and timestamps", async () => {
    setAccessToken("audit-token");
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const requestUrl = toRequestUrl(input);
      if (isAuditLogRequest(input)) {
        return jsonResponse(200, [
          {
            id: 2,
            actor_user_id: 1,
            action: "user.updated",
            resource_type: "user",
            resource_id: "3",
            summary: "Updated user reader_user",
            created_at: "2026-05-01T12:05:00Z",
          },
          {
            id: 1,
            actor_user_id: null,
            action: "system.seeded",
            resource_type: "rbac",
            resource_id: null,
            summary: "Seeded RBAC catalog",
            created_at: "2026-05-01T12:00:00Z",
          },
        ]);
      }

      throw new Error(`Unhandled audit log request: ${requestUrl.pathname}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderAuditLogPage();

    expect(
      await screen.findByRole("heading", { name: t("admin.auditLog.title") }, ASYNC_ROUTE_TIMEOUT),
    ).toBeInTheDocument();
    expect(screen.getByText(t("admin.auditLog.subtitle"))).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: t("admin.auditLog.columns.createdAt") })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: t("admin.auditLog.columns.actor") })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: t("admin.auditLog.columns.action") })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: t("admin.auditLog.columns.resource") })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: t("admin.auditLog.columns.summary") })).toBeInTheDocument();

    const updatedRow = (await screen.findByText("Updated user reader_user")).closest("tr");
    expect(updatedRow).not.toBeNull();
    if (!updatedRow) {
      throw new Error("Expected updated audit row");
    }

    expect(within(updatedRow).getByText("2026-05-01T12:05:00 UTC")).toBeInTheDocument();
    expect(within(updatedRow).getByText("1")).toBeInTheDocument();
    expect(within(updatedRow).getByText("user.updated")).toBeInTheDocument();
    expect(within(updatedRow).getByText("user #3")).toBeInTheDocument();
    expect(screen.getByText(t("admin.auditLog.actor.system"))).toBeInTheDocument();

    const [, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(new Headers(request.headers).get("Authorization")).toBe("Bearer audit-token");
  });

  it("renders empty state when no audit entries exist", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const requestUrl = toRequestUrl(input);
      if (isAuditLogRequest(input)) {
        return jsonResponse(200, []);
      }

      throw new Error(`Unhandled audit log request: ${requestUrl.pathname}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderAuditLogPage();

    expect(
      await screen.findByRole("heading", { name: t("admin.auditLog.title") }, ASYNC_ROUTE_TIMEOUT),
    ).toBeInTheDocument();
    expect(screen.getByText(t("admin.auditLog.empty"))).toBeInTheDocument();
  });

  it("shows request-id diagnostics for API errors", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const requestUrl = toRequestUrl(input);
      if (isAuditLogRequest(input)) {
        return jsonResponse(
          403,
          {
            detail: "Missing audit_logs:read",
            code: "forbidden",
            request_id: "req-audit-forbidden",
          },
          "req-audit-forbidden",
        );
      }

      throw new Error(`Unhandled audit log request: ${requestUrl.pathname}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderAuditLogPage();

    expect(
      await screen.findByRole("heading", { name: t("admin.common.error.title") }, ASYNC_ROUTE_TIMEOUT),
    ).toBeInTheDocument();
    expect(await screen.findByText(/request_id=req-audit-forbidden/)).toBeInTheDocument();
    expect(screen.queryByText(t("admin.auditLog.empty"))).not.toBeInTheDocument();
  });

  it("shows generic ui error for invalid audit log contracts", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const requestUrl = toRequestUrl(input);
      if (isAuditLogRequest(input)) {
        return jsonResponse(200, [{ id: "invalid" }]);
      }

      throw new Error(`Unhandled audit log request: ${requestUrl.pathname}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderAuditLogPage();

    await waitFor(
      () => {
        expect(screen.getByRole("heading", { name: t("admin.common.error.title") })).toBeInTheDocument();
        expect(screen.getByText(t("admin.common.error.generic"))).toBeInTheDocument();
      },
      { timeout: 4000 },
    );
  });

  it("keeps invalid timestamp strings unchanged", () => {
    expect(formatAuditLogTimestamp("not-a-date")).toBe("not-a-date");
  });
});
