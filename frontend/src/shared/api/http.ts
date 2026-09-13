import { buildApiUrl } from "@/shared/api/env";
import { ApiError, getResponseRequestId, parseApiError } from "@/shared/api/errors";
import { getAccessToken, revokeAccessToken } from "@/shared/auth/storage";
import { t } from "@/shared/i18n/ui-text";
import { emitObservabilityEvent } from "@/shared/observability/events";

type ResponseParser<T> = (payload: unknown) => T;

type BaseRequestOptions = Omit<RequestInit, "headers"> & {
  headers?: HeadersInit;
  withAuth?: boolean;
  diagnosticPath?: string;
};

export type RequestOptions<T> = BaseRequestOptions & {
  parse: ResponseParser<T>;
};

export type NoContentRequestOptions = BaseRequestOptions;

interface ApiResponse {
  response: Response;
  method: string;
  diagnosticPath: string;
}

export const toDiagnosticApiPath = (path: string): string => path.split(/[?#]/)[0]!;

const throwResponseError = (apiError: ApiError, method: string, path: string): never => {
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
};

const executeRequest = async (
  path: string,
  options: BaseRequestOptions = {},
): Promise<ApiResponse> => {
  const { withAuth = true, headers, diagnosticPath, ...init } = options;
  const requestHeaders = new Headers(headers ?? {});
  const pathForDiagnostics = toDiagnosticApiPath(diagnosticPath ?? path);

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
        path: pathForDiagnostics,
      },
    });
    throw networkError;
  }

  if (!response.ok) {
    const apiError = await parseApiError(response);
    if (withAuth && apiError.status === 401) {
      revokeAccessToken();
    }
    return throwResponseError(apiError, method, pathForDiagnostics);
  }

  return { response, method, diagnosticPath: pathForDiagnostics };
};

const throwInvalidResponse = ({ response, method, diagnosticPath }: ApiResponse): never =>
  throwResponseError(
    new ApiError(
      t("api.error.invalidResponse"),
      response.status,
      "invalid_response",
      getResponseRequestId(response),
    ),
    method,
    diagnosticPath,
  );

export const apiRequest = async <T>(path: string, options: RequestOptions<T>): Promise<T> => {
  const { parse, ...requestOptions } = options;
  const result = await executeRequest(path, requestOptions);

  if (result.response.status === 204) {
    return throwInvalidResponse(result);
  }

  try {
    return parse(await result.response.json());
  } catch {
    return throwInvalidResponse(result);
  }
};

export const apiNoContentRequest = async (
  path: string,
  options: NoContentRequestOptions = {},
): Promise<void> => {
  const result = await executeRequest(path, options);
  if (result.response.status !== 204) {
    return throwInvalidResponse(result);
  }
};
