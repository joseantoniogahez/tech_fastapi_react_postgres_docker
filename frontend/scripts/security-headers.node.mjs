import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { afterEach, test } from "node:test";

import { createServeConfig, normalizeApiOrigin, writeServeConfig } from "./generate-serve-config.mjs";
import { runSecurityHeadersSmoke } from "./security-headers-smoke.mjs";

const temporaryDirectories = [];

afterEach(() => {
  for (const directory of temporaryDirectories.splice(0)) {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});

test("generates deterministic serve configuration from a canonical API origin", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "frontend-serve-config-"));
  temporaryDirectories.push(directory);
  const outputPath = path.join(directory, "serve.json");

  writeServeConfig(outputPath, "HTTPS://API.Example.COM:443/");
  const first = fs.readFileSync(outputPath, "utf8");
  writeServeConfig(outputPath, "https://api.example.com");
  const second = fs.readFileSync(outputPath, "utf8");

  assert.equal(first, second);
  const config = JSON.parse(first);
  assert.equal(config.headers[0].source, "**");
  const csp = config.headers[0].headers.find((header) => header.key === "Content-Security-Policy").value;
  assert.match(csp, /connect-src 'self' https:\/\/api\.example\.com/);
  assert.doesNotMatch(csp, /connect-src[^;]*(?:https:|http:)\s*(?:;|$)/);
});

test("rejects API values that are not canonical HTTP(S) origins", () => {
  for (const value of [
    "",
    "ftp://api.example.com",
    "https://user@api.example.com",
    "https://api.example.com/v1",
    "https://api.example.com?debug=true",
    "https://api.example.com#status",
  ]) {
    assert.throws(() => normalizeApiOrigin(value), /VITE_API_ORIGIN/);
  }
});

test("HTTP smoke inspects root and SPA fallback response headers", async () => {
  const apiOrigin = "https://api.example.com";
  const config = createServeConfig(apiOrigin);
  const headers = Object.fromEntries(
    config.headers[0].headers.map(({ key, value }) => [key, value]),
  );
  const requestedPaths = [];
  const server = http.createServer((request, response) => {
    requestedPaths.push(request.url);
    response.writeHead(200, { ...headers, "Content-Type": "text/html; charset=utf-8" });
    response.end('<!doctype html><html><body><div id="root"></div></body></html>');
  });

  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const address = server.address();
    assert.ok(address && typeof address === "object");
    await runSecurityHeadersSmoke({
      baseUrl: `http://127.0.0.1:${address.port}`,
      expectedApiOrigin: apiOrigin,
      attempts: 1,
    });
  } finally {
    await new Promise((resolve, reject) =>
      server.close((error) => (error ? reject(error) : resolve())),
    );
  }

  assert.deepEqual(requestedPaths, ["/", "/__security_headers_spa_fallback__"]);
});

test("HTTP smoke fails closed when the CSP allows arbitrary HTTPS origins", async () => {
  const apiOrigin = "https://api.example.com";
  const config = createServeConfig(apiOrigin);
  const headers = Object.fromEntries(config.headers[0].headers.map(({ key, value }) => [key, value]));
  headers["Content-Security-Policy"] = headers["Content-Security-Policy"].replace(
    `connect-src 'self' ${apiOrigin}`,
    "connect-src 'self' https:",
  );
  const server = http.createServer((_request, response) => {
    response.writeHead(200, { ...headers, "Content-Type": "text/html" });
    response.end('<!doctype html><div id="root"></div>');
  });

  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const address = server.address();
    assert.ok(address && typeof address === "object");
    await assert.rejects(
      runSecurityHeadersSmoke({
        baseUrl: `http://127.0.0.1:${address.port}`,
        expectedApiOrigin: apiOrigin,
        attempts: 1,
      }),
      /connect-src/,
    );
  } finally {
    await new Promise((resolve, reject) =>
      server.close((error) => (error ? reject(error) : resolve())),
    );
  }
});
