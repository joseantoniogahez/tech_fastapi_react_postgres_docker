import {
  ACCESS_TOKEN_LEGACY_STORAGE_KEY,
  ACCESS_TOKEN_STORAGE_KEY,
  LOGGED_OUT_STORAGE_KEY,
  clearAccessToken,
  getAccessToken,
  revokeAccessToken,
  setAccessToken,
} from "@/shared/auth/storage";

describe("token storage", () => {
  it("stores and retrieves access token from session storage", () => {
    setAccessToken("token-123");

    expect(sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)).toBe("token-123");
    expect(getAccessToken()).toBe("token-123");
  });

  it("migrates legacy localStorage token into session storage", () => {
    localStorage.setItem(ACCESS_TOKEN_LEGACY_STORAGE_KEY, "legacy-token");

    expect(getAccessToken()).toBe("legacy-token");
    expect(localStorage.getItem(ACCESS_TOKEN_LEGACY_STORAGE_KEY)).toBeNull();
    expect(sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)).toBe("legacy-token");
  });

  it("removes token on clear from both storages", () => {
    localStorage.setItem(ACCESS_TOKEN_LEGACY_STORAGE_KEY, "legacy-token");
    setAccessToken("token-123");

    clearAccessToken();

    expect(getAccessToken()).toBeNull();
    expect(sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)).toBeNull();
    expect(localStorage.getItem(ACCESS_TOKEN_LEGACY_STORAGE_KEY)).toBeNull();
    expect(localStorage.getItem(LOGGED_OUT_STORAGE_KEY)).toBeNull();
  });

  it("rejects a session token restored after logout until a new login stores a token", () => {
    revokeAccessToken();
    sessionStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, "restored-history-token");

    expect(getAccessToken()).toBeNull();
    expect(sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)).toBeNull();

    setAccessToken("fresh-login-token");
    expect(localStorage.getItem(LOGGED_OUT_STORAGE_KEY)).toBeNull();
    expect(getAccessToken()).toBe("fresh-login-token");
  });
});
