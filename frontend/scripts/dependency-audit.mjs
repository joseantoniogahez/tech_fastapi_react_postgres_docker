import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FRONTEND_DIR = path.resolve(__dirname, "..");
const POLICY_PATH = path.join(FRONTEND_DIR, "security", "dependency_audit_policy.json");

const policy = JSON.parse(fs.readFileSync(POLICY_PATH, "utf8"));
const maxHigh = Number(policy.max_high ?? 0);
const maxCritical = Number(policy.max_critical ?? 0);

const auditResult = spawnSync("npm audit --omit=dev --json", {
  cwd: FRONTEND_DIR,
  encoding: "utf8",
  env: process.env,
  shell: true,
});

if (auditResult.error) {
  console.error(`Dependency audit execution failed: ${auditResult.error.message}`);
  process.exit(1);
}

const stdout = auditResult.stdout?.trim() ?? "";
if (!stdout) {
  console.error("Unable to parse npm audit output: empty stdout");
  process.exit(1);
}

let parsedAudit;
try {
  parsedAudit = JSON.parse(stdout);
} catch {
  console.error("Unable to parse npm audit JSON output.");
  process.exit(1);
}

const vulnerabilities = parsedAudit.metadata?.vulnerabilities ?? {};
const highCount = Number(vulnerabilities.high ?? 0);
const criticalCount = Number(vulnerabilities.critical ?? 0);

if (highCount > maxHigh || criticalCount > maxCritical) {
  console.error(
    `Dependency audit failed: high=${highCount} (max ${maxHigh}), critical=${criticalCount} (max ${maxCritical})`,
  );
  process.exit(1);
}

console.log(
  `Dependency audit passed: high=${highCount} (max ${maxHigh}), critical=${criticalCount} (max ${maxCritical})`,
);
