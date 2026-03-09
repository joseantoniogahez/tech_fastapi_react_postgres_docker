import { ApiContractError } from "@/shared/api/contracts";
import { buildApiUrl } from "@/shared/api/env";
import {
  loginWithCredentials,
  logout,
  readCurrentUser,
  resolveSessionUser,
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
    expect(url).toBe(buildApiUrl("/token"));
    expect(request.method).toBe("POST");
    expect(new Headers(request.headers).get("Content-Type")).toBe(
      "application/x-www-form-urlencoded",
    );
    const body = request.body as URLSearchParams;
    expect(body.get("username")).toBe("admin");
    expect(body.get("password")).toBe("{{password}}");
    expect(getAccessToken()).toBe("fresh-token");
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
