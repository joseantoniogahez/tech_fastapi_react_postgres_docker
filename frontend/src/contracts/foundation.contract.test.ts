import { QueryClient } from "@tanstack/react-query";

import { MUTATION_POLICY_MATRIX, shouldRetryDefaultMutation } from "@/app/mutation-policy";
import { createQueryClient } from "@/app/query-client";
import { QUERY_POLICY_MATRIX, shouldRetryDefaultQuery } from "@/app/query-policy";
import { buildApiUrl } from "@/shared/api/env";
import { ApiError } from "@/shared/api/errors";
import { SESSION_QUERY_KEY, sessionQueryOptions } from "@/shared/auth/session";

describe("foundation contracts", () => {
  it("builds API URLs with normalized origin and base path", () => {
    expect(
      buildApiUrl("/users/me", {
        VITE_API_ORIGIN: "http://localhost:8000/",
        VITE_API_BASE_PATH: "v1/",
      }),
    ).toBe("http://localhost:8000/v1/users/me");
  });

  it("keeps session query options aligned with session policy", () => {
    const options = sessionQueryOptions();

    expect(options.queryKey).toEqual(SESSION_QUERY_KEY);
    expect(options.staleTime).toBe(QUERY_POLICY_MATRIX.sessionQuery.staleTimeMs);
    expect(options.retry).toBe(false);
    expect(options.refetchOnWindowFocus).toBe(true);
  });

  it("enforces default query retry contract for transient and unauthorized errors", () => {
    expect(shouldRetryDefaultQuery(0, new ApiError("Timeout", 503, "internal_error"))).toBe(true);
    expect(shouldRetryDefaultQuery(1, new ApiError("Timeout", 503, "internal_error"))).toBe(false);
    expect(shouldRetryDefaultQuery(0, new ApiError("Unauthorized", 401, "unauthorized"))).toBe(false);
  });

  it("creates query client with configured default query behavior", () => {
    const client: QueryClient = createQueryClient();
    const defaults = client.getDefaultOptions();

    expect(defaults.queries?.staleTime).toBe(QUERY_POLICY_MATRIX.defaultQuery.staleTimeMs);
    expect(defaults.queries?.refetchOnWindowFocus).toBe(false);
    expect(typeof defaults.queries?.retry).toBe("function");
    expect(typeof defaults.mutations?.retry).toBe("function");
  });

  it("enforces default mutation retry contract and no-retry auth mutation policy", () => {
    expect(shouldRetryDefaultMutation(0, new ApiError("Timeout", 503, "internal_error"))).toBe(true);
    expect(shouldRetryDefaultMutation(1, new ApiError("Timeout", 503, "internal_error"))).toBe(false);
    expect(shouldRetryDefaultMutation(0, new ApiError("Unauthorized", 401, "unauthorized"))).toBe(false);
    expect(MUTATION_POLICY_MATRIX.authLoginMutation.retry).toBe(false);
    expect(MUTATION_POLICY_MATRIX.authLogoutMutation.retry).toBe(false);
  });
});
