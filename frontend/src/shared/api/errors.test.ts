import {
  ApiError,
  appendRequestIdDiagnostic,
  getApiErrorRequestId,
  parseApiError,
} from "@/shared/api/errors";

describe("api errors", () => {
  it("extracts request id from response header", async () => {
    const response = new Response(
      JSON.stringify({
        detail: "Backend error",
        code: "internal_error",
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

  it("returns request id only for ApiError", () => {
    expect(getApiErrorRequestId(new ApiError("Error", 500, "internal_error", "req-999"))).toBe("req-999");
    expect(getApiErrorRequestId(new Error("Other"))).toBeNull();
  });
});
