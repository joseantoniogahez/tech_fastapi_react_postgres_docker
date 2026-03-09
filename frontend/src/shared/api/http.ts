import { buildApiUrl } from "@/shared/api/env";
import { ApiError, parseApiError } from "@/shared/api/errors";
import { clearAccessToken, getAccessToken } from "@/shared/auth/storage";
import { emitObservabilityEvent } from "@/shared/observability/events";

type ResponseParser<T> = (payload: unknown) => T;

type RequestOptions<T> = Omit<RequestInit, "headers"> & {
  headers?: HeadersInit;
  withAuth?: boolean;
  parse?: ResponseParser<T>;
};

export const apiRequest = async <T>(path: string, options: RequestOptions<T> = {}): Promise<T> => {
  const { withAuth = true, headers, parse, ...init } = options;
  const requestHeaders = new Headers(headers ?? {});

  if (withAuth) {
    const token = getAccessToken();
    if (token) {
      requestHeaders.set("Authorization", `Bearer ${token}`);
    }
  }

  const method = init.method ?? "GET";
  let response: Response;
  try {
    response = await fetch(buildApiUrl(path), {
      ...init,
      headers: requestHeaders,
    });
  } catch {
    const networkError = new ApiError("Error de comunicacion con el servidor", 0, "network_error");
    emitObservabilityEvent({
      event_name: "api.request.network_error",
      level: "error",
      context: {
        method,
        path,
        code: networkError.code,
      },
    });
    throw networkError;
  }

  if (!response.ok) {
    const apiError = await parseApiError(response);
    if (withAuth && apiError.status === 401) {
      clearAccessToken();
    }
    emitObservabilityEvent({
      event_name: "api.request.response_error",
      level: "error",
      request_id: apiError.requestId ?? null,
      context: {
        method,
        path,
        status: apiError.status,
        code: apiError.code,
      },
    });
    throw apiError;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const payload = (await response.json()) as unknown;
  if (parse) {
    return parse(payload);
  }

  return payload as T;
};
