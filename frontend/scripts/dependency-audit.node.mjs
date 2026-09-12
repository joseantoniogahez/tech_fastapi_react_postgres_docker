import assert from "node:assert/strict";
import { test } from "node:test";

import { evaluateDependencyAudit } from "./dependency-audit.mjs";

const policy = { max_high: 0, max_critical: 0 };

function auditResult({
  status = 0,
  signal = null,
  error = undefined,
  vulnerabilities = { info: 0, low: 0, moderate: 0, high: 0, critical: 0, total: 0 },
  report = undefined,
} = {}) {
  return {
    status,
    signal,
    error,
    stdout: JSON.stringify(
      report ?? {
        auditReportVersion: 2,
        metadata: { vulnerabilities },
      },
    ),
  };
}

test("accepts a valid audit report within policy", () => {
  const evaluation = evaluateDependencyAudit(auditResult(), policy);

  assert.equal(evaluation.ok, true);
  assert.match(evaluation.message, /high=0.*critical=0/);
});

test("applies project thresholds to a valid npm vulnerability exit", () => {
  const evaluation = evaluateDependencyAudit(
    auditResult({
      status: 1,
      vulnerabilities: { info: 0, low: 1, moderate: 0, high: 0, critical: 0, total: 1 },
    }),
    policy,
  );

  assert.equal(evaluation.ok, true);
});

test("rejects reports that exceed the project threshold", () => {
  const evaluation = evaluateDependencyAudit(
    auditResult({
      status: 1,
      vulnerabilities: { info: 0, low: 0, moderate: 0, high: 1, critical: 0, total: 1 },
    }),
    policy,
  );

  assert.equal(evaluation.ok, false);
  assert.match(evaluation.message, /Dependency audit failed: high=1/);
});

test("fails closed on npm operational error JSON", () => {
  const evaluation = evaluateDependencyAudit(
    auditResult({
      status: 1,
      report: { error: { code: "EAI_AGAIN", summary: "registry unavailable" } },
    }),
    policy,
  );

  assert.equal(evaluation.ok, false);
  assert.match(evaluation.message, /operational error report/);
});

test("fails closed on missing or malformed vulnerability metadata", () => {
  for (const report of [
    { auditReportVersion: 2 },
    { auditReportVersion: 2, metadata: { vulnerabilities: {} } },
    {
      auditReportVersion: 2,
      metadata: { vulnerabilities: { high: "0", critical: 0 } },
    },
  ]) {
    assert.equal(evaluateDependencyAudit(auditResult({ report }), policy).ok, false);
  }
});

test("fails closed when a non-governed severity count is invalid", () => {
  const evaluation = evaluateDependencyAudit(
    auditResult({
      status: 1,
      vulnerabilities: {
        info: 0,
        low: "invalid",
        moderate: 0,
        high: 0,
        critical: 0,
        total: 0,
      },
    }),
    policy,
  );

  assert.equal(evaluation.ok, false);
  assert.match(evaluation.message, /invalid low vulnerability count/);
});

test("fails closed when the vulnerability total is inconsistent", () => {
  const evaluation = evaluateDependencyAudit(
    auditResult({
      status: 1,
      vulnerabilities: { info: 0, low: 1, moderate: 0, high: 0, critical: 0, total: 0 },
    }),
    policy,
  );

  assert.equal(evaluation.ok, false);
  assert.match(evaluation.message, /inconsistent total vulnerability count/);
});

test("fails closed on a process error, unexpected status, or signal", () => {
  assert.equal(
    evaluateDependencyAudit(auditResult({ error: new Error("spawn failed") }), policy).ok,
    false,
  );
  assert.equal(evaluateDependencyAudit(auditResult({ status: 2 }), policy).ok, false);
  assert.equal(
    evaluateDependencyAudit(auditResult({ status: null, signal: "SIGTERM" }), policy).ok,
    false,
  );
});

test("fails closed on empty or non-JSON output", () => {
  assert.equal(
    evaluateDependencyAudit({ status: 1, signal: null, stdout: "" }, policy).ok,
    false,
  );
  assert.equal(
    evaluateDependencyAudit({ status: 1, signal: null, stdout: "not-json" }, policy).ok,
    false,
  );
});
