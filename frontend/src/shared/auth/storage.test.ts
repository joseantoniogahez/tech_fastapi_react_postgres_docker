import {
  ACCESS_TOKEN_LEGACY_STORAGE_KEY,
  ACCESS_TOKEN_STORAGE_KEY,
  clearAccessToken,
  getAccessToken,
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
  });
});
