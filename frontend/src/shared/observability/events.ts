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

const REDACTED_FIELDS = new Set(["authorization", "password", "token", "access_token"]);

const sanitizeValue = (value: unknown): unknown => {
  if (Array.isArray(value)) {
    return value.map((item) => sanitizeValue(item));
  }

  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    const sanitizedRecord: Record<string, unknown> = {};
    for (const [key, entry] of Object.entries(record)) {
      if (REDACTED_FIELDS.has(key.toLowerCase())) {
        sanitizedRecord[key] = "[redacted]";
      } else {
        sanitizedRecord[key] = sanitizeValue(entry);
      }
    }
    return sanitizedRecord;
  }

  return value;
};

export const emitObservabilityEvent = (event: ObservabilityEvent): void => {
  const payload = {
    event_name: event.event_name,
    level: event.level,
    timestamp: new Date().toISOString(),
    request_id: event.request_id ?? null,
    context: sanitizeValue(event.context ?? {}),
  };

  if (event.level === "error") {
    console.error("[frontend-observability]", payload);
    return;
  }

  if (event.level === "warn") {
    console.warn("[frontend-observability]", payload);
    return;
  }

  console.info("[frontend-observability]", payload);
};
