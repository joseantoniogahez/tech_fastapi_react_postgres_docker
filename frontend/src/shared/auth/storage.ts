const LEGACY_ACCESS_TOKEN_KEY = "auth.access_token";
const SESSION_ACCESS_TOKEN_KEY = "auth.session.access_token";
const STORAGE_PROBE_KEY = "__auth_storage_probe__";

let inMemoryAccessToken: string | null = null;

const canUseStorage = (storage: Storage | undefined): storage is Storage => {
  if (!storage) {
    return false;
  }

  try {
    storage.setItem(STORAGE_PROBE_KEY, "ok");
    storage.removeItem(STORAGE_PROBE_KEY);
    return true;
  } catch {
    return false;
  }
};

const getSessionStorage = (): Storage | undefined => {
  if (typeof window === "undefined") {
    return undefined;
  }
  return window.sessionStorage;
};

const getLocalStorage = (): Storage | undefined => {
  if (typeof window === "undefined") {
    return undefined;
  }
  return window.localStorage;
};

const migrateLegacyTokenIfNeeded = (): void => {
  const sessionStorage = getSessionStorage();
  const localStorage = getLocalStorage();
  if (!canUseStorage(sessionStorage) || !canUseStorage(localStorage)) {
    return;
  }

  const existingSessionToken = sessionStorage.getItem(SESSION_ACCESS_TOKEN_KEY);
  if (existingSessionToken) {
    localStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY);
    return;
  }

  const legacyToken = localStorage.getItem(LEGACY_ACCESS_TOKEN_KEY);
  if (legacyToken) {
    sessionStorage.setItem(SESSION_ACCESS_TOKEN_KEY, legacyToken);
  }
  localStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY);
};

export const getAccessToken = (): string | null => {
  const sessionStorage = getSessionStorage();
  if (canUseStorage(sessionStorage)) {
    migrateLegacyTokenIfNeeded();
    const token = sessionStorage.getItem(SESSION_ACCESS_TOKEN_KEY);
    inMemoryAccessToken = token;
    return token;
  }

  return inMemoryAccessToken;
};

export const setAccessToken = (token: string): void => {
  inMemoryAccessToken = token;

  const sessionStorage = getSessionStorage();
  if (canUseStorage(sessionStorage)) {
    sessionStorage.setItem(SESSION_ACCESS_TOKEN_KEY, token);
  }

  const localStorage = getLocalStorage();
  if (canUseStorage(localStorage)) {
    localStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY);
  }
};

export const clearAccessToken = (): void => {
  inMemoryAccessToken = null;

  const sessionStorage = getSessionStorage();
  if (canUseStorage(sessionStorage)) {
    sessionStorage.removeItem(SESSION_ACCESS_TOKEN_KEY);
  }

  const localStorage = getLocalStorage();
  if (canUseStorage(localStorage)) {
    localStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY);
  }
};

export const ACCESS_TOKEN_STORAGE_KEY = SESSION_ACCESS_TOKEN_KEY;
export const ACCESS_TOKEN_LEGACY_STORAGE_KEY = LEGACY_ACCESS_TOKEN_KEY;
