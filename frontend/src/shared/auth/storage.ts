const ACCESS_TOKEN_KEY = "auth.access_token";

export const getAccessToken = (): string | null => localStorage.getItem(ACCESS_TOKEN_KEY);

export const setAccessToken = (token: string): void => {
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
};

export const clearAccessToken = (): void => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
};

export const ACCESS_TOKEN_STORAGE_KEY = ACCESS_TOKEN_KEY;
