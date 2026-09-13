type EventLevel = "info" | "warn" | "error";

export interface ObservabilityEvent {
  event_name:
    | "api.request.network_error"
    | "api.request.response_error"
    | "routing.protected.error"
    | "routing.route_error"
    | "runtime.error"
    | "runtime.unhandled_rejection";
  level: EventLevel;
  request_id?: string | null;
  context?: Record<string, unknown>;
}

const REDACTED_FIELD = /token$|^authorization$|^password$/i;

export const sanitizeObservabilityValue = (value: unknown): unknown => {
  if (Array.isArray(value)) {
    return value.map(sanitizeObservabilityValue);
  }

  if (value && typeof value === "object") {
    const sanitizedRecord: Record<string, unknown> = {};
    for (const [key, entry] of Object.entries(value)) {
      sanitizedRecord[key] = REDACTED_FIELD.test(key)
        ? "[redacted]"
        : sanitizeObservabilityValue(entry);
    }
    return sanitizedRecord;
  }

  return value;
};

export const emitObservabilityEvent = (event: ObservabilityEvent): void => {
  const payload = {
    event_name: event.event_name,
    level: event.level,
    timestamp: new Date().toJSON(),
    request_id: event.request_id ?? null,
    context: sanitizeObservabilityValue(event.context ?? {}),
  };

  console[event.level]("[frontend-observability]", payload);
};
