import { ApiError } from "@/shared/api/errors";

const TRANSIENT_HTTP_STATUSES = new Set([408, 425, 429, 500, 502, 503, 504]);
const MAX_DEFAULT_QUERY_RETRIES = 1;

export const QUERY_POLICY_MATRIX = {
  defaultQuery: {
    staleTimeMs: 30_000,
    refetchOnWindowFocus: false,
    maxRetries: MAX_DEFAULT_QUERY_RETRIES,
    retryStrategy: "retry only transient/network errors",
  },
  sessionQuery: {
    staleTimeMs: 60_000,
    refetchOnWindowFocus: true,
    retry: false,
    retryStrategy: "no retry",
  },
} as const;

const isTransientApiError = (error: ApiError): boolean => {
  if (error.code === "network_error" || error.status === 0) {
    return true;
  }
  return TRANSIENT_HTTP_STATUSES.has(error.status);
};

export const shouldRetryDefaultQuery = (failureCount: number, error: unknown): boolean => {
  if (failureCount >= MAX_DEFAULT_QUERY_RETRIES) {
    return false;
  }

  if (error instanceof ApiError) {
    return isTransientApiError(error);
  }

  // Unknown client/runtime failures can be transient in the browser context.
  return true;
};

export const defaultQueryPolicy = {
  staleTime: QUERY_POLICY_MATRIX.defaultQuery.staleTimeMs,
  refetchOnWindowFocus: QUERY_POLICY_MATRIX.defaultQuery.refetchOnWindowFocus,
  retry: shouldRetryDefaultQuery,
} as const;

export const sessionQueryPolicy = {
  staleTime: QUERY_POLICY_MATRIX.sessionQuery.staleTimeMs,
  refetchOnWindowFocus: QUERY_POLICY_MATRIX.sessionQuery.refetchOnWindowFocus,
  retry: QUERY_POLICY_MATRIX.sessionQuery.retry,
} as const;
