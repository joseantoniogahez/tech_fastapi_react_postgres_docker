import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { afterEach, test } from "node:test";
import { fileURLToPath } from "node:url";

import { createServeConfig, normalizeApiOrigin, writeServeConfig } from "./generate-serve-config.mjs";
import { runSecurityHeadersSmoke } from "./security-headers-smoke.mjs";

const temporaryDirectories = [];
const generatorPath = fileURLToPath(new URL("./generate-serve-config.mjs", import.meta.url));

afterEach(() => {
  for (const directory of temporaryDirectories.splice(0)) {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});

test("CLI matches Vite production environment files, expansion, and process precedence", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "frontend-env-config-"));
  temporaryDirectories.push(directory);
  const outputPath = path.join(directory, "serve.json");
  const env = { ...process.env };
  delete env.VITE_API_ORIGIN;
  const checkOrigin = (expectedOrigin) => {
    const result = spawnSync(process.execPath, [generatorPath, "--output", outputPath], {
      cwd: directory, env, encoding: "utf8",
    });
    assert.equal(result.status, 0, result.stderr);
    const config = JSON.parse(fs.readFileSync(outputPath, "utf8"));
    const csp = config.headers[0].headers.find((header) => header.key === "Content-Security-Policy").value;
    assert.equal(csp.split("; ").find((directive) => directive.startsWith("connect-src")),
      `connect-src 'self' ${expectedOrigin}`);
  };

  checkOrigin("http://localhost:8000");
  for (const [file, origin] of [
    [".env", "https://base.example.test"],
    [".env.local", "https://local.example.test"],
    [".env.production", "https://production.example.test"],
    [".env.production.local", "https://production-local.example.test"],
  ]) {
    fs.writeFileSync(path.join(directory, file), `VITE_API_ORIGIN=${origin}\n`);
    checkOrigin(origin);
  }
  fs.writeFileSync(path.join(directory, ".env.production.local"),
    "REVIEW_API_HOST=expanded.example.test\nVITE_API_ORIGIN=https://${REVIEW_API_HOST}\n");
  checkOrigin("https://expanded.example.test");
  env.VITE_API_ORIGIN = "https://process.example.test";
  checkOrigin(env.VITE_API_ORIGIN);
});

test("CLI rejects an invalid production file origin before writing configuration", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "frontend-invalid-env-"));
  temporaryDirectories.push(directory);
  fs.writeFileSync(path.join(directory, ".env.production"), "VITE_API_ORIGIN=https://api.example.test/v1\n");
  const env = { ...process.env };
  delete env.VITE_API_ORIGIN;
  const outputPath = path.join(directory, "serve.json");
  for (const args of [["--check"], ["--output", outputPath]]) {
    const result = spawnSync(process.execPath, [generatorPath, ...args], {
      cwd: directory, env, encoding: "utf8",
    });
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /VITE_API_ORIGIN/);
    assert.equal(fs.existsSync(outputPath), false);
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
