import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { createQueryClient } from "@/app/query-client";
import { AdminUsersPage } from "@/features/admin-users/AdminUsersPage";
import { getAccessToken, setAccessToken } from "@/shared/auth/storage";
import { t } from "@/shared/i18n/ui-text";

interface MockUser {
  id: number;
  username: string;
  disabled: boolean;
  role_ids: number[];
}

interface MockRole {
  id: number;
  name: string;
  permissions: { id: string; name: string; scope: string }[];
  parent_role_ids: number[];
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

const renderAdminUsersPage = () => {
  const queryClient = createQueryClient();

  render(
    <QueryClientProvider client={queryClient}>
      <AdminUsersPage />
    </QueryClientProvider>,
  );
};

describe("AdminUsersPage", () => {
  it(
    "completes create, update and soft-delete flows",
    async () => {
    let users: MockUser[] = [
      {
        id: 1,
        username: "admin",
        disabled: false,
        role_ids: [1],
      },
    ];
    const roles: MockRole[] = [
      {
        id: 1,
        name: "admin_role",
        permissions: [],
        parent_role_ids: [],
      },
      {
        id: 2,
        name: "reader_role",
        permissions: [],
        parent_role_ids: [],
      },
    ];
    let updatedPayload: {
      username: string;
      disabled: boolean;
      role_ids: number[];
      current_password?: string;
      new_password?: string;
    } | null = null;

    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const requestUrl = toRequestUrl(input);
      const method = init?.method ?? "GET";
      const path = requestUrl.pathname;

      if (method === "GET" && path === "/v1/rbac/users") {
        return jsonResponse(200, users);
      }

      if (method === "GET" && path === "/v1/rbac/roles") {
        return jsonResponse(200, roles);
      }

      if (method === "POST" && path === "/v1/rbac/users") {
        const payload = readJsonBody<{ username: string; role_ids: number[] }>(init);
        const createdUser: MockUser = {
          id: 99,
          username: payload.username,
          disabled: false,
          role_ids: payload.role_ids,
        };
        users = [...users, createdUser];
        return jsonResponse(201, createdUser);
      }

      if (method === "PUT" && path === "/v1/rbac/users/99") {
        const payload = readJsonBody<{
          username: string;
          disabled: boolean;
          role_ids: number[];
          current_password?: string;
          new_password?: string;
        }>(init);
        updatedPayload = payload;
        users = users.map((user) =>
          user.id === 99
            ? {
                ...user,
                username: payload.username,
                disabled: payload.disabled,
                role_ids: payload.role_ids,
              }
            : user,
        );
        const updatedUser = users.find((user) => user.id === 99);
        return jsonResponse(200, updatedUser);
      }

      if (method === "DELETE" && path === "/v1/rbac/users/99") {
        users = users.map((user) => (user.id === 99 ? { ...user, disabled: true } : user));
        return jsonResponse(204, null);
      }

      throw new Error(`Unhandled request: ${method} ${path}`);
    });

    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(window, "confirm").mockReturnValueOnce(false).mockReturnValue(true);
    const user = userEvent.setup();

    renderAdminUsersPage();

    expect(
      await screen.findByRole("heading", { name: t("admin.users.title") }, { timeout: 8000 }),
    ).toBeInTheDocument();
    expect(await screen.findByText("admin", {}, { timeout: 8000 })).toBeInTheDocument();

    await user.type(screen.getByLabelText(t("admin.users.create.username")), "ops_user");
    await user.type(screen.getByLabelText(t("admin.users.create.password")), "OpsUser123");
    await user.selectOptions(screen.getByLabelText(t("admin.users.create.roles")), "2");
    await user.click(screen.getByRole("button", { name: t("admin.users.create.submit") }));

    const createdUsernameCell = await screen.findByText("ops_user");
    const createdRow = createdUsernameCell.closest("tr");
    expect(createdRow).not.toBeNull();
    if (!createdRow) {
      throw new Error("Expected created row");
    }

    await user.click(within(createdRow).getByRole("button", { name: t("admin.users.actions.edit") }));
    const editHeading = await screen.findByRole("heading", { name: /^Editar usuario:/ });
    const editSection = editHeading.closest("section");
    expect(editSection).not.toBeNull();
    if (!editSection) {
      throw new Error("Expected edit section");
    }
    const editFormScope = within(editSection);
    const editUsernameInput = editFormScope.getByLabelText(t("admin.users.edit.username"));
    const editCurrentPasswordInput = editFormScope.getByLabelText(t("admin.users.edit.currentPassword"));
    const editNewPasswordInput = editFormScope.getByLabelText(t("admin.users.edit.newPassword"));
    const editRolesInput = editFormScope.getByLabelText(t("admin.users.edit.roles"));

    await user.clear(editUsernameInput);
    await user.type(editUsernameInput, "ops_user_draft");
    await user.type(editCurrentPasswordInput, "OpsUser123");
    await user.type(editNewPasswordInput, "OpsUser456");
    await user.selectOptions(editRolesInput, "1");
    await user.click(editFormScope.getByRole("button", { name: t("admin.users.edit.cancel") }));

    expect(screen.queryByRole("button", { name: t("admin.users.edit.cancel") })).not.toBeInTheDocument();

    await user.click(within(createdRow).getByRole("button", { name: t("admin.users.actions.edit") }));
    const editHeadingSecondPass = await screen.findByRole("heading", { name: /^Editar usuario:/ });
    const editSectionSecondPass = editHeadingSecondPass.closest("section");
    expect(editSectionSecondPass).not.toBeNull();
    if (!editSectionSecondPass) {
      throw new Error("Expected edit section on second pass");
    }
    const editFormScopeSecondPass = within(editSectionSecondPass);
    await user.clear(editFormScopeSecondPass.getByLabelText(t("admin.users.edit.username")));
    await user.type(editFormScopeSecondPass.getByLabelText(t("admin.users.edit.username")), "ops_user_v2");
    await user.type(editFormScopeSecondPass.getByLabelText(t("admin.users.edit.currentPassword")), "OpsUser123");
    await user.type(editFormScopeSecondPass.getByLabelText(t("admin.users.edit.newPassword")), "OpsUser789");
    await user.selectOptions(editFormScopeSecondPass.getByLabelText(t("admin.users.edit.roles")), ["1", "2"]);
    const disabledCheckbox = editFormScopeSecondPass.getByLabelText(t("admin.users.edit.disabled"));
    await user.click(disabledCheckbox);
    await user.click(editFormScopeSecondPass.getByRole("button", { name: t("admin.users.edit.submit") }));

    await waitFor(() => {
      expect(screen.getByText(t("admin.users.status.disabled"))).toBeInTheDocument();
    });
    expect(updatedPayload).toEqual({
      username: "ops_user_v2",
      disabled: true,
      role_ids: [1, 2],
      current_password: "OpsUser123", // pragma: allowlist secret
      new_password: "OpsUser789", // pragma: allowlist secret
    });

    const updatedUsernameCell = await screen.findByText("ops_user_v2");
    const updatedRow = updatedUsernameCell.closest("tr");
    expect(updatedRow).not.toBeNull();
    if (!updatedRow) {
      throw new Error("Expected updated row");
    }

    await user.click(within(updatedRow).getByRole("button", { name: t("admin.users.actions.delete") }));
    expect(
      fetchMock.mock.calls.some((call) => {
        const requestUrl = toRequestUrl(call[0]);
        const request = call[1];
        return requestUrl.pathname === "/v1/rbac/users/99" && request?.method === "DELETE";
      }),
    ).toBe(false);

    await user.click(within(updatedRow).getByRole("button", { name: t("admin.users.actions.delete") }));

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some((call) => {
          const requestUrl = toRequestUrl(call[0]);
          const request = call[1];
          return requestUrl.pathname === "/v1/rbac/users/99" && request?.method === "DELETE";
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

      if (method === "GET" && path === "/v1/rbac/users") {
        return jsonResponse(
          403,
          {
            detail: "Missing users:manage",
            code: "forbidden",
            request_id: "req-users-forbidden",
          },
          "req-users-forbidden",
        );
      }

      if (method === "GET" && path === "/v1/rbac/roles") {
        return jsonResponse(200, []);
      }

      throw new Error(`Unhandled request: ${method} ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderAdminUsersPage();

    expect(await screen.findByRole("heading", { name: t("admin.common.error.title") })).toBeInTheDocument();
    expect(await screen.findByText(/request_id=req-users-forbidden/)).toBeInTheDocument();
  });

  it("shows inline conflict details when user create returns 409", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const requestUrl = toRequestUrl(input);
      const method = init?.method ?? "GET";
      const path = requestUrl.pathname;

      if (method === "GET" && path === "/v1/rbac/users") {
        return jsonResponse(200, []);
      }

      if (method === "GET" && path === "/v1/rbac/roles") {
        return jsonResponse(200, [
          {
            id: 1,
            name: "admin_role",
            permissions: [],
            parent_role_ids: [],
          },
        ]);
      }

      if (method === "POST" && path === "/v1/rbac/users") {
        return jsonResponse(
          409,
          {
            detail: "Username already exists",
            code: "conflict",
            request_id: "req-users-conflict",
          },
          "req-users-conflict",
        );
      }

      throw new Error(`Unhandled request: ${method} ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    renderAdminUsersPage();

    await screen.findByRole("heading", { name: t("admin.users.title") });
    await user.type(screen.getByLabelText(t("admin.users.create.username")), "duplicated");
    await user.type(screen.getByLabelText(t("admin.users.create.password")), "Duplicated123");
    await user.click(screen.getByRole("button", { name: t("admin.users.create.submit") }));

    expect(await screen.findByRole("heading", { name: t("admin.common.error.title") })).toBeInTheDocument();
    expect(await screen.findByText(/Username already exists/)).toBeInTheDocument();
    expect(await screen.findByText(/request_id=req-users-conflict/)).toBeInTheDocument();
  });

  it("clears invalid session token when RBAC endpoint responds 401", async () => {
    setAccessToken("expired-token");
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const requestUrl = toRequestUrl(input);
      const method = init?.method ?? "GET";
      const path = requestUrl.pathname;

      if (method === "GET" && path === "/v1/rbac/users") {
        return jsonResponse(
          401,
          {
            detail: "Could not validate credentials",
            code: "unauthorized",
            request_id: "req-users-401",
          },
          "req-users-401",
        );
      }

      if (method === "GET" && path === "/v1/rbac/roles") {
        return jsonResponse(200, []);
      }

      throw new Error(`Unhandled request: ${method} ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderAdminUsersPage();

    expect(await screen.findByRole("heading", { name: t("admin.common.error.title") })).toBeInTheDocument();
    expect(await screen.findByText(/Could not validate credentials/)).toBeInTheDocument();
    expect(getAccessToken()).toBeNull();
  });

  it("shows generic ui error for non-api exceptions", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const requestUrl = toRequestUrl(input);
      const method = init?.method ?? "GET";
      const path = requestUrl.pathname;

      if (method === "GET" && path === "/v1/rbac/users") {
        return jsonResponse(200, [{ id: "invalid" }]);
      }

      if (method === "GET" && path === "/v1/rbac/roles") {
        return jsonResponse(200, []);
      }

      throw new Error(`Unhandled request: ${method} ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderAdminUsersPage();

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
