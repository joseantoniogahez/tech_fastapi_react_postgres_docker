/// <reference types="node" />

import fs from "node:fs";
import path from "node:path";

import {
  CODE_CHANGE_REQUEST_TEMPLATE_PATH,
  DOCS_DIR,
  FEATURE_REQUEST_TEMPLATE_PATH,
  FRONTEND_DOCS_INDEX_PATH,
  FRONTEND_FOUNDATION_STATUS_PATH,
  FRONTEND_PLAYBOOK_PATH,
  FRONTEND_DIR,
  INTEGRATION_REQUEST_TEMPLATE_PATH,
  REPO_DIR,
  REQUIRED_FOUNDATION_STATUS_SECTIONS,
  REQUIRED_PLAYBOOK_SECTIONS,
  REQUIRED_TEMPLATE_SECTIONS,
} from "@/contracts/docs";

const SECTION_HEADING_PATTERN_TEMPLATE = /^## (.+)$/gm;
const PATH_TOKEN_PATTERN = /`((?:frontend\/)?(?:src|docs)\/[A-Za-z0-9_./*-]+(?:\.[A-Za-z0-9]+)?)`/g;

const TEMPLATE_PATHS = [
  FEATURE_REQUEST_TEMPLATE_PATH,
  INTEGRATION_REQUEST_TEMPLATE_PATH,
  CODE_CHANGE_REQUEST_TEMPLATE_PATH,
] as const;

const collectMarkdownFiles = (rootPath: string): string[] => {
  const entries = fs.readdirSync(rootPath, { withFileTypes: true });

  return entries.flatMap((entry) => {
    const absolutePath = path.join(rootPath, entry.name);
    if (entry.isDirectory()) {
      return collectMarkdownFiles(absolutePath);
    }

    return entry.name.endsWith(".md") ? [absolutePath] : [];
  });
};

const readMarkdown = (filePath: string): string => fs.readFileSync(filePath, "utf8");

const toRelativeFrontendPath = (filePath: string): string => path.relative(FRONTEND_DIR, filePath).replace(/\\/g, "/");

const extractSectionHeadings = (markdown: string): Set<string> => {
  const headings = new Set<string>();
  let match = SECTION_HEADING_PATTERN_TEMPLATE.exec(markdown);

  while (match !== null) {
    headings.add(match[1].trim());
    match = SECTION_HEADING_PATTERN_TEMPLATE.exec(markdown);
  }

  SECTION_HEADING_PATTERN_TEMPLATE.lastIndex = 0;
  return headings;
};

const resolveDocTokenPath = (token: string): string => {
  if (token.startsWith("frontend/")) {
    return path.resolve(REPO_DIR, token);
  }

  return path.resolve(FRONTEND_DIR, token);
};

describe("documentation contracts", () => {
  it("keeps markdown path references valid for src/docs tokens", () => {
    const markdownFiles = collectMarkdownFiles(DOCS_DIR);
    const missingReferences: string[] = [];

    for (const markdownFile of markdownFiles) {
      const markdown = readMarkdown(markdownFile);
      const uniqueTokens = new Set<string>();
      let match = PATH_TOKEN_PATTERN.exec(markdown);

      while (match !== null) {
        uniqueTokens.add(match[1]);
        match = PATH_TOKEN_PATTERN.exec(markdown);
      }
      PATH_TOKEN_PATTERN.lastIndex = 0;

      for (const token of [...uniqueTokens].sort()) {
        if (token.includes("*") || token.includes("<") || token.includes(">")) {
          continue;
        }

        const resolvedPath = resolveDocTokenPath(token);
        if (fs.existsSync(resolvedPath)) {
          continue;
        }

        missingReferences.push(`${toRelativeFrontendPath(markdownFile)} -> ${token}`);
      }
    }

    expect(missingReferences).toEqual([]);
  });

  it("enforces required sections in frontend playbook", () => {
    expect(fs.existsSync(FRONTEND_PLAYBOOK_PATH)).toBe(true);

    const markdown = readMarkdown(FRONTEND_PLAYBOOK_PATH);
    const headings = extractSectionHeadings(markdown);

    const missingSections = REQUIRED_PLAYBOOK_SECTIONS.filter((section) => !headings.has(section));
    expect(missingSections).toEqual([]);
  });

  it("enforces required sections in request templates", () => {
    const missingTemplateFiles = TEMPLATE_PATHS.filter((templatePath) => !fs.existsSync(templatePath));
    expect(missingTemplateFiles).toEqual([]);

    const missingTemplateSections: string[] = [];
    for (const templatePath of TEMPLATE_PATHS) {
      const markdown = readMarkdown(templatePath);
      const headings = extractSectionHeadings(markdown);

      for (const section of REQUIRED_TEMPLATE_SECTIONS) {
        if (headings.has(section)) {
          continue;
        }

        missingTemplateSections.push(`${toRelativeFrontendPath(templatePath)} -> ${section}`);
      }
    }

    expect(missingTemplateSections).toEqual([]);
  });

  it("enforces required sections in frontend foundation status doc", () => {
    expect(fs.existsSync(FRONTEND_FOUNDATION_STATUS_PATH)).toBe(true);

    const markdown = readMarkdown(FRONTEND_FOUNDATION_STATUS_PATH);
    const headings = extractSectionHeadings(markdown);
    const missingSections = REQUIRED_FOUNDATION_STATUS_SECTIONS.filter((section) => !headings.has(section));

    expect(missingSections).toEqual([]);
  });

  it("keeps docs index linked to foundation status doc", () => {
    const indexMarkdown = readMarkdown(FRONTEND_DOCS_INDEX_PATH);

    expect(indexMarkdown).toContain("foundation_status.md");
  });
});
