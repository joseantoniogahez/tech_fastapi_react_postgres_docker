import { useQuery } from "@tanstack/react-query";

import { sessionQueryPolicy } from "@/app/query-policy";
import { isUnauthorizedError } from "@/shared/api/errors";
import { apiRequest } from "@/shared/api/http";
import {
  parseAccessTokenResponse,
  parseAuthenticatedUser,
  type AccessTokenResponse,
  type AuthenticatedUser,
} from "@/shared/auth/contracts";
import { clearAccessToken, getAccessToken, setAccessToken } from "@/shared/auth/storage";

interface Credentials {
  username: string;
  password: string;
}

export type { AuthenticatedUser };

export const SESSION_QUERY_KEY = ["auth", "session"] as const;
export const TOKEN_ENDPOINT_PATH = "/token";
export const CURRENT_USER_ENDPOINT_PATH = "/users/me";

export const readCurrentUser = (): Promise<AuthenticatedUser> =>
  apiRequest<AuthenticatedUser>(CURRENT_USER_ENDPOINT_PATH, {
    parse: parseAuthenticatedUser,
  });

export const loginWithCredentials = async ({ username, password }: Credentials): Promise<void> => {
  const body = new URLSearchParams({
    username,
    password,
  });

  const token = await apiRequest<AccessTokenResponse>(TOKEN_ENDPOINT_PATH, {
    method: "POST",
    body,
    withAuth: false,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    parse: parseAccessTokenResponse,
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

export const sessionQueryOptions = () => ({
  queryKey: SESSION_QUERY_KEY,
  queryFn: resolveSessionUser,
  ...sessionQueryPolicy,
});

export const useSession = () => useQuery(sessionQueryOptions());
