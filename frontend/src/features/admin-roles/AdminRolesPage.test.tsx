import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { createQueryClient } from "@/app/query-client";
import { AdminRolesPage } from "@/features/admin-roles/AdminRolesPage";
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

const renderAdminRolesPage = () => {
  const queryClient = createQueryClient();

  render(
    <QueryClientProvider client={queryClient}>
      <AdminRolesPage />
    </QueryClientProvider>,
  );
};

describe("AdminRolesPage", () => {
  it(
    "completes role create/update/delete and assignment flows",
    async () => {
    let roles: MockRole[] = [
      {
        id: 1,
        name: "admin_role",
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

      if (method === "POST" && path === "/v1/rbac/roles") {
        const payload = readJsonBody<{ name: string }>(init);
        const createdRole: MockRole = {
          id: 2,
          name: payload.name,
          permissions: [],
          parent_role_ids: [],
        };
        roles = [...roles, createdRole];
        return jsonResponse(201, createdRole);
      }

      if (method === "PUT" && path === "/v1/rbac/roles/2") {
        const payload = readJsonBody<{ name: string }>(init);
        roles = roles.map((role) => (role.id === 2 ? { ...role, name: payload.name } : role));
        return jsonResponse(200, roles.find((role) => role.id === 2));
      }

      if (method === "PUT" && path === "/v1/rbac/roles/2/inherits/1") {
        roles = roles.map((role) =>
          role.id === 2 ? { ...role, parent_role_ids: [...new Set([...role.parent_role_ids, 1])] } : role,
        );
        return jsonResponse(204, null);
      }

      if (method === "DELETE" && path === "/v1/rbac/roles/2/inherits/1") {
        roles = roles.map((role) =>
          role.id === 2
            ? { ...role, parent_role_ids: role.parent_role_ids.filter((parentRoleId) => parentRoleId !== 1) }
            : role,
        );
        return jsonResponse(204, null);
      }

      if (method === "PUT" && path === "/v1/rbac/roles/2/permissions/users%3Amanage") {
        roles = roles.map((role) =>
          role.id === 2
            ? {
                ...role,
                permissions: [
                  ...role.permissions,
                  {
                    id: "users:manage",
                    name: "Manage users",
                    scope: "any",
                  },
                ],
              }
            : role,
        );
        return jsonResponse(200, {
          id: "users:manage",
          name: "Manage users",
          scope: "any",
        });
      }

      if (method === "DELETE" && path === "/v1/rbac/roles/2/permissions/users%3Amanage") {
        roles = roles.map((role) =>
          role.id === 2
            ? { ...role, permissions: role.permissions.filter((permission) => permission.id !== "users:manage") }
            : role,
        );
        return jsonResponse(204, null);
      }

      if (method === "DELETE" && path === "/v1/rbac/roles/2") {
        roles = roles.filter((role) => role.id !== 2);
        return jsonResponse(204, null);
      }

      throw new Error(`Unhandled request: ${method} ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(window, "confirm").mockReturnValueOnce(false).mockReturnValue(true);
    const user = userEvent.setup();

    renderAdminRolesPage();

    expect(await screen.findByRole("heading", { name: t("admin.roles.title") })).toBeInTheDocument();

    const [createRoleInput] = screen.getAllByLabelText(t("admin.roles.create.name"));
    await user.type(createRoleInput, "editor_role");
    await user.click(screen.getByRole("button", { name: t("admin.roles.create.submit") }));

    const editorRoleInput = await screen.findByDisplayValue("editor_role");
    const editorRoleCard = editorRoleInput.closest("section");
    expect(editorRoleCard).not.toBeNull();
    if (!editorRoleCard) {
      return;
    }

    await user.selectOptions(within(editorRoleCard).getByLabelText(t("admin.roles.parents.select")), "1");
    await user.click(within(editorRoleCard).getByRole("button", { name: t("admin.roles.parents.add") }));
    expect(await within(editorRoleCard).findByText("admin_role")).toBeInTheDocument();
    await user.click(within(editorRoleCard).getByRole("button", { name: t("admin.roles.parents.remove") }));
    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some((call) => {
          const requestUrl = toRequestUrl(call[0]);
          const request = call[1];
          return requestUrl.pathname === "/v1/rbac/roles/2/inherits/1" && request?.method === "DELETE";
        }),
      ).toBe(true);
    });

    await user.selectOptions(
      within(editorRoleCard).getByLabelText(t("admin.roles.permissions.select")),
      "users:manage",
    );
    await user.click(within(editorRoleCard).getByRole("button", { name: t("admin.roles.permissions.add") }));
    expect(await within(editorRoleCard).findByText("Manage users")).toBeInTheDocument();
    await user.click(within(editorRoleCard).getByRole("button", { name: t("admin.roles.permissions.remove") }));
    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some((call) => {
          const requestUrl = toRequestUrl(call[0]);
          const request = call[1];
          return requestUrl.pathname === "/v1/rbac/roles/2/permissions/users%3Amanage" && request?.method === "DELETE";
        }),
      ).toBe(true);
    });

    await user.clear(within(editorRoleCard).getByLabelText(t("admin.roles.create.name")));
    await user.type(within(editorRoleCard).getByLabelText(t("admin.roles.create.name")), "editor_role_v2");
    await user.click(within(editorRoleCard).getByRole("button", { name: t("admin.roles.actions.update") }));
    expect(await within(editorRoleCard).findByDisplayValue("editor_role_v2")).toBeInTheDocument();

    await user.click(within(editorRoleCard).getByRole("button", { name: t("admin.roles.actions.delete") }));
    expect(
      fetchMock.mock.calls.some((call) => {
        const requestUrl = toRequestUrl(call[0]);
        const request = call[1];
        return requestUrl.pathname === "/v1/rbac/roles/2" && request?.method === "DELETE";
      }),
    ).toBe(false);
    await user.click(within(editorRoleCard).getByRole("button", { name: t("admin.roles.actions.delete") }));

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some((call) => {
          const requestUrl = toRequestUrl(call[0]);
          const request = call[1];
          return requestUrl.pathname === "/v1/rbac/roles/2" && request?.method === "DELETE";
        }),
      ).toBe(true);
    });
    },
    20000,
  );

  it("shows request-id diagnostics for API errors", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const requestUrl = toRequestUrl(input);
      const method = init?.method ?? "GET";
      const path = requestUrl.pathname;

      if (method === "GET" && path === "/v1/rbac/roles") {
        return jsonResponse(
          403,
          {
            detail: "Missing roles:manage",
            code: "forbidden",
            request_id: "req-roles-forbidden",
          },
          "req-roles-forbidden",
        );
      }

      if (method === "GET" && path === "/v1/rbac/permissions") {
        return jsonResponse(200, []);
      }

      throw new Error(`Unhandled request: ${method} ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderAdminRolesPage();

    expect(await screen.findByRole("heading", { name: t("admin.common.error.title") })).toBeInTheDocument();
    expect(await screen.findByText(/request_id=req-roles-forbidden/)).toBeInTheDocument();
  });

  it("shows inline conflict details when role create returns 409", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const requestUrl = toRequestUrl(input);
      const method = init?.method ?? "GET";
      const path = requestUrl.pathname;

      if (method === "GET" && path === "/v1/rbac/roles") {
        return jsonResponse(200, []);
      }

      if (method === "GET" && path === "/v1/rbac/permissions") {
        return jsonResponse(200, []);
      }

      if (method === "POST" && path === "/v1/rbac/roles") {
        return jsonResponse(
          409,
          {
            detail: "Role name already exists",
            code: "conflict",
            request_id: "req-roles-conflict",
          },
          "req-roles-conflict",
        );
      }

      throw new Error(`Unhandled request: ${method} ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    renderAdminRolesPage();

    const [createRoleInput] = await screen.findAllByLabelText(t("admin.roles.create.name"));
    await user.type(createRoleInput, "duplicate_role");
    await user.click(screen.getByRole("button", { name: t("admin.roles.create.submit") }));

    expect(await screen.findByRole("heading", { name: t("admin.common.error.title") })).toBeInTheDocument();
    expect(await screen.findByText(/Role name already exists/)).toBeInTheDocument();
    expect(await screen.findByText(/request_id=req-roles-conflict/)).toBeInTheDocument();
  });

  it("shows generic ui error for non-api exceptions", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const requestUrl = toRequestUrl(input);
      const method = init?.method ?? "GET";
      const path = requestUrl.pathname;

      if (method === "GET" && path === "/v1/rbac/roles") {
        return jsonResponse(200, [{ id: "invalid" }]);
      }

      if (method === "GET" && path === "/v1/rbac/permissions") {
        return jsonResponse(200, []);
      }

      throw new Error(`Unhandled request: ${method} ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderAdminRolesPage();

    await waitFor(
      () => {
        expect(screen.getByRole("heading", { name: t("admin.common.error.title") })).toBeInTheDocument();
        expect(screen.getByText(t("admin.common.error.generic"))).toBeInTheDocument();
      },
      { timeout: 4000 },
    );
    await waitFor(() => {
      expect(fetchMock.mock.calls.length).toBeGreaterThanOrEqual(3);
    });
  });
});
