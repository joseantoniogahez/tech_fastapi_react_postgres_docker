import {
  ACCESS_TOKEN_STORAGE_KEY,
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from "@/shared/auth/storage";

describe("token storage", () => {
  it("stores and retrieves access token", () => {
    setAccessToken("token-123");

    expect(localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)).toBe("token-123");
    expect(getAccessToken()).toBe("token-123");
  });

  it("removes token on clear", () => {
    setAccessToken("token-123");

    clearAccessToken();

    expect(getAccessToken()).toBeNull();
  });
});
