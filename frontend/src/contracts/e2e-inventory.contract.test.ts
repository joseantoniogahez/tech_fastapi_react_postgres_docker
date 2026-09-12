/// <reference types="node" />

import fs from "node:fs";
import path from "node:path";

import { FRONTEND_DIR } from "@/contracts/docs";

const SPEC_PATH = path.join(FRONTEND_DIR, "e2e", "foundation-smoke.spec.ts");
const DOC_PATH = path.join(FRONTEND_DIR, "docs", "operations", "e2e_smoke_suite.md");
const SCENARIO_SECTION_PATTERN = /## Scenario Inventory\s+([\s\S]*?)\n## /;

describe("E2E scenario inventory contract", () => {
  it("keeps the documented and implemented scenario inventories exactly aligned", () => {
    const spec = fs.readFileSync(SPEC_PATH, "utf8");
    const markdown = fs.readFileSync(DOC_PATH, "utf8");
    const scenarioNames = [...spec.matchAll(/\btest\("([^"]+)"/g)].map((match) => match[1]);
    const scenarioSection = SCENARIO_SECTION_PATTERN.exec(markdown)?.[1];
    const documentedScenarioNames = [...(scenarioSection ?? "").matchAll(/^- `([^`]+)`$/gm)].map(
      (match) => match[1],
    );

    expect(scenarioNames.length).toBeGreaterThan(0);
    expect(documentedScenarioNames).toEqual(scenarioNames);
  });
});
