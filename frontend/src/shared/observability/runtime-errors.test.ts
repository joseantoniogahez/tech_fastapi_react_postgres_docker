import { ApiError } from "@/shared/api/errors";
import {
  installGlobalRuntimeErrorHandlers,
  resetRuntimeErrorHandlersForTests,
} from "@/shared/observability/runtime-errors";

describe("global runtime error handlers", () => {
  beforeEach(() => {
    resetRuntimeErrorHandlersForTests();
  });

  afterEach(() => {
    resetRuntimeErrorHandlersForTests();
    vi.restoreAllMocks();
  });

  it("captures window runtime errors and emits structured diagnostics", () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);

    installGlobalRuntimeErrorHandlers();
    installGlobalRuntimeErrorHandlers();

    const runtimeError = new Error("runtime failure");
    window.dispatchEvent(
      new ErrorEvent("error", {
        message: runtimeError.message,
        error: runtimeError,
        filename: "main.tsx",
        lineno: 12,
        colno: 4,
      }),
    );

    expect(errorSpy).toHaveBeenCalledTimes(1);
    expect(errorSpy.mock.calls[0]?.[1]).toMatchObject({
      event_name: "runtime.error",
      level: "error",
      request_id: null,
      context: {
        message: "runtime failure",
        filename: "main.tsx",
      },
    });
  });

  it("captures unhandled rejection and preserves ApiError request correlation", () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    installGlobalRuntimeErrorHandlers();

    const rejectionReason = new ApiError("request failed", 500, "internal_error", "req-runtime-500");
    const rejectionEvent = new Event("unhandledrejection") as PromiseRejectionEvent;
    Object.defineProperty(rejectionEvent, "reason", {
      value: rejectionReason,
      configurable: true,
    });

    window.dispatchEvent(rejectionEvent);

    expect(errorSpy).toHaveBeenCalledTimes(1);
    expect(errorSpy.mock.calls[0]?.[1]).toMatchObject({
      event_name: "runtime.unhandled_rejection",
      request_id: "req-runtime-500",
      context: {
        is_api_error: true,
      },
    });
  });

  it("normalizes non-error runtime payloads to string or unknown fallback", () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    installGlobalRuntimeErrorHandlers();

    window.dispatchEvent(
      new ErrorEvent("error", {
        message: "string-only-runtime-message",
      }),
    );

    const unknownReasonEvent = new Event("unhandledrejection") as PromiseRejectionEvent;
    Object.defineProperty(unknownReasonEvent, "reason", {
      value: { detail: "opaque-object" },
      configurable: true,
    });
    window.dispatchEvent(unknownReasonEvent);

    expect(errorSpy).toHaveBeenCalledTimes(2);
    expect(errorSpy.mock.calls[0]?.[1]).toMatchObject({
      event_name: "runtime.error",
      context: {
        message: "string-only-runtime-message",
      },
    });
    expect(errorSpy.mock.calls[1]?.[1]).toMatchObject({
      event_name: "runtime.unhandled_rejection",
      context: {
        reason: "Unknown runtime error",
        is_api_error: false,
      },
    });
  });
});
