# Frontend Accessibility Gate Baseline

This document defines the automated accessibility quality gate for foundation routes.

## Scope

- Landing route (`/`)
- Login and registration routes (`/login`, `/register`)
- Loaded welcome and profile routes, including authenticated navigation and global logout
- Explicit not-found route state
- Protected error state for session validation failure (`/welcome` fallback UI)
- Selected admin routes, including users, assignments, permissions, and audit log.

## Automation Contract

- Baseline test file: `src/app/accessibility.routes.test.tsx`.
- Engine: `axe-core` running inside the frontend Vitest workflow.
- Token contrast contract: `src/contracts/accessibility-colors.contract.test.ts` verifies secondary
  text at 4.5:1 and control boundaries at 3:1 against every declared solid background and the
  maximum single-gradient washes.
- The jsdom axe gate does not calculate real-browser color contrast. Contrast and browser-specific
  behavior remain mandatory manual review checks unless a separately approved browser axe gate is added.
- Violations fail the test suite and therefore fail `npm --prefix frontend run check`.

## Commands

- Focused run: `npm --prefix frontend run test:a11y`
- Standard workflow run: `npm --prefix frontend run check`

## Reviewer Validation Checklist

- Any UI change on baseline routes keeps `test:a11y` green.
- Review secondary text on both solid surfaces and the body gradient at mobile and desktop widths.
- Review open navigation at 320 and 390 CSS pixels: it stacks above content below the `md`
  breakpoint, preserves usable fields, and closes after navigation. The E2E smoke covers profile,
  users, and roles for overflow and content width; desktop retains the sidebar.
- Review default control boundaries and the 2 px accent focus-visible outline on auth, profile, and
  administration fields.
- New UI states include semantic labels/headings and keyboard-safe controls.
- If accepted violations are temporarily allowed, they require explicit reviewer notes and follow-up task ID.

## Maintenance Rule

- When auth/routing error states change, update this gate coverage in the same pull request.
