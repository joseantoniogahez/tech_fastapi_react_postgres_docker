import {
  FrontendEnvError,
  buildApiUrl,
  getApiBaseUrl,
  readFrontendEnvConfig,
} from "@/shared/api/env";

describe("frontend env contracts", () => {
  it("uses defaults when build inputs are absent", () => {
    expect(readFrontendEnvConfig({})).toEqual({
      apiOrigin: "http://localhost:8000",
      apiBasePath: "/v1",
    });
  });

  it("canonicalizes the API origin and normalizes the independent base path", () => {
    const config = readFrontendEnvConfig({
      VITE_API_ORIGIN: " HTTPS://API.Example.COM:443/ ",
      VITE_API_BASE_PATH: "v1/",
    });

    expect(config.apiOrigin).toBe("https://api.example.com");
    expect(config.apiBasePath).toBe("/v1");
    expect(
      getApiBaseUrl({
        VITE_API_ORIGIN: "https://api.example.com/",
        VITE_API_BASE_PATH: "/v1/",
      }),
    ).toBe("https://api.example.com/v1");
  });

  it.each([
    ["malformed URL", "not-a-url"],
    ["unsupported protocol", "ftp://api.example.com"],
    ["username", "https://user@api.example.com"],
    ["password", "https://user:secret@api.example.com"], // pragma: allowlist secret
    ["non-root path", "https://api.example.com/v1"],
    ["query string", "https://api.example.com/?region=us"],
    ["empty query string", "https://api.example.com/?"],
    ["fragment", "https://api.example.com/#status"],
    ["empty fragment", "https://api.example.com/#"],
  ])("fails fast when API origin has a %s", (_case, apiOrigin) => {
    expect(() => readFrontendEnvConfig({ VITE_API_ORIGIN: apiOrigin })).toThrow(
      FrontendEnvError,
    );
  });

  it.each([
    ["VITE_API_ORIGIN", { VITE_API_ORIGIN: " " }],
    ["VITE_API_BASE_PATH", { VITE_API_BASE_PATH: " " }],
  ])("rejects an empty %s build input", (_field, env) => {
    expect(() => readFrontendEnvConfig(env)).toThrow(FrontendEnvError);
  });

  it.each([
    ["VITE_API_ORIGIN", { VITE_API_ORIGIN: 42 }],
    ["VITE_API_BASE_PATH", { VITE_API_BASE_PATH: false }],
  ])("rejects a non-string %s build input", (_field, env) => {
    expect(() => readFrontendEnvConfig(env)).toThrow(FrontendEnvError);
  });

  it("preserves non-default ports in the canonical origin", () => {
    expect(
      readFrontendEnvConfig({ VITE_API_ORIGIN: "http://API.Example.COM:8080/" })
        .apiOrigin,
    ).toBe("http://api.example.com:8080");
  });

  it("collapses a root API base path independently from the origin", () => {
    expect(readFrontendEnvConfig({ VITE_API_BASE_PATH: "/" }).apiBasePath).toBe(
      "",
    );
  });

  it("fails fast for invalid base path format", () => {
    expect(() =>
      readFrontendEnvConfig({
        VITE_API_ORIGIN: "https://api.example.com",
        VITE_API_BASE_PATH: "/bad path",
      }),
    ).toThrow(FrontendEnvError);
  });

  it("builds API URL from validated build-time config", () => {
    expect(
      buildApiUrl("/users/me", {
        VITE_API_ORIGIN: "https://api.example.com/",
        VITE_API_BASE_PATH: "/v1/",
      }),
    ).toBe("https://api.example.com/v1/users/me");
  });
});
