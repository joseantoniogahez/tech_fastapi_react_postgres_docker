export const MUTATION_POLICY_MATRIX = {
  defaultMutation: {
    retry: false,
    retryStrategy: "no inherited automatic retry",
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

export const defaultMutationPolicy = {
  retry: MUTATION_POLICY_MATRIX.defaultMutation.retry,
} as const;

export const authLoginMutationPolicy = {
  retry: MUTATION_POLICY_MATRIX.authLoginMutation.retry,
} as const;

export const authLogoutMutationPolicy = {
  retry: MUTATION_POLICY_MATRIX.authLogoutMutation.retry,
} as const;
