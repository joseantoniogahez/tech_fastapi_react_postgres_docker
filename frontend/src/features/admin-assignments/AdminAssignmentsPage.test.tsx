import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { createQueryClient } from "@/app/query-client";
import { AdminAssignmentsPage } from "@/features/admin-assignments/AdminAssignmentsPage";
import { SESSION_QUERY_KEY } from "@/shared/auth/session";
import { IAM_PERMISSION } from "@/shared/iam/contracts";
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

const renderAdminAssignmentsPage = (
  permissions: string[] = [
    IAM_PERMISSION.USER_ROLES_MANAGE,
    IAM_PERMISSION.USERS_MANAGE,
    IAM_PERMISSION.ROLES_MANAGE,
  ],
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
      <AdminAssignmentsPage />
    </QueryClientProvider>,
  );
};

describe("AdminAssignmentsPage", () => {
  it("loads direct assignment views and uses dedicated assign/remove endpoints", async () => {
    const users: MockUser[] = [
      {
        id: 1,
        username: "admin",
        disabled: false,
        role_ids: [],
      },
      {
        id: 2,
        username: "reader_user",
        disabled: false,
        role_ids: [2],
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
    let assignmentsByUserId: Record<number, number[]> = {
      2: [2],
    };

    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const requestUrl = toRequestUrl(input);
      const method = init?.method ?? "GET";
      const path = requestUrl.pathname;

      const buildAssignedRoles = (userId: number) =>
        roles
          .filter((role) => (assignmentsByUserId[userId] ?? []).includes(role.id))
          .map((role) => ({ id: role.id, name: role.name }));

      const buildAssignedUsers = (roleId: number) =>
        users
          .filter((user) => (assignmentsByUserId[user.id] ?? []).includes(roleId))
          .map((user) => ({ id: user.id, username: user.username, disabled: user.disabled }));

      if (method === "GET" && path === "/v1/rbac/users") {
        return jsonResponse(200, users);
      }

      if (method === "GET" && path === "/v1/rbac/roles") {
        return jsonResponse(200, roles);
      }

      if (method === "GET" && path === "/v1/rbac/users/2/roles") {
        return jsonResponse(200, buildAssignedRoles(2));
      }

      if (method === "GET" && path === "/v1/rbac/roles/1/users") {
        return jsonResponse(200, buildAssignedUsers(1));
      }

      if (method === "GET" && path === "/v1/rbac/roles/2/users") {
        return jsonResponse(200, buildAssignedUsers(2));
      }

      if (method === "PUT" && path === "/v1/rbac/users/2/roles/1") {
        assignmentsByUserId = {
          ...assignmentsByUserId,
          2: [...new Set([...(assignmentsByUserId[2] ?? []), 1])],
        };
        return jsonResponse(200, { user_id: 2, role_id: 1 });
      }

      if (method === "DELETE" && path === "/v1/rbac/users/2/roles/1") {
        assignmentsByUserId = {
          ...assignmentsByUserId,
          2: (assignmentsByUserId[2] ?? []).filter((roleId) => roleId !== 1),
        };
        return jsonResponse(204, null);
      }

      throw new Error(`Unhandled request: ${method} ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    renderAdminAssignmentsPage();

    expect(await screen.findByRole("heading", { name: t("admin.as.title") })).toBeInTheDocument();

    await user.selectOptions(await screen.findByLabelText(t("admin.users.columns.username")), "2");
    await user.selectOptions(await screen.findByLabelText(t("admin.users.columns.roles")), "2");

    const userRolesCard = screen.getByRole("heading", { name: t("admin.as.uTitle") }).closest("article");
    const roleUsersCard = screen.getByRole("heading", { name: t("admin.as.rTitle") }).closest("article");
    expect(userRolesCard).not.toBeNull();
    expect(roleUsersCard).not.toBeNull();
    if (!userRolesCard || !roleUsersCard) {
      throw new Error("Expected direct assignment cards");
    }

    expect(await within(userRolesCard).findByText("reader_role")).toBeInTheDocument();
    expect(await within(roleUsersCard).findByText("reader_user")).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText(t("admin.users.columns.roles")), "1");
    await user.click(screen.getByRole("button", { name: t("admin.as.submit") }));

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some((call) => {
          const requestUrl = toRequestUrl(call[0]);
          const request = call[1];
          return requestUrl.pathname === "/v1/rbac/users/2/roles/1" && request?.method === "PUT";
        }),
      ).toBe(true);
    });

    expect(await within(userRolesCard).findByText("admin_role")).toBeInTheDocument();
    expect(await within(roleUsersCard).findByText("reader_user")).toBeInTheDocument();

    const assignedUserRow = within(roleUsersCard).getByText("reader_user").closest("li");
    expect(assignedUserRow).not.toBeNull();
    if (!assignedUserRow) {
      throw new Error("Expected assigned user row");
    }

    await user.click(within(assignedUserRow).getByRole("button", { name: t("admin.roles.permissions.remove") }));

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.filter((call) => {
          const requestUrl = toRequestUrl(call[0]);
          const request = call[1];
          return requestUrl.pathname === "/v1/rbac/users/2/roles/1" && request?.method === "DELETE";
        }),
      ).toHaveLength(1);
    });

    await waitFor(() => {
      expect(within(userRolesCard).queryByText("admin_role")).not.toBeInTheDocument();
    });
    await waitFor(() => {
      expect(within(roleUsersCard).getByText(t("admin.as.rEmpty"))).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: t("admin.as.submit") }));

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.filter((call) => {
          const requestUrl = toRequestUrl(call[0]);
          const request = call[1];
          return requestUrl.pathname === "/v1/rbac/users/2/roles/1" && request?.method === "PUT";
        }),
      ).toHaveLength(2);
    });

    expect(await within(userRolesCard).findByText("admin_role")).toBeInTheDocument();

    const assignedRoleRow = within(userRolesCard).getByText("admin_role").closest("li");
    expect(assignedRoleRow).not.toBeNull();
    if (!assignedRoleRow) {
      throw new Error("Expected assigned role row");
    }

    await user.click(within(assignedRoleRow).getByRole("button", { name: t("admin.roles.permissions.remove") }));

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some((call) => {
          const requestUrl = toRequestUrl(call[0]);
          const request = call[1];
          return requestUrl.pathname === "/v1/rbac/users/2/roles/1" && request?.method === "DELETE";
        }),
      ).toBe(true);
    });

    await waitFor(() => {
      expect(within(userRolesCard).queryByText("admin_role")).not.toBeInTheDocument();
    });
    await waitFor(() => {
      expect(within(roleUsersCard).getByText(t("admin.as.rEmpty"))).toBeInTheDocument();
    });
  });

  it("falls back to manual ids and surfaces request-id diagnostics for direct read failures", async () => {
    const requestPaths: string[] = [];
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const requestUrl = toRequestUrl(input);
      const method = init?.method ?? "GET";
      const path = requestUrl.pathname;
      requestPaths.push(path);

      if (method === "GET" && /^\/v1\/rbac\/users\/\d+\/roles$/.test(path)) {
        return jsonResponse(
          404,
          {
            detail: "User not found",
            code: "not_found",
            request_id: "req-assignments-user-404",
          },
          "req-assignments-user-404",
        );
      }

      if (method === "GET" && /^\/v1\/rbac\/roles\/\d+\/users$/.test(path)) {
        return jsonResponse(200, []);
      }

      throw new Error(`Unhandled request: ${method} ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    renderAdminAssignmentsPage([IAM_PERMISSION.USER_ROLES_MANAGE]);

    expect(await screen.findByRole("heading", { name: t("admin.as.title") })).toBeInTheDocument();
    await user.type(screen.getByLabelText(t("admin.as.uid")), "999");
    await user.type(screen.getByLabelText(t("admin.as.rid")), "888");

    expect(await screen.findByText(/request_id=req-assignments-user-404/)).toBeInTheDocument();
    expect(requestPaths).not.toContain("/v1/rbac/users");
    expect(requestPaths).not.toContain("/v1/rbac/roles");
  });
});
