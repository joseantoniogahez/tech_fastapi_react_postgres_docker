import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FRONTEND_DIR = path.resolve(__dirname, "..");
const POLICY_PATH = path.join(FRONTEND_DIR, "security", "dependency_audit_policy.json");
const VULNERABILITY_SEVERITIES = ["info", "low", "moderate", "high", "critical"];

function failure(message) {
  return { ok: false, message };
}

function isNonNegativeInteger(value) {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

export function evaluateDependencyAudit(auditResult, policy) {
  const maxHigh = Number(policy.max_high ?? 0);
  const maxCritical = Number(policy.max_critical ?? 0);
  if (!isNonNegativeInteger(maxHigh) || !isNonNegativeInteger(maxCritical)) {
    return failure("Dependency audit policy contains invalid thresholds.");
  }

  if (auditResult.error) {
    return failure(`Dependency audit execution failed: ${auditResult.error.message}`);
  }
  if (auditResult.signal) {
    return failure(`Dependency audit execution was interrupted by ${auditResult.signal}.`);
  }
  if (auditResult.status !== 0 && auditResult.status !== 1) {
    return failure(`Dependency audit execution returned unexpected status ${auditResult.status}.`);
  }

  const stdout = auditResult.stdout?.trim() ?? "";
  if (!stdout) {
    return failure("Unable to parse npm audit output: empty stdout");
  }

  let parsedAudit;
  try {
    parsedAudit = JSON.parse(stdout);
  } catch {
    return failure("Unable to parse npm audit JSON output.");
  }

  if (!parsedAudit || typeof parsedAudit !== "object" || Array.isArray(parsedAudit)) {
    return failure("Unable to validate npm audit report structure.");
  }
  if (Object.hasOwn(parsedAudit, "error")) {
    return failure("npm audit returned an operational error report.");
  }
  if (!Number.isInteger(parsedAudit.auditReportVersion) || parsedAudit.auditReportVersion < 1) {
    return failure("npm audit report is missing a valid auditReportVersion.");
  }

  const vulnerabilities = parsedAudit.metadata?.vulnerabilities;
  if (!vulnerabilities || typeof vulnerabilities !== "object" || Array.isArray(vulnerabilities)) {
    return failure("npm audit report is missing vulnerability metadata.");
  }

  for (const severity of [...VULNERABILITY_SEVERITIES, "total"]) {
    if (!isNonNegativeInteger(vulnerabilities[severity])) {
      return failure(`npm audit report contains an invalid ${severity} vulnerability count.`);
    }
  }

  const severityTotal = VULNERABILITY_SEVERITIES.reduce(
    (sum, severity) => sum + vulnerabilities[severity],
    0,
  );
  if (vulnerabilities.total !== severityTotal) {
    return failure("npm audit report contains an inconsistent total vulnerability count.");
  }

  const highCount = vulnerabilities.high;
  const criticalCount = vulnerabilities.critical;
  if (highCount > maxHigh || criticalCount > maxCritical) {
    return failure(
      `Dependency audit failed: high=${highCount} (max ${maxHigh}), critical=${criticalCount} (max ${maxCritical})`,
    );
  }

  return {
    ok: true,
    message: `Dependency audit passed: high=${highCount} (max ${maxHigh}), critical=${criticalCount} (max ${maxCritical})`,
  };
}

export function main() {
  const policy = JSON.parse(fs.readFileSync(POLICY_PATH, "utf8"));
  const auditResult = spawnSync("npm audit --omit=dev --json", {
    cwd: FRONTEND_DIR,
    encoding: "utf8",
    env: process.env,
    shell: true,
  });
  const evaluation = evaluateDependencyAudit(auditResult, policy);
  const output = evaluation.ok ? console.log : console.error;
  output(evaluation.message);
  return evaluation.ok ? 0 : 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  process.exitCode = main();
}
