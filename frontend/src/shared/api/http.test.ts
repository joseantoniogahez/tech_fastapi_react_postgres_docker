import { buildApiUrl } from "@/shared/api/env";
import { ApiError } from "@/shared/api/errors";
import { apiNoContentRequest, apiRequest, toDiagnosticApiPath } from "@/shared/api/http";

describe("API request diagnostics", () => {
  it.each([
    ["/users/me", "/users/me"],
    ["/search?name=Ana&phone=5551234567#private-fragment", "/search"],
    ["/search#private-fragment?token=secret-value", "/search"],
    ["?token=secret-value", ""],
  ])("maps %s to a query-free and fragment-free path", (path, expected) => {
    expect(toDiagnosticApiPath(path)).toBe(expected);
  });

  it("keeps sensitive query, fragment, and body values out of network-error events", async () => {
    const path = "/search?name=Ana%20Lopez&phone=5551234567&token=secret-value#private-fragment";
    const fetchMock = vi.fn().mockRejectedValue(new Error("Network down"));
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      apiRequest(path, {
        method: "POST",
        withAuth: false,
        body: JSON.stringify({ token: "body-secret-value" }),
        parse: (payload) => payload,
      }),
    ).rejects.toMatchObject({ status: 0, code: "network_error" });

    expect(fetchMock).toHaveBeenCalledWith(
      buildApiUrl(path),
      expect.objectContaining({ method: "POST" }),
    );
    expect(errorSpy.mock.calls[0]?.[1]).toMatchObject({
      event_name: "api.request.network_error",
      context: {
        path: "/search",
      },
    });

    const emittedPayload = JSON.stringify(errorSpy.mock.calls);
    for (const sensitiveValue of [
      "Ana%20Lopez",
      "5551234567",
      "secret-value",
      "private-fragment",
      "body-secret-value",
    ]) {
      expect(emittedPayload).not.toContain(sensitiveValue);
    }
  });

  it("uses a caller-owned static path for dynamic response-error diagnostics", async () => {
    const path = "/rbac/users/987654321?name=Private#private-fragment";
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found",
      headers: new Headers({ "X-Request-ID": "req-dynamic-404" }),
      json: () => Promise.resolve({ detail: "Not found", code: "not_found" }),
    } satisfies Partial<Response>);
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      apiRequest(path, {
        diagnosticPath: "/rbac/users/{user_id}?ignored=true#ignored",
        parse: (payload) => payload,
      }),
    ).rejects.toMatchObject({ status: 404, requestId: "req-dynamic-404" });

    expect(fetchMock).toHaveBeenCalledWith(buildApiUrl(path), expect.any(Object));
    expect(errorSpy.mock.calls[0]?.[1]).toMatchObject({
      event_name: "api.request.response_error",
      request_id: "req-dynamic-404",
      context: {
        path: "/rbac/users/{user_id}",
        status: 404,
      },
    });
    expect(JSON.stringify(errorSpy.mock.calls)).not.toContain("987654321");
  });

  it("parses successful JSON through the required runtime parser", async () => {
    const parser = vi.fn((payload: unknown) => {
      if (typeof payload !== "object" || payload === null || !("name" in payload)) {
        throw new Error("invalid fixture");
      }
      return (payload as { name: unknown }).name;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ name: "validated" }),
      } satisfies Partial<Response>),
    );

    await expect(apiRequest("/validated", { parse: parser })).resolves.toBe("validated");
    expect(parser).toHaveBeenCalledWith({ name: "validated" });
  });

  it.each([
    {
      name: "invalid JSON",
      json: () => Promise.reject(new SyntaxError("private malformed response")),
      parse: (payload: unknown) => payload,
    },
    {
      name: "parser failure",
      json: () => Promise.resolve({ token: "response-secret" }),
      parse: () => {
        throw new Error("private parser failure response-secret");
      },
    },
  ])("normalizes $name without leaking parser or response details", async ({ json, parse }) => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ "X-Request-ID": "req-invalid-response" }),
        json,
      } satisfies Partial<Response>),
    );

    await expect(apiRequest("/validated", { parse })).rejects.toMatchObject({
      message: "Respuesta invalida del servidor",
      status: 200,
      code: "invalid_response",
      requestId: "req-invalid-response",
    } satisfies Partial<ApiError>);

    const emittedPayload = JSON.stringify(errorSpy.mock.calls);
    expect(emittedPayload).toContain("api.request.response_error");
    expect(emittedPayload).toContain("req-invalid-response");
    expect(emittedPayload).not.toContain("private malformed response");
    expect(emittedPayload).not.toContain("private parser failure");
    expect(emittedPayload).not.toContain("response-secret");
  });

  it("rejects no-content from the JSON path before calling its parser", async () => {
    const parser = vi.fn((payload: unknown) => payload);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 204,
        headers: new Headers({ "X-Request-ID": "req-unexpected-204" }),
      } satisfies Partial<Response>),
    );

    await expect(apiRequest("/validated", { parse: parser })).rejects.toMatchObject({
      status: 204,
      code: "invalid_response",
      requestId: "req-unexpected-204",
    } satisfies Partial<ApiError>);
    expect(parser).not.toHaveBeenCalled();
  });

  it("accepts only 204 through the explicit no-content path", async () => {
    const json = vi.fn();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 204,
        headers: new Headers(),
        json,
      } satisfies Partial<Response>),
    );

    await expect(apiNoContentRequest("/validated", { method: "DELETE" })).resolves.toBeUndefined();
    expect(json).not.toHaveBeenCalled();
  });

  it("rejects an unexpected payload response from the no-content path", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ "X-Request-ID": "req-unexpected-content" }),
        json: () => Promise.resolve({ detail: "must not be consumed" }),
      } satisfies Partial<Response>),
    );

    await expect(apiNoContentRequest("/validated", { method: "DELETE" })).rejects.toMatchObject({
      message: "Respuesta invalida del servidor",
      status: 200,
      code: "invalid_response",
      requestId: "req-unexpected-content",
    } satisfies Partial<ApiError>);
  });

  it("requires a runtime parser for every JSON request at compile time", () => {
    const verifyParserType = (): void => {
      // @ts-expect-error JSON requests require an explicit runtime parser.
      void apiRequest<unknown>("/validated", {});
    };

    expect(verifyParserType).toBeTypeOf("function");
  });
});
