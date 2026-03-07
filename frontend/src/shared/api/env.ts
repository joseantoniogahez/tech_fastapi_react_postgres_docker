const DEFAULT_API_ORIGIN = "http://localhost:8000";
const DEFAULT_API_BASE_PATH = "/v1";

interface FrontendEnv {
  [key: string]: unknown;
  VITE_API_ORIGIN?: string;
  VITE_API_BASE_PATH?: string;
}

const normalizeOrigin = (origin: string): string => origin.trim().replace(/\/+$/, "");

const normalizeBasePath = (basePath: string): string => {
  const sanitized = basePath.trim().replace(/^\/+|\/+$/g, "");
  return sanitized ? `/${sanitized}` : "";
};

const normalizePath = (path: string): string => `/${path.replace(/^\/+/, "")}`;

export const getApiBaseUrl = (env: FrontendEnv = import.meta.env as FrontendEnv): string => {
  const origin = normalizeOrigin(env.VITE_API_ORIGIN ?? DEFAULT_API_ORIGIN);
  const basePath = normalizeBasePath(env.VITE_API_BASE_PATH ?? DEFAULT_API_BASE_PATH);
  return `${origin}${basePath}`;
};

export const buildApiUrl = (path: string, env: FrontendEnv = import.meta.env as FrontendEnv): string =>
  `${getApiBaseUrl(env)}${normalizePath(path)}`;
