import { getApiErrorRequestId, hasApiErrorCause } from "@/shared/api/errors";
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
    emitObservabilityEvent({
      event_name: "runtime.error",
      level: "error",
      request_id: getApiErrorRequestId(event.error),
      context: {
        message: resolveErrorMessage(event.error ?? event.message),
      },
    });
  };

  runtimeUnhandledRejectionHandler = (event) => {
    const reason: unknown = event.reason;
    emitObservabilityEvent({
      event_name: "runtime.unhandled_rejection",
      level: "error",
      request_id: getApiErrorRequestId(reason),
      context: {
        reason: resolveErrorMessage(reason),
        is_api_error: hasApiErrorCause(reason),
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
