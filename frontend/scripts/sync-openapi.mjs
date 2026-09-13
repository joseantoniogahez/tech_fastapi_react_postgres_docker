import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const REPO_DIR = path.resolve(__dirname, "..", "..");
const BACKEND_DIR = path.join(REPO_DIR, "backend");
const OUTPUT_PATH = path.join(REPO_DIR, "frontend", "contracts", "openapi", "backend_openapi.json");
const IS_CHECK_MODE = process.argv.includes("--check");
const VENV_PYTHON_WINDOWS = path.join(REPO_DIR, ".venv", "Scripts", "python.exe");
const VENV_PYTHON_POSIX = path.join(REPO_DIR, ".venv", "bin", "python");
const explicitPython = process.env.OPENAPI_PYTHON?.trim();
const EXPLICIT_PYTHON =
  explicitPython && /[\\/]/u.test(explicitPython) && !path.isAbsolute(explicitPython)
    ? path.resolve(REPO_DIR, explicitPython)
    : explicitPython;

const PYTHON_CODE = `
import json
from app.main import app
print(json.dumps(app.openapi(), sort_keys=True, indent=2, ensure_ascii=False))
`;

const execute = (command, args) =>
  spawnSync(command, args, {
    cwd: BACKEND_DIR,
    encoding: "utf8",
    env: { ...process.env, APP_ENV: "test" },
  });

const runPythonExport = () => {
  const command =
    EXPLICIT_PYTHON ||
    [VENV_PYTHON_WINDOWS, VENV_PYTHON_POSIX].find((candidate) => fs.existsSync(candidate));
  if (!command) {
    throw new Error(
      "Repository root .venv Python not found. Create .venv or explicitly set OPENAPI_PYTHON.",
    );
  }

  const result = execute(command, ["-c", PYTHON_CODE]);
  if (result.status === 0 && result.stdout.trim()) {
    return result.stdout;
  }
  const detail = result.stderr?.trim() || result.stdout?.trim() || `exit=${result.status}`;
  throw new Error(`Unable to export backend OpenAPI with ${command}.\n${detail}`);
};

const normalizeJson = (text) => `${JSON.stringify(JSON.parse(text), null, 2)}\n`;

const exportedJson = normalizeJson(runPythonExport());
const outputDir = path.dirname(OUTPUT_PATH);
const existingJson = fs.existsSync(OUTPUT_PATH) ? fs.readFileSync(OUTPUT_PATH, "utf8") : null;

if (IS_CHECK_MODE) {
  if (existingJson === null) {
    console.error(`OpenAPI artifact not found: ${OUTPUT_PATH}`);
    console.error("Run: npm --prefix frontend run openapi:sync");
    process.exit(1);
  }

  const normalizedExistingJson = normalizeJson(existingJson);
  if (normalizedExistingJson !== exportedJson) {
    console.error("OpenAPI artifact is stale.");
    console.error("Run: npm --prefix frontend run openapi:sync");
    process.exit(1);
  }

  console.log("OpenAPI artifact is up to date.");
  process.exit(0);
}

fs.mkdirSync(outputDir, { recursive: true });
fs.writeFileSync(OUTPUT_PATH, exportedJson, "utf8");
console.log(`OpenAPI artifact written: ${OUTPUT_PATH}`);
