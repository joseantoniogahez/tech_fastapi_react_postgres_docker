import { ApiError } from "@/shared/api/errors";

import {
  MUTATION_POLICY_MATRIX,
  authLoginMutationPolicy,
  authLogoutMutationPolicy,
  shouldRetryDefaultMutation,
} from "@/app/mutation-policy";

describe("mutation policy", () => {
  it("retries transient mutation failures once", () => {
    expect(shouldRetryDefaultMutation(0, new ApiError("Temporary", 503, "internal_error"))).toBe(true);
    expect(shouldRetryDefaultMutation(1, new ApiError("Temporary", 503, "internal_error"))).toBe(false);
  });

  it("does not retry unauthorized or conflict mutation failures", () => {
    expect(shouldRetryDefaultMutation(0, new ApiError("Unauthorized", 401, "unauthorized"))).toBe(false);
    expect(shouldRetryDefaultMutation(0, new ApiError("Conflict", 409, "conflict"))).toBe(false);
  });

  it("retries network-like and unknown runtime failures once", () => {
    expect(shouldRetryDefaultMutation(0, new ApiError("Network", 0, "network_error"))).toBe(true);
    expect(shouldRetryDefaultMutation(0, new Error("Browser canceled request"))).toBe(true);
    expect(shouldRetryDefaultMutation(1, new Error("Browser canceled request"))).toBe(false);
  });

  it("keeps auth mutation policies as explicit no-retry contracts", () => {
    expect(MUTATION_POLICY_MATRIX.authLoginMutation.retry).toBe(false);
    expect(MUTATION_POLICY_MATRIX.authLogoutMutation.retry).toBe(false);
    expect(authLoginMutationPolicy.retry).toBe(false);
    expect(authLogoutMutationPolicy.retry).toBe(false);
  });
});
