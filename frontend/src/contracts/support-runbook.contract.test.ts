/// <reference types="node" />

import fs from "node:fs";
import path from "node:path";

import { FRONTEND_DIR } from "@/contracts/docs";

const RUNBOOK_PATH = path.join(FRONTEND_DIR, "docs", "operations", "support_diagnostics_runbook.md");

describe("support diagnostics runbook contracts", () => {
  it("keeps required triage and taxonomy sections", () => {
    const markdown = fs.readFileSync(RUNBOOK_PATH, "utf8");

    expect(markdown).toContain("## Triage Flow");
    expect(markdown).toContain("## Error Taxonomy and Actions");
    expect(markdown).toContain("## Required Incident Artifact");
  });

  it("documents the baseline frontend error taxonomy", () => {
    const markdown = fs.readFileSync(RUNBOOK_PATH, "utf8");

    expect(markdown).toContain("`unauthorized`");
    expect(markdown).toContain("`forbidden`");
    expect(markdown).toContain("`internal_error`");
    expect(markdown).toContain("`network_error`");
    expect(markdown).toContain("`invalid_input`");
    expect(markdown).toContain("request_id");
  });
});
