/// <reference types="node" />

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { FRONTEND_DIR } from "@/contracts/docs";

const INDEX_HTML_PATH = path.join(FRONTEND_DIR, "index.html");
const DOCKERFILE_PATH = path.join(FRONTEND_DIR, "Dockerfile");
const GENERATOR_PATH = path.join(FRONTEND_DIR, "scripts", "generate-serve-config.mjs");
const SECURITY_BASELINE_DOC_PATH = path.join(FRONTEND_DIR, "docs", "operations", "browser_security_baseline.md");

interface ServeHeader {
  key: string;
  value: string;
}

interface ServeConfig {
  headers: { source: string; headers: ServeHeader[] }[];
}

const generateConfig = (apiOrigin: string) => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "frontend-browser-security-"));
  const outputPath = path.join(directory, "serve.json");
  const result = spawnSync(process.execPath, [GENERATOR_PATH, "--output", outputPath], {
    cwd: FRONTEND_DIR,
    encoding: "utf8",
    env: { ...process.env, VITE_API_ORIGIN: apiOrigin },
  });
  return { directory, outputPath, result };
};

describe("browser security baseline contracts", () => {
  it("keeps only the compatible referrer defense in development markup", () => {
    const html = fs.readFileSync(INDEX_HTML_PATH, "utf8");

    expect(html).toContain('name="referrer" content="strict-origin-when-cross-origin"');
    expect(html).not.toContain('http-equiv="Content-Security-Policy"');
    expect(html).not.toContain('http-equiv="Permissions-Policy"');
  });

  it("generates the complete serve response-header contract from the API origin", () => {
    const { directory, outputPath, result } = generateConfig("HTTPS://API.Example.COM:443/");
    try {
      expect(result.status, result.stderr).toBe(0);
      const config = JSON.parse(fs.readFileSync(outputPath, "utf8")) as ServeConfig;
      expect(config.headers).toHaveLength(1);
      expect(config.headers[0]?.source).toBe("**");

      const headers = Object.fromEntries(config.headers[0]?.headers.map(({ key, value }) => [key, value]) ?? []);
      expect(headers).toMatchObject({
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
      });

      const csp = headers["Content-Security-Policy"];
      expect(csp).toContain("connect-src 'self' https://api.example.com");
      expect(csp).toContain("frame-ancestors 'none'");
      expect(csp).toContain("script-src 'self'");
      expect(csp).not.toMatch(/connect-src[^;]*(?:^|\s)(?:\*|https?:)(?:\s|;|$)/);
    } finally {
      fs.rmSync(directory, { recursive: true, force: true });
    }
  });

  it.each([
    ["empty", ""],
    ["unsupported protocol", "ftp://api.example.com"],
    ["userinfo", "https://user@api.example.com"],
    ["path", "https://api.example.com/v1"],
    ["query", "https://api.example.com?debug=true"],
    ["fragment", "https://api.example.com#status"],
  ])("fails config generation for an API origin with %s", (_case, apiOrigin) => {
    const { directory, outputPath, result } = generateConfig(apiOrigin);
    try {
      expect(result.status).not.toBe(0);
      expect(fs.existsSync(outputPath)).toBe(false);
    } finally {
      fs.rmSync(directory, { recursive: true, force: true });
    }
  });

  it("keeps the generated config coupled to the production serve process", () => {
    const dockerfile = fs.readFileSync(DOCKERFILE_PATH, "utf8");

    expect(dockerfile).toContain("RUN npm install -g serve@14.2.6");
    expect(dockerfile).toContain("COPY --from=builder /app/.generated/serve.json /app/serve.json");
    expect(dockerfile).toContain("serve -s dist");
    expect(dockerfile).toContain("-c /app/serve.json");
    expect(dockerfile).not.toMatch(/FROM base AS production[\s\S]*ENV VITE_API_ORIGIN/);
  });

  it("documents HTTP enforcement, generation, and real-response validation", () => {
    const markdown = fs.readFileSync(SECURITY_BASELINE_DOC_PATH, "utf8");

    expect(markdown).toContain("## Required Response Headers");
    expect(markdown).toContain("## Build-Time Generation");
    expect(markdown).toContain("security-headers-smoke.mjs");
    expect(markdown).toContain("SPA fallback");
  });
});
