import { buildApiUrl, getApiBaseUrl } from "@/app/services/api";

describe("API URL helpers", () => {
  const previousApiOrigin = process.env.NEXT_PUBLIC_API_ORIGIN;
  const previousApiBasePath = process.env.NEXT_PUBLIC_API_BASE_PATH;

  afterEach(() => {
    if (previousApiOrigin === undefined) delete process.env.NEXT_PUBLIC_API_ORIGIN;
    else process.env.NEXT_PUBLIC_API_ORIGIN = previousApiOrigin;

    if (previousApiBasePath === undefined) delete process.env.NEXT_PUBLIC_API_BASE_PATH;
    else process.env.NEXT_PUBLIC_API_BASE_PATH = previousApiBasePath;
  });

  it("uses NEXT_PUBLIC_API_ORIGIN and NEXT_PUBLIC_API_BASE_PATH", () => {
    process.env.NEXT_PUBLIC_API_ORIGIN = "http://localhost:8000/";
    process.env.NEXT_PUBLIC_API_BASE_PATH = "/api/";

    expect(getApiBaseUrl()).toBe("http://localhost:8000/api");
  });

  it("uses /api when env vars are not defined", () => {
    delete process.env.NEXT_PUBLIC_API_ORIGIN;
    delete process.env.NEXT_PUBLIC_API_BASE_PATH;

    expect(getApiBaseUrl()).toBe("/api");
  });

  it("supports root API path", () => {
    process.env.NEXT_PUBLIC_API_ORIGIN = "http://localhost:8000";
    process.env.NEXT_PUBLIC_API_BASE_PATH = "/";

    expect(getApiBaseUrl()).toBe("http://localhost:8000");
  });

  it("builds endpoint URLs with normalized path", () => {
    process.env.NEXT_PUBLIC_API_ORIGIN = "http://localhost:8000/";
    process.env.NEXT_PUBLIC_API_BASE_PATH = "/api/";

    expect(buildApiUrl("books/")).toBe("http://localhost:8000/api/books/");
  });
});
