import { buildApiUrl } from "@/shared/api/env";
import { parseApiError } from "@/shared/api/errors";
import { getAccessToken } from "@/shared/auth/storage";

type RequestOptions = Omit<RequestInit, "headers"> & {
  headers?: HeadersInit;
  withAuth?: boolean;
};

export const apiRequest = async <T>(path: string, options: RequestOptions = {}): Promise<T> => {
  const { withAuth = true, headers, ...init } = options;
  const requestHeaders = new Headers(headers ?? {});

  if (withAuth) {
    const token = getAccessToken();
    if (token) {
      requestHeaders.set("Authorization", `Bearer ${token}`);
    }
  }

  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: requestHeaders,
  });

  if (!response.ok) {
    throw await parseApiError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
};
