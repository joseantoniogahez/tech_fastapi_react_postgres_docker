const readTrimmedString = (value: unknown): string | undefined =>
  typeof value === "string" ? value.trim() || undefined : undefined;

export const getResponseRequestId = (response: Response): string | undefined =>
  readTrimmedString(response.headers?.get?.("X-Request-ID"));

export class ApiError extends Error {
  status: number;

  code?: string;

  requestId?: string;

  constructor(message: string, status: number, code?: string, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

export const parseApiError = async (response: Response): Promise<ApiError> => {
  let payload: Record<string, unknown> | undefined;

  try {
    const value: unknown = await response.json();
    if (value && typeof value === "object" && !Array.isArray(value)) {
      payload = value as Record<string, unknown>;
    }
  } catch {
    // Invalid JSON leaves the payload unavailable.
  }

  const requestId =
    getResponseRequestId(response) ?? readTrimmedString(payload?.request_id);
  const code = readTrimmedString(payload?.code);

  const message =
    readTrimmedString(payload?.detail) ??
    readTrimmedString(response.statusText) ??
    "Error de comunicacion con el servidor";
  return new ApiError(message, response.status, code, requestId);
};

const findApiErrorInCauseChain = (
  error: unknown,
  requireRequestId: boolean,
): ApiError | null => {
  const visited = new Set<Error>();
  let current = error;

  while (
    visited.size < 9 &&
    current instanceof Error &&
    !visited.has(current)
  ) {
    if (current instanceof ApiError && (!requireRequestId || current.requestId)) {
      return current;
    }

    visited.add(current);
    current = current.cause;
  }

  return null;
};

export const getApiErrorRequestId = (error: unknown): string | null =>
  findApiErrorInCauseChain(error, true)?.requestId ?? null;

export const hasApiErrorCause = (error: unknown): boolean =>
  Boolean(findApiErrorInCauseChain(error, false));

export const appendRequestIdDiagnostic = (message: string, requestId: string | null): string => {
  if (!requestId) {
    return message;
  }
  return `${message} (request_id=${requestId})`;
};

export const isUnauthorizedError = (error: unknown): error is ApiError =>
  error instanceof ApiError && error.status === 401;
