import { buildApiUrl } from "@/shared/api/env";
import { ApiError } from "@/shared/api/errors";
import {
  assignRbacRolePermission,
  createAdminUser,
  readAdminUser,
  readAdminUsers,
  removeRbacRoleInheritance,
  removeRbacRolePermission,
  softDeleteAdminUser,
  updateRbacRole,
} from "@/shared/rbac/admin";
import { getAccessToken, setAccessToken } from "@/shared/auth/storage";

const errorResponse = (
  status: number,
  payload: { detail: string; code: string; request_id?: string },
): Partial<Response> => ({
  ok: false,
  status,
  statusText: "Error",
  headers: {
    get: (name: string) => (name.toLowerCase() === "x-request-id" ? (payload.request_id ?? null) : null),
  },
  json: () => Promise.resolve(payload),
});

describe("rbac admin client", () => {
  it("reads admin users list", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          {
            id: 1,
            username: "admin",
            disabled: false,
            role_ids: [1],
          },
        ]),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    const users = await readAdminUsers();

    expect(users).toHaveLength(1);
    const [url, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(buildApiUrl("/rbac/users"));
    expect(request.method).toBeUndefined();
  });

  it("reads single admin user by id", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          id: 7,
          username: "auditor",
          disabled: false,
          role_ids: [2],
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    const user = await readAdminUser(7);

    expect(user.username).toBe("auditor");
    const [url, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(buildApiUrl("/rbac/users/7"));
    expect(request.method).toBeUndefined();
  });

  it("creates user with json payload", async () => {
    setAccessToken("valid-token");
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: () =>
        Promise.resolve({
          id: 9,
          username: "ops_user",
          disabled: false,
          role_ids: [1, 2],
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    await createAdminUser({
      username: "ops_user",
      password: "OpsUser123", // pragma: allowlist secret
      role_ids: [1, 2],
    });

    const [url, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(buildApiUrl("/rbac/users"));
    expect(request.method).toBe("POST");
    expect(new Headers(request.headers).get("Content-Type")).toBe("application/json");
    expect(new Headers(request.headers).get("Authorization")).toBe("Bearer valid-token");
    expect(request.body).toBe(
      JSON.stringify({ username: "ops_user", password: "OpsUser123", role_ids: [1, 2] }), // pragma: allowlist secret
    );
  });

  it("updates role with json payload", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          id: 2,
          name: "editor_role",
          permissions: [],
          parent_role_ids: [],
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    await updateRbacRole(2, { name: "editor_role" });

    const [url, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(buildApiUrl("/rbac/roles/2"));
    expect(request.method).toBe("PUT");
    expect(request.body).toBe(JSON.stringify({ name: "editor_role" }));
  });

  it("assigns role permission with default any scope", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          id: "users:manage",
          name: "Manage users",
          scope: "any",
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    await assignRbacRolePermission(2, "users:manage");

    const [, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(request.method).toBe("PUT");
    expect(request.body).toBe(JSON.stringify({ scope: "any" }));
  });

  it("sends delete for soft-delete admin user", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    await softDeleteAdminUser(5);

    const [url, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(buildApiUrl("/rbac/users/5"));
    expect(request.method).toBe("DELETE");
  });

  it("sends delete for role inheritance removal", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    await removeRbacRoleInheritance(3, 1);

    const [url, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(buildApiUrl("/rbac/roles/3/inherits/1"));
    expect(request.method).toBe("DELETE");
  });

  it("sends delete for role permission removal", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    await removeRbacRolePermission(3, "users:manage");

    const [url, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(buildApiUrl("/rbac/roles/3/permissions/users%3Amanage"));
    expect(request.method).toBe("DELETE");
  });

  it.each([
    {
      status: 400,
      code: "invalid_input",
      detail: "Invalid payload",
      requestId: "req-rbac-400",
    },
    {
      status: 403,
      code: "forbidden",
      detail: "Forbidden operation",
      requestId: "req-rbac-403",
    },
    {
      status: 404,
      code: "not_found",
      detail: "Resource not found",
      requestId: "req-rbac-404",
    },
    {
      status: 409,
      code: "conflict",
      detail: "Duplicate entity",
      requestId: "req-rbac-409",
    },
  ])(
    "surfaces normalized API error for status $status",
    async ({ status, code, detail, requestId }) => {
      const fetchMock = vi.fn().mockResolvedValue(
        errorResponse(status, {
          detail,
          code,
          request_id: requestId,
        }),
      );
      vi.stubGlobal("fetch", fetchMock);

      await expect(readAdminUsers()).rejects.toMatchObject({
        status,
        code,
        message: detail,
        requestId,
      } satisfies Partial<ApiError>);
    },
  );

  it("clears access token when RBAC endpoint returns 401", async () => {
    setAccessToken("expired-token");
    const fetchMock = vi.fn().mockResolvedValue(
      errorResponse(401, {
        detail: "Could not validate credentials",
        code: "unauthorized",
        request_id: "req-rbac-401",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(readAdminUsers()).rejects.toMatchObject({
      status: 401,
      code: "unauthorized",
      requestId: "req-rbac-401",
    } satisfies Partial<ApiError>);
    expect(getAccessToken()).toBeNull();
  });

  it("maps network failures to network_error API contract", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error("Network down"));
    vi.stubGlobal("fetch", fetchMock);

    await expect(readAdminUsers()).rejects.toMatchObject({
      status: 0,
      code: "network_error",
      message: "Error de comunicacion con el servidor",
    } satisfies Partial<ApiError>);
  });
});
