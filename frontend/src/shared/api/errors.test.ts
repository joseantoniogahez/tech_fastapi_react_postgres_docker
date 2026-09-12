import {
  ApiError,
  appendRequestIdDiagnostic,
  getApiErrorRequestId,
  hasApiErrorCause,
  parseApiError,
} from "@/shared/api/errors";

describe("api errors", () => {
  it("extracts request id from response header", async () => {
    const response = new Response(
      JSON.stringify({
        detail: "Backend error",
        code: "internal_error",
        request_id: "req-payload-must-not-win",
      }),
      {
        status: 500,
        headers: {
          "Content-Type": "application/json",
          "X-Request-ID": "req-header-123",
        },
      },
    );

    const error = await parseApiError(response);

    expect(error).toBeInstanceOf(ApiError);
    expect(error.message).toBe("Backend error");
    expect(error.code).toBe("internal_error");
    expect(error.requestId).toBe("req-header-123");
  });

  it("extracts request id from payload when header is missing", async () => {
    const response = new Response(
      JSON.stringify({
        detail: "Validation error",
        code: "invalid_input",
        request_id: "req-payload-456",
      }),
      {
        status: 400,
        headers: {
          "Content-Type": "application/json",
        },
      },
    );

    const error = await parseApiError(response);

    expect(error.requestId).toBe("req-payload-456");
  });

  it("appends request id diagnostic to message", () => {
    expect(appendRequestIdDiagnostic("Could not validate credentials", "req-789")).toBe(
      "Could not validate credentials (request_id=req-789)",
    );
    expect(appendRequestIdDiagnostic("Could not validate credentials", null)).toBe("Could not validate credentials");
  });

  it("rejects malformed property types without throwing or trusting them", async () => {
    const response = new Response(
      JSON.stringify({
        detail: 42,
        code: ["internal_error"],
        request_id: { value: "req-untrusted" },
      }),
      {
        status: 502,
        statusText: "Bad Gateway",
        headers: {
          "Content-Type": "application/json",
        },
      },
    );

    const error = await parseApiError(response);

    expect(error).toMatchObject({
      message: "Bad Gateway",
      status: 502,
      code: undefined,
      requestId: undefined,
    });
  });

  it("falls back safely when the response body is invalid JSON", async () => {
    const response = new Response("not-json", {
      status: 500,
      statusText: "",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const error = await parseApiError(response);

    expect(error).toMatchObject({
      message: "Error de comunicacion con el servidor",
      status: 500,
      code: undefined,
      requestId: undefined,
    });
  });

  it("ignores non-object JSON error payloads", async () => {
    const response = new Response(JSON.stringify(["unexpected"]), {
      status: 400,
      statusText: "Invalid response",
    });

    await expect(parseApiError(response)).resolves.toMatchObject({
      message: "Invalid response",
      code: undefined,
      requestId: undefined,
    });
  });

  it("returns request correlation for direct, wrapped, and nested ApiError causes", () => {
    const apiError = new ApiError("Error", 500, "internal_error", "req-999");
    const wrappedError = new Error("wrapped", { cause: apiError });
    const nestedError = new Error("nested", { cause: new Error("middle", { cause: wrappedError }) });

    expect(getApiErrorRequestId(apiError)).toBe("req-999");
    expect(getApiErrorRequestId(wrappedError)).toBe("req-999");
    expect(getApiErrorRequestId(nestedError)).toBe("req-999");
    expect(hasApiErrorCause(apiError)).toBe(true);
    expect(hasApiErrorCause(wrappedError)).toBe(true);
    expect(hasApiErrorCause(nestedError)).toBe(true);
  });

  it("stops safely on cyclic and over-depth cause chains", () => {
    const first = new Error("first");
    const second = new Error("second", { cause: first });
    Object.defineProperty(first, "cause", { value: second, configurable: true });

    let overDepth: Error = new ApiError("too deep", 500, "internal_error", "req-too-deep");
    for (let index = 0; index < 9; index += 1) {
      overDepth = new Error(`wrapper-${index}`, { cause: overDepth });
    }

    expect(getApiErrorRequestId(first)).toBeNull();
    expect(hasApiErrorCause(first)).toBe(false);
    expect(getApiErrorRequestId(overDepth)).toBeNull();
    expect(hasApiErrorCause(overDepth)).toBe(false);
    expect(getApiErrorRequestId(new Error("Other"))).toBeNull();
  });
});
