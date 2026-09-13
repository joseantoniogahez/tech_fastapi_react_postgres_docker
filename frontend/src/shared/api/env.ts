const DEFAULT_API_ORIGIN = "http://localhost:8000";
const DEFAULT_API_BASE_PATH = "/v1";

interface FrontendEnvInput {
  [key: string]: unknown;
  VITE_API_ORIGIN?: unknown;
  VITE_API_BASE_PATH?: unknown;
}

interface FrontendEnvConfig {
  apiOrigin: string;
  apiBasePath: string;
}

export class FrontendEnvError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "FrontendEnvError";
  }
}

const normalizeBasePath = (basePath: string): string => {
  const sanitized = basePath.trim().replace(/^\/+|\/+$/g, "");
  return sanitized ? `/${sanitized}` : "";
};

const normalizePath = (path: string): string => `/${path.replace(/^\/+/, "")}`;

const ensureString = (value: unknown, fieldName: string): string => {
  if (typeof value !== "string") {
    throw new FrontendEnvError(`${fieldName} must be a string`);
  }

  const normalized = value.trim();
  if (!normalized) {
    throw new FrontendEnvError(`${fieldName} must not be empty`);
  }

  return normalized;
};

const validateOrigin = (origin: string): string => {
  try {
    const url = new URL(origin);
    if (url.protocol !== "http:" && url.protocol !== "https:") {
      throw new FrontendEnvError(`VITE_API_ORIGIN must use http/https protocol, received '${url.protocol}'`);
    }

    if (url.username || url.password || url.href !== `${url.origin}/`) {
      throw new FrontendEnvError("VITE_API_ORIGIN must be an origin");
    }

    return url.origin;
  } catch (error) {
    if (error instanceof FrontendEnvError) {
      throw error;
    }

    throw new FrontendEnvError(`VITE_API_ORIGIN is invalid URL: '${origin}'`);
  }
};

const validateBasePath = (basePath: string): string => {
  const normalizedBasePath = normalizeBasePath(basePath);
  if (normalizedBasePath.includes(" ")) {
    throw new FrontendEnvError("VITE_API_BASE_PATH must not contain spaces");
  }

  return normalizedBasePath;
};

export const readFrontendEnvConfig = (
  env: FrontendEnvInput = import.meta.env as FrontendEnvInput,
): FrontendEnvConfig => {
  const origin = ensureString(env.VITE_API_ORIGIN ?? DEFAULT_API_ORIGIN, "VITE_API_ORIGIN");
  const basePath = ensureString(env.VITE_API_BASE_PATH ?? DEFAULT_API_BASE_PATH, "VITE_API_BASE_PATH");

  return {
    apiOrigin: validateOrigin(origin),
    apiBasePath: validateBasePath(basePath),
  };
};

export const getApiBaseUrl = (env: FrontendEnvInput = import.meta.env as FrontendEnvInput): string => {
  const config = readFrontendEnvConfig(env);
  return `${config.apiOrigin}${config.apiBasePath}`;
};

export const buildApiUrl = (path: string, env: FrontendEnvInput = import.meta.env as FrontendEnvInput): string => {
  const apiBaseUrl = getApiBaseUrl(env);
  return `${apiBaseUrl}${normalizePath(path)}`;
};
