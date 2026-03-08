import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";

const THIS_FILE = fileURLToPath(import.meta.url);
const SCRIPTS_DIR = path.dirname(THIS_FILE);
const FRONTEND_DIR = path.resolve(SCRIPTS_DIR, "..");
const DIST_ASSETS_DIR = path.join(FRONTEND_DIR, "dist", "assets");
const POLICY_PATH = path.join(FRONTEND_DIR, "performance", "bundle_budget.json");

const readPolicy = () => {
  const policyRaw = fs.readFileSync(POLICY_PATH, "utf8");
  return JSON.parse(policyRaw);
};

const collectAssetMetrics = (extension) => {
  if (!fs.existsSync(DIST_ASSETS_DIR)) {
    throw new Error(`Missing dist assets directory at '${DIST_ASSETS_DIR}'. Run 'npm --prefix frontend run build' first.`);
  }

  const assetNames = fs.readdirSync(DIST_ASSETS_DIR).filter((name) => name.endsWith(extension));
  let totalRawBytes = 0;
  let totalGzipBytes = 0;

  for (const assetName of assetNames) {
    const assetPath = path.join(DIST_ASSETS_DIR, assetName);
    const content = fs.readFileSync(assetPath);
    totalRawBytes += content.byteLength;
    totalGzipBytes += zlib.gzipSync(content).byteLength;
  }

  return {
    assetCount: assetNames.length,
    totalRawBytes,
    totalGzipBytes,
  };
};

const formatBytes = (value) => `${value.toLocaleString("en-US")} B`;

const evaluateBudget = ({ label, actual, limit }) => {
  const ok = actual <= limit;
  const status = ok ? "PASS" : "FAIL";
  console.log(
    `[${status}] ${label}: actual=${formatBytes(actual)} limit=${formatBytes(limit)}`,
  );
  return ok;
};

const policy = readPolicy();
const jsMetrics = collectAssetMetrics(".js");
const cssMetrics = collectAssetMetrics(".css");

console.log("Performance budget report:");
console.log(`- JS assets: ${jsMetrics.assetCount}`);
console.log(`- CSS assets: ${cssMetrics.assetCount}`);

const checks = [
  evaluateBudget({
    label: "total_js_bytes",
    actual: jsMetrics.totalRawBytes,
    limit: policy.max_total_js_bytes,
  }),
  evaluateBudget({
    label: "total_js_gzip_bytes",
    actual: jsMetrics.totalGzipBytes,
    limit: policy.max_total_js_gzip_bytes,
  }),
  evaluateBudget({
    label: "total_css_bytes",
    actual: cssMetrics.totalRawBytes,
    limit: policy.max_total_css_bytes,
  }),
  evaluateBudget({
    label: "total_css_gzip_bytes",
    actual: cssMetrics.totalGzipBytes,
    limit: policy.max_total_css_gzip_bytes,
  }),
];

if (checks.some((check) => !check)) {
  process.exitCode = 1;
} else {
  console.log("Performance budgets passed.");
}
