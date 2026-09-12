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
    const sensitiveFilename = "https://app.example.test/main.tsx?token=private#fragment";
    window.dispatchEvent(
      new ErrorEvent("error", {
        message: runtimeError.message,
        error: runtimeError,
        filename: sensitiveFilename,
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
      },
    });
    expect(JSON.stringify(errorSpy.mock.calls)).not.toContain(sensitiveFilename);
    expect(JSON.stringify(errorSpy.mock.calls)).not.toContain("private");
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

  it("preserves ApiError diagnostics through wrapped and nested causes", () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    installGlobalRuntimeErrorHandlers();

    const apiError = new ApiError("request failed", 503, "service_unavailable", "req-nested-503");
    const wrappedReason = new Error("feature failed", { cause: apiError });
    const nestedReason = new Error("workflow failed", {
      cause: new Error("operation failed", { cause: wrappedReason }),
    });

    for (const reason of [wrappedReason, nestedReason]) {
      const rejectionEvent = new Event("unhandledrejection") as PromiseRejectionEvent;
      Object.defineProperty(rejectionEvent, "reason", {
        value: reason,
        configurable: true,
      });
      window.dispatchEvent(rejectionEvent);
    }

    expect(errorSpy).toHaveBeenCalledTimes(2);
    expect(errorSpy.mock.calls[0]?.[1]).toMatchObject({
      request_id: "req-nested-503",
      context: {
        reason: "feature failed",
        is_api_error: true,
      },
    });
    expect(errorSpy.mock.calls[1]?.[1]).toMatchObject({
      request_id: "req-nested-503",
      context: {
        reason: "workflow failed",
        is_api_error: true,
      },
    });
  });

  it("stops cyclic cause traversal without classifying it as an ApiError", () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    installGlobalRuntimeErrorHandlers();

    const first = new Error("first");
    const second = new Error("second", { cause: first });
    Object.defineProperty(first, "cause", { value: second, configurable: true });
    const rejectionEvent = new Event("unhandledrejection") as PromiseRejectionEvent;
    Object.defineProperty(rejectionEvent, "reason", {
      value: first,
      configurable: true,
    });

    window.dispatchEvent(rejectionEvent);

    expect(errorSpy.mock.calls[0]?.[1]).toMatchObject({
      request_id: null,
      context: {
        reason: "first",
        is_api_error: false,
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
