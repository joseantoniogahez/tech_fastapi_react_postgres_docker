import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

export const DEFAULT_API_ORIGIN = "http://localhost:8000";

const SECURITY_HEADERS = Object.freeze({
  "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
});

export const normalizeApiOrigin = (value = DEFAULT_API_ORIGIN) => {
  if (typeof value !== "string") {
    throw new TypeError("VITE_API_ORIGIN must be a string");
  }

  const candidate = value.trim();
  if (!candidate) {
    throw new TypeError("VITE_API_ORIGIN must not be empty");
  }

  let url;
  try {
    url = new URL(candidate);
  } catch {
    throw new TypeError("VITE_API_ORIGIN must be a valid URL");
  }

  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new TypeError("VITE_API_ORIGIN must use the http or https protocol");
  }

  if (url.username || url.password || url.href !== `${url.origin}/`) {
    throw new TypeError("VITE_API_ORIGIN must be a canonical HTTP(S) origin");
  }

  return url.origin;
};

export const createContentSecurityPolicy = (apiOrigin) =>
  [
    "default-src 'self'",
    "base-uri 'self'",
    `connect-src 'self' ${normalizeApiOrigin(apiOrigin)}`,
    "font-src 'self' data: https://fonts.gstatic.com",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "frame-src 'none'",
    "img-src 'self' data:",
    "object-src 'none'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  ].join("; ");

export const createServeConfig = (apiOrigin) => ({
  cleanUrls: false,
  directoryListing: false,
  headers: [
    {
      source: "**",
      headers: [
        { key: "Content-Security-Policy", value: createContentSecurityPolicy(apiOrigin) },
        ...Object.entries(SECURITY_HEADERS).map(([key, value]) => ({ key, value })),
      ],
    },
  ],
});

export const writeServeConfig = (outputPath, apiOrigin) => {
  const resolvedOutputPath = path.resolve(outputPath);
  fs.mkdirSync(path.dirname(resolvedOutputPath), { recursive: true });
  fs.writeFileSync(resolvedOutputPath, `${JSON.stringify(createServeConfig(apiOrigin), null, 2)}\n`, "utf8");
  return resolvedOutputPath;
};

const parseArguments = (args) => {
  if (args.length === 1 && args[0] === "--check") {
    return { checkOnly: true };
  }
  if (args.length === 2 && args[0] === "--output" && args[1]) {
    return { checkOnly: false, outputPath: args[1] };
  }
  throw new TypeError("usage: node scripts/generate-serve-config.mjs --check | --output <path>");
};

const main = async () => {
  const options = parseArguments(process.argv.slice(2));
  const { loadEnv } = await import("vite");
  const env = loadEnv("production", process.cwd());
  const apiOrigin = normalizeApiOrigin(env.VITE_API_ORIGIN);
  if (!options.checkOnly) {
    writeServeConfig(options.outputPath, apiOrigin);
  }
};

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try {
    await main();
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
