import { ApiContractError } from "@/shared/api/contracts";
import { parseAccessTokenResponse, parseAuthenticatedUser } from "@/shared/auth/contracts";

describe("auth contracts", () => {
  it("parses authenticated user payload", () => {
    expect(
      parseAuthenticatedUser({
        id: 1,
        username: "admin",
        disabled: false,
        permissions: ["users:manage"],
      }),
    ).toEqual({
      id: 1,
      username: "admin",
      disabled: false,
      permissions: ["users:manage"],
    });
  });

  it("rejects invalid authenticated user payload", () => {
    expect(() =>
      parseAuthenticatedUser({
        id: "1",
        username: "admin",
        disabled: false,
        permissions: ["users:manage"],
      }),
    ).toThrow(ApiContractError);
  });

  it("rejects authenticated user payload when permissions are missing", () => {
    expect(() =>
      parseAuthenticatedUser({
        id: 1,
        username: "admin",
        disabled: false,
      }),
    ).toThrow(ApiContractError);
  });

  it("parses access token payload", () => {
    expect(
      parseAccessTokenResponse({
        access_token: "token",
        token_type: "bearer",
      }),
    ).toEqual({
      access_token: "token",
      token_type: "bearer",
    });
  });

  it("rejects invalid token type", () => {
    expect(() =>
      parseAccessTokenResponse({
        access_token: "token",
        token_type: "Bearer",
      }),
    ).toThrow(ApiContractError);
  });
});
