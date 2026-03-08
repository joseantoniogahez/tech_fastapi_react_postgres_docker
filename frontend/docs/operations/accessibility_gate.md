# Frontend Accessibility Gate Baseline

This document defines the automated accessibility quality gate for foundation routes.

## Scope

- Landing route (`/`)
- Login route (`/login`)
- Protected error state for session validation failure (`/welcome` fallback UI)

## Automation Contract

- Baseline test file: `src/app/accessibility.routes.test.tsx`.
- Engine: `axe-core` running inside the frontend Vitest workflow.
- Violations fail the test suite and therefore fail `npm --prefix frontend run check`.

## Commands

- Focused run: `npm --prefix frontend run test:a11y`
- Standard workflow run: `npm --prefix frontend run check`

## Reviewer Validation Checklist

- Any UI change on baseline routes keeps `test:a11y` green.
- New UI states include semantic labels/headings and keyboard-safe controls.
- If accepted violations are temporarily allowed, they require explicit reviewer notes and follow-up task ID.

## Maintenance Rule

- When auth/routing error states change, update this gate coverage in the same pull request.
