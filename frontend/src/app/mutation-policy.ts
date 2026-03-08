import { ApiError } from "@/shared/api/errors";

const TRANSIENT_HTTP_STATUSES = new Set([408, 425, 429, 500, 502, 503, 504]);
const MAX_DEFAULT_MUTATION_RETRIES = 1;

export const MUTATION_POLICY_MATRIX = {
  defaultMutation: {
    maxRetries: MAX_DEFAULT_MUTATION_RETRIES,
    retryStrategy: "retry only transient/network failures",
  },
  authLoginMutation: {
    retry: false,
    invalidationStrategy: "write-through session cache and invalidate session query",
  },
  authLogoutMutation: {
    retry: false,
    invalidationStrategy: "clear session cache and invalidate session query",
  },
} as const;

const isTransientMutationError = (error: ApiError): boolean => {
  if (error.code === "network_error" || error.status === 0) {
    return true;
  }

  if (error.status === 401 || error.status === 409) {
    return false;
  }

  return TRANSIENT_HTTP_STATUSES.has(error.status);
};

export const shouldRetryDefaultMutation = (failureCount: number, error: unknown): boolean => {
  if (failureCount >= MAX_DEFAULT_MUTATION_RETRIES) {
    return false;
  }

  if (error instanceof ApiError) {
    return isTransientMutationError(error);
  }

  return true;
};

export const defaultMutationPolicy = {
  retry: shouldRetryDefaultMutation,
} as const;

export const authLoginMutationPolicy = {
  retry: MUTATION_POLICY_MATRIX.authLoginMutation.retry,
} as const;

export const authLogoutMutationPolicy = {
  retry: MUTATION_POLICY_MATRIX.authLogoutMutation.retry,
} as const;
