const DEFAULT_API_ORIGIN = "";
const DEFAULT_API_BASE_PATH = "/api";

const normalizeOrigin = (origin: string): string => origin.trim().replace(/\/+$/, "");

const normalizeBasePath = (basePath: string): string => {
  const sanitized = basePath.trim().replace(/^\/+|\/+$/g, "");
  return sanitized ? `/${sanitized}` : "";
};

const normalizePath = (path: string): string => `/${path.replace(/^\/+/, "")}`;

export const getApiBaseUrl = (): string => {
  const origin = normalizeOrigin(
    process.env.NEXT_PUBLIC_API_ORIGIN || DEFAULT_API_ORIGIN
  );
  const basePath = normalizeBasePath(
    process.env.NEXT_PUBLIC_API_BASE_PATH || DEFAULT_API_BASE_PATH
  );
  return `${origin}${basePath}`;
};

export const buildApiUrl = (path: string): string =>
  `${getApiBaseUrl()}${normalizePath(path)}`;
