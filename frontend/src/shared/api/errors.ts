interface ApiErrorPayload {
  detail?: string;
  code?: string;
}

export class ApiError extends Error {
  status: number;

  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export const parseApiError = async (response: Response): Promise<ApiError> => {
  let payload: ApiErrorPayload | undefined;

  try {
    payload = (await response.json()) as ApiErrorPayload;
  } catch {
    payload = undefined;
  }

  const detail = payload?.detail?.trim();
  if (detail) {
    return new ApiError(detail, response.status, payload?.code);
  }

  const statusText = response.statusText.trim();
  if (statusText) {
    return new ApiError(statusText, response.status, payload?.code);
  }

  return new ApiError("Error de comunicacion con el servidor", response.status, payload?.code);
};

export const isUnauthorizedError = (error: unknown): error is ApiError =>
  error instanceof ApiError && error.status === 401;
