/// <reference types="node" />

import fs from "node:fs";
import path from "node:path";

import { FRONTEND_DIR } from "@/contracts/docs";

const POLICY_PATH = path.join(FRONTEND_DIR, "performance", "bundle_budget.json");
const DOC_PATH = path.join(FRONTEND_DIR, "docs", "operations", "performance_budget.md");

describe("performance budget contracts", () => {
  it("keeps bundle budget policy with required numeric thresholds", () => {
    const policy = JSON.parse(fs.readFileSync(POLICY_PATH, "utf8")) as Record<string, unknown>;

    const requiredNumericKeys = [
      "max_total_js_bytes",
      "max_total_js_gzip_bytes",
      "max_total_css_bytes",
      "max_total_css_gzip_bytes",
    ];

    for (const key of requiredNumericKeys) {
      expect(typeof policy[key]).toBe("number");
      expect((policy[key] as number) > 0).toBe(true);
    }
  });

  it("documents the budget gate commands and enforcement ownership", () => {
    const markdown = fs.readFileSync(DOC_PATH, "utf8");

    expect(markdown).toContain("## Budget Policy Source");
    expect(markdown).toContain("## Enforcement Rule");
    expect(markdown).toContain("## Commands");
    expect(markdown).toContain("npm --prefix frontend run build");
    expect(markdown).toContain("npm --prefix frontend run perf:check");
  });
});
