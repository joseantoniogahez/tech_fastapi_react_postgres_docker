import { ApiContractError } from "@/shared/api/contracts";
import { buildApiUrl } from "@/shared/api/env";
import {
  CURRENT_USER_ENDPOINT_PATH,
  loginWithCredentials,
  logout,
  readCurrentUser,
  registerUser,
  resolveSessionUser,
  updateCurrentUser,
  REGISTER_USER_ENDPOINT_PATH,
  TOKEN_ENDPOINT_PATH,
} from "@/shared/auth/session";
import { getAccessToken, setAccessToken } from "@/shared/auth/storage";

describe("session client", () => {
  it("submits login with form payload and stores token", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          access_token: "fresh-token",
          token_type: "bearer",
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    await loginWithCredentials({ username: "admin", password: "{{password}}" });

    const [url, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(buildApiUrl(TOKEN_ENDPOINT_PATH));
    expect(request.method).toBe("POST");
    expect(new Headers(request.headers).get("Content-Type")).toBe(
      "application/x-www-form-urlencoded",
    );
    const body = request.body as URLSearchParams;
    expect(body.get("username")).toBe("admin");
    expect(body.get("password")).toBe("{{password}}");
    expect(getAccessToken()).toBe("fresh-token");
  });

  it("submits registration without auth header and parses the created user", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: () =>
        Promise.resolve({
          id: 5,
          username: "new_user",
          disabled: false,
          permissions: [],
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    const registeredUser = await registerUser({
      username: " new_user ",
      password: "StrongPass1", // pragma: allowlist secret
    });

    const [url, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(buildApiUrl(REGISTER_USER_ENDPOINT_PATH));
    expect(request.method).toBe("POST");
    expect(new Headers(request.headers).get("Content-Type")).toBe("application/json");
    expect(new Headers(request.headers).get("Authorization")).toBeNull();
    expect(request.body).toBe(
      JSON.stringify({
        username: " new_user ",
        password: "StrongPass1", // pragma: allowlist secret
      }),
    );
    expect(registeredUser).toEqual({
      id: 5,
      username: "new_user",
      disabled: false,
      permissions: [],
    });
  });

  it("submits current-user update with bearer auth", async () => {
    setAccessToken("valid-token");
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          id: 1,
          username: "updated_user",
          disabled: false,
          permissions: ["users:manage"],
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    const updatedUser = await updateCurrentUser({
      username: "updated_user",
      current_password: "CurrentPass1", // pragma: allowlist secret
      new_password: "NextPass2", // pragma: allowlist secret
    });

    const [url, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(buildApiUrl(CURRENT_USER_ENDPOINT_PATH));
    expect(request.method).toBe("PATCH");
    expect(new Headers(request.headers).get("Content-Type")).toBe("application/json");
    expect(new Headers(request.headers).get("Authorization")).toBe("Bearer valid-token");
    expect(request.body).toBe(
      JSON.stringify({
        username: "updated_user",
        current_password: "CurrentPass1", // pragma: allowlist secret
        new_password: "NextPass2", // pragma: allowlist secret
      }),
    );
    expect(updatedUser).toEqual({
      id: 1,
      username: "updated_user",
      disabled: false,
      permissions: ["users:manage"],
    });
  });

  it("clears invalid token when /users/me responds 401", async () => {
    setAccessToken("expired-token");
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: () =>
        Promise.resolve({
          detail: "Could not validate credentials",
          code: "unauthorized",
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    const user = await resolveSessionUser();

    expect(user).toBeNull();
    expect(getAccessToken()).toBeNull();
  });

  it("raises contract error when /users/me payload is invalid", async () => {
    setAccessToken("valid-token");
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
        json: () =>
          Promise.resolve({
          id: "1",
          username: "admin",
          disabled: false,
          permissions: [],
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    await expect(readCurrentUser()).rejects.toBeInstanceOf(ApiContractError);
  });

  it("clears token on logout", () => {
    setAccessToken("valid-token");

    logout();

    expect(getAccessToken()).toBeNull();
  });
});
