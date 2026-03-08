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

const PYTHON_CODE = `
import json
from app.main import app
print(json.dumps(app.openapi(), sort_keys=True, indent=2, ensure_ascii=False))
`;

const execute = (command, args) =>
  spawnSync(command, args, {
    cwd: BACKEND_DIR,
    encoding: "utf8",
    env: process.env,
  });

const runPythonExport = () => {
  const candidates = process.env.BACKEND_PYTHON_BIN
    ? [[process.env.BACKEND_PYTHON_BIN, ["-c", PYTHON_CODE]]]
    : process.env.PYTHON_BIN
    ? [[process.env.PYTHON_BIN, ["-c", PYTHON_CODE]]]
    : [
        [VENV_PYTHON_WINDOWS, ["-c", PYTHON_CODE]],
        [VENV_PYTHON_POSIX, ["-c", PYTHON_CODE]],
        ["python", ["-c", PYTHON_CODE]],
        ["python3", ["-c", PYTHON_CODE]],
        ["py", ["-3", "-c", PYTHON_CODE]],
      ];

  const errors = [];
  for (const [command, args] of candidates) {
    const result = execute(command, args);
    if (result.status === 0 && result.stdout.trim()) {
      return result.stdout;
    }

    const stderr = result.stderr?.trim();
    const stdout = result.stdout?.trim();
    errors.push(`${command} ${args.join(" ")} -> ${stderr || stdout || `exit=${result.status}`}`);
  }

  throw new Error(`Unable to export backend OpenAPI.\n${errors.join("\n")}`);
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
