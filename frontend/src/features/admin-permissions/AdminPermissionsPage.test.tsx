import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { createQueryClient } from "@/app/query-client";
import { AdminPermissionsPage } from "@/features/admin-permissions/AdminPermissionsPage";
import { SESSION_QUERY_KEY } from "@/shared/auth/session";
import { IAM_PERMISSION } from "@/shared/iam/contracts";
import { t } from "@/shared/i18n/ui-text";

interface MockRolePermission {
  id: string;
  name: string;
  scope: string;
}

interface MockRole {
  id: number;
  name: string;
  permissions: MockRolePermission[];
  parent_role_ids: number[];
}

interface MockPermission {
  id: string;
  name: string;
}

const toRequestUrl = (input: RequestInfo | URL): URL => {
  if (input instanceof URL) {
    return input;
  }
  if (typeof input === "string") {
    return new URL(input);
  }
  return new URL(input.url);
};

const readJsonBody = <T,>(init?: RequestInit): T => {
  if (typeof init?.body !== "string") {
    throw new Error("Expected JSON string body");
  }
  return JSON.parse(init.body) as T;
};

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

const renderAdminPermissionsPage = (
  permissions: string[] = [IAM_PERMISSION.ROLE_PERMISSIONS_MANAGE, IAM_PERMISSION.ROLES_MANAGE],
) => {
  const queryClient = createQueryClient();
  queryClient.setQueryData(SESSION_QUERY_KEY, {
    id: 1,
    username: "admin",
    disabled: false,
    permissions,
  });

  render(
    <QueryClientProvider client={queryClient}>
      <AdminPermissionsPage />
    </QueryClientProvider>,
  );
};

describe("AdminPermissionsPage", () => {
  it.each(["own", "tenant", "any"] as const)(
    "renders explicit scope selection and submits %s without fallback",
    async (scope) => {
      let roles: MockRole[] = [
        {
          id: 2,
          name: "editor_role",
          permissions: [],
          parent_role_ids: [],
        },
      ];
      const permissions: MockPermission[] = [
        {
          id: "users:manage",
          name: "Manage users",
        },
      ];

      const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const requestUrl = toRequestUrl(input);
        const method = init?.method ?? "GET";
        const path = requestUrl.pathname;

        if (method === "GET" && path === "/v1/rbac/roles") {
          return jsonResponse(200, roles);
        }

        if (method === "GET" && path === "/v1/rbac/permissions") {
          return jsonResponse(200, permissions);
        }

        if (method === "PUT" && path === "/v1/rbac/roles/2/permissions/users%3Amanage") {
          const payload = readJsonBody<{ scope: string }>(init);
          roles = roles.map((role) =>
            role.id === 2
              ? {
                  ...role,
                  permissions: [
                    {
                      id: "users:manage",
                      name: "Manage users",
                      scope: payload.scope,
                    },
                  ],
                }
              : role,
          );
          return jsonResponse(200, {
            id: "users:manage",
            name: "Manage users",
            scope: payload.scope,
          });
        }

        if (method === "DELETE" && path === "/v1/rbac/roles/2/permissions/users%3Amanage") {
          roles = roles.map((role) =>
            role.id === 2 ? { ...role, permissions: [] } : role,
          );
          return jsonResponse(204, null);
        }

        throw new Error(`Unhandled request: ${method} ${path}`);
      });
      vi.stubGlobal("fetch", fetchMock);
      const user = userEvent.setup();

      renderAdminPermissionsPage();

      expect(await screen.findByRole("heading", { name: t("admin.pm.title") })).toBeInTheDocument();
      const roleSelect = await screen.findByLabelText(t("admin.roles.create.name"));
      const permissionSelect = await screen.findByLabelText(t("admin.roles.permissions.select"));
      const scopeSelect = await screen.findByLabelText(t("admin.roles.permissions.scope.label"));

      expect(within(scopeSelect).getByRole("option", { name: "own" })).toBeInTheDocument();
      expect(within(scopeSelect).getByRole("option", { name: "tenant" })).toBeInTheDocument();
      expect(within(scopeSelect).getByRole("option", { name: "any" })).toBeInTheDocument();

      await user.selectOptions(roleSelect, "2");
      await user.selectOptions(permissionSelect, "users:manage");

      const assignButton = screen.getByRole("button", { name: t("admin.roles.permissions.add") });
      expect(assignButton).toBeDisabled();

      await user.selectOptions(scopeSelect, scope);
      expect(assignButton).toBeEnabled();
      await user.click(assignButton);

      await waitFor(() => {
        expect(
          fetchMock.mock.calls.some((call) => {
            const requestUrl = toRequestUrl(call[0]);
            const request = call[1];
            return (
              requestUrl.pathname === "/v1/rbac/roles/2/permissions/users%3Amanage" &&
              request?.method === "PUT" &&
              request.body === JSON.stringify({ scope })
            );
          }),
        ).toBe(true);
      });

      const listCard = screen.getByRole("heading", { name: t("admin.pm.list") }).closest("article");
      expect(listCard).not.toBeNull();
      if (!listCard) {
        throw new Error("Expected assigned permissions card");
      }

      expect(await within(listCard).findByText("Manage users")).toBeInTheDocument();
      expect(await within(listCard).findByText(new RegExp(`Alcance: ${scope}`))).toBeInTheDocument();

      const permissionRow = within(listCard).getByText("Manage users").closest("li");
      expect(permissionRow).not.toBeNull();
      if (!permissionRow) {
        throw new Error("Expected permission row");
      }

      await user.click(within(permissionRow).getByRole("button", { name: t("admin.roles.permissions.remove") }));

      await waitFor(() => {
        expect(
          fetchMock.mock.calls.some((call) => {
            const requestUrl = toRequestUrl(call[0]);
            const request = call[1];
            return requestUrl.pathname === "/v1/rbac/roles/2/permissions/users%3Amanage" && request?.method === "DELETE";
          }),
        ).toBe(true);
      });

      await waitFor(() => {
        expect(within(listCard).getByText(t("admin.roles.card.noPermissions"))).toBeInTheDocument();
      });
    },
  );

  it("supports permission-only manual mode and surfaces request-id diagnostics", async () => {
    const requestPaths: string[] = [];
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const requestUrl = toRequestUrl(input);
      const method = init?.method ?? "GET";
      const path = requestUrl.pathname;
      requestPaths.push(path);

      if (method === "GET" && path === "/v1/rbac/permissions") {
        return jsonResponse(200, [
          {
            id: "users:manage",
            name: "Manage users",
          },
        ]);
      }

      if (method === "PUT" && path === "/v1/rbac/roles/999/permissions/users%3Amanage") {
        return jsonResponse(
          404,
          {
            detail: "Role 999 not found",
            code: "not_found",
            request_id: "req-permissions-404",
          },
          "req-permissions-404",
        );
      }

      if (method === "DELETE" && path === "/v1/rbac/roles/999/permissions/users%3Amanage") {
        return jsonResponse(204, null);
      }

      throw new Error(`Unhandled request: ${method} ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    renderAdminPermissionsPage([IAM_PERMISSION.ROLE_PERMISSIONS_MANAGE]);

    expect(await screen.findByRole("heading", { name: t("admin.pm.title") })).toBeInTheDocument();
    expect(screen.getByText(t("admin.pm.manual"))).toBeInTheDocument();

    await user.type(screen.getByLabelText(t("admin.as.rid")), "999");
    await user.selectOptions(screen.getByLabelText(t("admin.roles.permissions.select")), "users:manage");
    await user.click(screen.getByRole("button", { name: t("admin.roles.permissions.remove") }));
    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some((call) => {
          const requestUrl = toRequestUrl(call[0]);
          const request = call[1];
          return requestUrl.pathname === "/v1/rbac/roles/999/permissions/users%3Amanage" && request?.method === "DELETE";
        }),
      ).toBe(true);
    });
    await user.selectOptions(screen.getByLabelText(t("admin.roles.permissions.scope.label")), "tenant");
    await user.click(screen.getByRole("button", { name: t("admin.roles.permissions.add") }));

    expect(await screen.findByText(/request_id=req-permissions-404/)).toBeInTheDocument();
    expect(requestPaths).not.toContain("/v1/rbac/roles");
  });
});
