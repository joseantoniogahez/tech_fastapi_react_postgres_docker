import { ApiError } from "@/shared/api/errors";
import { QUERY_POLICY_MATRIX, sessionQueryPolicy, shouldRetryDefaultQuery } from "@/app/query-policy";

describe("query policy", () => {
  it("retries transient server errors once", () => {
    expect(shouldRetryDefaultQuery(0, new ApiError("Server error", 500, "internal_error"))).toBe(true);
    expect(shouldRetryDefaultQuery(1, new ApiError("Server error", 500, "internal_error"))).toBe(false);
  });

  it("does not retry unauthorized errors", () => {
    expect(shouldRetryDefaultQuery(0, new ApiError("Unauthorized", 401, "unauthorized"))).toBe(false);
  });

  it("retries network errors once", () => {
    expect(shouldRetryDefaultQuery(0, new ApiError("Network error", 0, "network_error"))).toBe(true);
    expect(shouldRetryDefaultQuery(1, new ApiError("Network error", 0, "network_error"))).toBe(false);
  });

  it("session policy keeps explicit no-retry behavior", () => {
    expect(sessionQueryPolicy.retry).toBe(false);
    expect(sessionQueryPolicy.staleTime).toBe(QUERY_POLICY_MATRIX.sessionQuery.staleTimeMs);
    expect(sessionQueryPolicy.refetchOnWindowFocus).toBe(true);
  });
});
