interface ApiErrorPayload {
  detail?: string;
  code?: string;
  request_id?: string;
}

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
  let payload: ApiErrorPayload | undefined;

  try {
    payload = (await response.json()) as ApiErrorPayload;
  } catch {
    payload = undefined;
  }

  const requestIdHeader = response.headers?.get?.("X-Request-ID")?.trim();
  const requestIdPayload = payload?.request_id?.trim();
  const requestId = requestIdHeader && requestIdHeader.length > 0 ? requestIdHeader : requestIdPayload;

  const detail = payload?.detail?.trim();
  if (detail) {
    return new ApiError(detail, response.status, payload?.code, requestId);
  }

  const statusText = response.statusText?.trim();
  if (statusText) {
    return new ApiError(statusText, response.status, payload?.code, requestId);
  }

  return new ApiError("Error de comunicacion con el servidor", response.status, payload?.code, requestId);
};

export const getApiErrorRequestId = (error: unknown): string | null => {
  if (error instanceof ApiError && error.requestId) {
    return error.requestId;
  }
  return null;
};

export const appendRequestIdDiagnostic = (message: string, requestId: string | null): string => {
  if (!requestId) {
    return message;
  }
  return `${message} (request_id=${requestId})`;
};

export const isUnauthorizedError = (error: unknown): error is ApiError =>
  error instanceof ApiError && error.status === 401;
