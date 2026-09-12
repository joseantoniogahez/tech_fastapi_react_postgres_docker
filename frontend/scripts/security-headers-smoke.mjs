import path from "node:path";
import { pathToFileURL } from "node:url";

import { normalizeApiOrigin } from "./generate-serve-config.mjs";

const REQUIRED_HEADERS = Object.freeze({
  "permissions-policy": "geolocation=(), microphone=(), camera=()",
  "referrer-policy": "strict-origin-when-cross-origin",
  "x-content-type-options": "nosniff",
  "x-frame-options": "DENY",
});

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

const normalizeFrontendOrigin = (value) => {
  const origin = normalizeApiOrigin(value);
  if (origin !== value.replace(/\/$/, "")) {
    throw new TypeError("frontend smoke URL must be a canonical HTTP(S) origin");
  }
  return origin;
};

const parseDirectives = (policy) =>
  new Map(
    policy
      .split(";")
      .map((directive) => directive.trim().split(/\s+/))
      .filter(([name]) => name)
      .map(([name, ...values]) => [name, values]),
  );

const assertResponseContract = async (response, expectedApiOrigin, label) => {
  if (response.status !== 200) {
    throw new Error(`${label} returned HTTP ${response.status}, expected 200`);
  }

  for (const [name, expectedValue] of Object.entries(REQUIRED_HEADERS)) {
    const actualValue = response.headers.get(name);
    if (actualValue !== expectedValue) {
      throw new Error(`${label} header ${name} was '${actualValue}', expected '${expectedValue}'`);
    }
  }

  const policy = response.headers.get("content-security-policy");
  if (!policy) {
    throw new Error(`${label} is missing Content-Security-Policy`);
  }

  const directives = parseDirectives(policy);
  const connectSources = directives.get("connect-src") ?? [];
  if (!connectSources.includes("'self'") || !connectSources.includes(expectedApiOrigin)) {
    throw new Error(`${label} connect-src does not contain self and the configured API origin`);
  }
  if (connectSources.some((source) => source === "*" || source === "http:" || source === "https:")) {
    throw new Error(`${label} connect-src permits an open network source`);
  }
  if (directives.get("frame-ancestors")?.join(" ") !== "'none'") {
    throw new Error(`${label} does not deny framing through CSP frame-ancestors`);
  }
  if (directives.get("script-src")?.join(" ") !== "'self'") {
    throw new Error(`${label} does not restrict scripts to same-origin assets`);
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.toLowerCase().includes("text/html")) {
    throw new Error(`${label} returned '${contentType}', expected an HTML SPA response`);
  }
  const body = await response.text();
  if (!body.toLowerCase().includes("<!doctype html") || !body.includes('id="root"')) {
    throw new Error(`${label} did not return the SPA entry document`);
  }
};

const fetchWithRetry = async (url, attempts, retryDelayMs) => {
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return await fetch(url, { redirect: "error", signal: AbortSignal.timeout(5_000) });
    } catch (error) {
      lastError = error;
      if (attempt < attempts) {
        await sleep(retryDelayMs);
      }
    }
  }
  throw lastError;
};

export const runSecurityHeadersSmoke = async ({
  baseUrl,
  expectedApiOrigin,
  attempts = 15,
  retryDelayMs = 500,
}) => {
  const frontendOrigin = normalizeFrontendOrigin(baseUrl);
  const apiOrigin = normalizeApiOrigin(expectedApiOrigin);
  const paths = ["/", "/__security_headers_spa_fallback__"];

  for (const requestPath of paths) {
    const response = await fetchWithRetry(`${frontendOrigin}${requestPath}`, attempts, retryDelayMs);
    await assertResponseContract(response, apiOrigin, requestPath === "/" ? "root response" : "SPA fallback response");
  }
};

const main = async () => {
  const [baseUrl = process.env.FRONTEND_SMOKE_URL, expectedApiOrigin = process.env.FRONTEND_SMOKE_API_ORIGIN] =
    process.argv.slice(2);
  if (!baseUrl || !expectedApiOrigin) {
    throw new TypeError(
      "usage: node scripts/security-headers-smoke.mjs <frontend-origin> <expected-api-origin>",
    );
  }
  await runSecurityHeadersSmoke({ baseUrl, expectedApiOrigin });
  console.log("Frontend root and SPA fallback security headers passed.");
};

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
}
