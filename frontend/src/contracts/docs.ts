/// <reference types="node" />

import path from "node:path";
import { fileURLToPath } from "node:url";

const THIS_FILE = fileURLToPath(import.meta.url);
const THIS_DIR = path.dirname(THIS_FILE);

export const FRONTEND_DIR = path.resolve(THIS_DIR, "..", "..");
export const REPO_DIR = path.resolve(FRONTEND_DIR, "..");
export const DOCS_DIR = path.join(FRONTEND_DIR, "docs");
export const TEMPLATES_DIR = path.join(DOCS_DIR, "templates");

export const FRONTEND_PLAYBOOK_PATH = path.join(DOCS_DIR, "frontend_playbook.md");
export const FRONTEND_DOCS_INDEX_PATH = path.join(DOCS_DIR, "README.md");
export const FRONTEND_FOUNDATION_STATUS_PATH = path.join(DOCS_DIR, "foundation_status.md");

export const FEATURE_REQUEST_TEMPLATE_PATH = path.join(TEMPLATES_DIR, "feature_request.md");
export const INTEGRATION_REQUEST_TEMPLATE_PATH = path.join(TEMPLATES_DIR, "integration_request.md");
export const CODE_CHANGE_REQUEST_TEMPLATE_PATH = path.join(TEMPLATES_DIR, "code_change_request.md");

export const REQUIRED_PLAYBOOK_SECTIONS = [
  "Architecture Map",
  "Non-Negotiable Rules",
  "Query Policy Matrix",
  "Request and Template Conventions",
  "AI Operating Protocol",
  "Reviewer Checklist",
] as const;

export const REQUIRED_TEMPLATE_SECTIONS = [
  "How to Use This Template With the AI Assistant",
  "Problem and Goal",
  "Scope (In / Out)",
  "API, Auth, Routing, and State Implications",
  "UX, Accessibility, and Error Handling",
  "Acceptance Criteria",
  "AI Execution Constraints (Required)",
  "Required Tests and Validation",
  "Reviewer Validation Checklist",
] as const;

export const REQUIRED_FOUNDATION_STATUS_SECTIONS = [
  "Purpose",
  "Current Foundation Snapshot",
  "Active Guardrails",
  "Required Validation Gates",
  "Change Management Rules",
] as const;
