import { useQuery } from "@tanstack/react-query";

import { isUnauthorizedError } from "@/shared/api/errors";
import { apiRequest } from "@/shared/api/http";
import { clearAccessToken, getAccessToken, setAccessToken } from "@/shared/auth/storage";

export interface AuthenticatedUser {
  id: number;
  username: string;
  disabled: boolean;
}

interface AccessTokenResponse {
  access_token: string;
  token_type: "bearer";
}

interface Credentials {
  username: string;
  password: string;
}

export const SESSION_QUERY_KEY = ["auth", "session"] as const;

export const readCurrentUser = (): Promise<AuthenticatedUser> =>
  apiRequest<AuthenticatedUser>("/users/me");

export const loginWithCredentials = async ({ username, password }: Credentials): Promise<void> => {
  const body = new URLSearchParams({
    username,
    password,
  });

  const token = await apiRequest<AccessTokenResponse>("/token", {
    method: "POST",
    body,
    withAuth: false,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  setAccessToken(token.access_token);
};

export const logout = (): void => {
  clearAccessToken();
};

export const resolveSessionUser = async (): Promise<AuthenticatedUser | null> => {
  if (!getAccessToken()) {
    return null;
  }

  try {
    return await readCurrentUser();
  } catch (error) {
    if (isUnauthorizedError(error)) {
      clearAccessToken();
      return null;
    }
    throw error;
  }
};

const SESSION_STALE_TIME_MS = 60_000;

export const sessionQueryOptions = () => ({
  queryKey: SESSION_QUERY_KEY,
  queryFn: resolveSessionUser,
  staleTime: SESSION_STALE_TIME_MS,
  retry: false,
});

export const useSession = () => useQuery(sessionQueryOptions());
