import { ApiError, getApiErrorRequestId } from "@/shared/api/errors";
import { emitObservabilityEvent } from "@/shared/observability/events";

let runtimeHandlersInstalled = false;
let runtimeErrorHandler: ((event: ErrorEvent) => void) | null = null;
let runtimeUnhandledRejectionHandler: ((event: PromiseRejectionEvent) => void) | null = null;

const resolveErrorMessage = (value: unknown): string => {
  if (value instanceof Error) {
    return value.message;
  }

  if (typeof value === "string") {
    return value;
  }

  return "Unknown runtime error";
};

export const installGlobalRuntimeErrorHandlers = (): void => {
  if (runtimeHandlersInstalled) {
    return;
  }

  runtimeErrorHandler = (event) => {
    const requestId = getApiErrorRequestId(event.error);
    emitObservabilityEvent({
      event_name: "runtime.error",
      level: "error",
      request_id: requestId,
      context: {
        message: resolveErrorMessage(event.error ?? event.message),
        filename: event.filename || null,
        lineno: event.lineno || null,
        colno: event.colno || null,
      },
    });
  };

  runtimeUnhandledRejectionHandler = (event) => {
    const reason: unknown = event.reason;
    const requestId = getApiErrorRequestId(reason);

    emitObservabilityEvent({
      event_name: "runtime.unhandled_rejection",
      level: "error",
      request_id: requestId,
      context: {
        reason: resolveErrorMessage(reason),
        is_api_error: reason instanceof ApiError,
      },
    });
  };

  window.addEventListener("error", runtimeErrorHandler);
  window.addEventListener("unhandledrejection", runtimeUnhandledRejectionHandler);

  runtimeHandlersInstalled = true;
};

export const resetRuntimeErrorHandlersForTests = (): void => {
  if (runtimeErrorHandler) {
    window.removeEventListener("error", runtimeErrorHandler);
  }

  if (runtimeUnhandledRejectionHandler) {
    window.removeEventListener("unhandledrejection", runtimeUnhandledRejectionHandler);
  }

  runtimeErrorHandler = null;
  runtimeUnhandledRejectionHandler = null;
  runtimeHandlersInstalled = false;
};
