/// <reference types="node" />

import fs from "node:fs";
import path from "node:path";

import { FRONTEND_DIR } from "@/contracts/docs";

const INDEX_HTML_PATH = path.join(FRONTEND_DIR, "index.html");
const SECURITY_BASELINE_DOC_PATH = path.join(FRONTEND_DIR, "docs", "operations", "browser_security_baseline.md");

describe("browser security baseline contracts", () => {
  it("keeps required security meta policies in index.html", () => {
    const html = fs.readFileSync(INDEX_HTML_PATH, "utf8");

    expect(html).toContain('http-equiv="Content-Security-Policy"');
    expect(html).toContain("frame-ancestors 'none'");
    expect(html).toContain('name="referrer" content="strict-origin-when-cross-origin"');
    expect(html).toContain('http-equiv="Permissions-Policy"');
    expect(html).toContain("geolocation=()");
    expect(html).toContain("microphone=()");
    expect(html).toContain("camera=()");
  });

  it("documents security baseline ownership and enforcement scope", () => {
    const markdown = fs.readFileSync(SECURITY_BASELINE_DOC_PATH, "utf8");

    expect(markdown).toContain("## Required Baseline Policies");
    expect(markdown).toContain("## Ownership and Enforcement");
    expect(markdown).toContain("contract tests");
  });
});
