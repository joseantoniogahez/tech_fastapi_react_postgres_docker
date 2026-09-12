import {
  emitObservabilityEvent,
  sanitizeObservabilityValue,
} from "@/shared/observability/events";

describe("frontend observability events", () => {
  it("emits structured error events with request correlation", () => {
    const errorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => undefined);

    emitObservabilityEvent({
      event_name: "api.request.response_error",
      level: "error",
      request_id: "req-123",
      context: {
        method: "GET",
        path: "/users/me",
      },
    });

    expect(errorSpy).toHaveBeenCalledTimes(1);
    expect(errorSpy.mock.calls[0]?.[1]).toMatchObject({
      event_name: "api.request.response_error",
      level: "error",
      request_id: "req-123",
    });
    expect(errorSpy.mock.calls[0]?.[1]).toHaveProperty("timestamp");
  });

  it("redacts sensitive fields in event context", () => {
    const infoSpy = vi
      .spyOn(console, "info")
      .mockImplementation(() => undefined);

    emitObservabilityEvent({
      event_name: "runtime.error",
      level: "info",
      context: {
        authorization: "Bearer secret",
        nested: {
          password: "{{password}}",
        },
      },
    });

    expect(infoSpy.mock.calls[0]?.[1]).toMatchObject({
      context: {
        authorization: "[redacted]",
        nested: {
          password: "[redacted]",
        },
      },
    });
  });

  it("emits warn-level events and redacts array payload fields", () => {
    const warnSpy = vi
      .spyOn(console, "warn")
      .mockImplementation(() => undefined);

    emitObservabilityEvent({
      event_name: "runtime.unhandled_rejection",
      level: "warn",
      context: {
        attempts: [
          {
            token: "secret-token",
          },
        ],
      },
    });

    expect(warnSpy).toHaveBeenCalledTimes(1);
    expect(warnSpy.mock.calls[0]?.[1]).toMatchObject({
      event_name: "runtime.unhandled_rejection",
      level: "warn",
      context: {
        attempts: [
          {
            token: "[redacted]",
          },
        ],
      },
    });
  });

  it("recursively redacts without flattening arrays, objects, or repeated values", () => {
    const repeated = {
      refresh_token: "private-refresh-token",
      label: "preserved",
    };
    const context: Record<string, unknown> = {
      profile: {
        refresh_token: "private-refresh-token",
        attempts: [
          {
            token: "private-token",
            status: 401,
          },
        ],
      },
      repeated: [repeated, repeated],
    };

    expect(sanitizeObservabilityValue(context)).toEqual({
      profile: {
        refresh_token: "[redacted]",
        attempts: [
          {
            token: "[redacted]",
            status: 401,
          },
        ],
      },
      repeated: [
        { refresh_token: "[redacted]", label: "preserved" },
        { refresh_token: "[redacted]", label: "preserved" },
      ],
    });
    expect(repeated.refresh_token).toBe("private-refresh-token");
  });
});
