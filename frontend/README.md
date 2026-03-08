# frontend (Vite + React)

Frontend SPA for authentication entry flow.

For full-stack orchestration and shared environment setup, see `../README.md`.
For backend API behavior and authentication rules, see `../backend/README.md`.

## Technical Documentation Map

- `docs/frontend_playbook.md`: canonical frontend engineering rules, AI protocol, and reviewer checklist.
- `docs/foundation_status.md`: canonical snapshot of current frontend foundation state and quality gates.
- `docs/README.md`: role-based docs index and reading order.
- `docs/operations/*.md`: runtime and quality contracts (routing, API sync, security, accessibility, performance, observability).
- `docs/templates/*.md`: templates to request AI-driven features, integrations, and code changes.

## Tech Stack

- Vite 7
- React 19 + TypeScript
- React Router
- TanStack Query
- Tailwind CSS 4
- Vitest + Testing Library
- Playwright (smoke e2e)

## Prerequisites

- Node.js `>=20.9.0`
- npm `>=11`
- Python environment with backend dependencies installed when running `npm run check` (required by `openapi:check`).

## Environment Variables

Frontend runtime variables:

- `VITE_API_ORIGIN` (example: `http://localhost:8000`)
- `VITE_API_BASE_PATH` (example: `/v1`)

Defaults when unset:

- `VITE_API_ORIGIN`: `http://localhost:8000`
- `VITE_API_BASE_PATH`: `/v1`

Examples:

```bash
# Windows PowerShell
$env:VITE_API_ORIGIN="http://localhost:8000"
$env:VITE_API_BASE_PATH="/v1"

# macOS/Linux
export VITE_API_ORIGIN="http://localhost:8000"
export VITE_API_BASE_PATH="/v1"
```

## Development Environment

Install dependencies from `frontend/`:

```bash
npm install
```

Run dev server:

```bash
npm run dev
```

Frontend URL: `http://localhost:3000`

## Testing and Quality Gates

Run from `frontend/`:

```bash
npm run lint
npm run typecheck
npm run test
npm run test:coverage
npm run test:a11y
npm run test:e2e:ci
npm run check
```

`npm run check` executes:

- lint
- typecheck
- coverage gate
- OpenAPI artifact freshness gate (`openapi:check`)
- dependency audit gate (`deps:audit`)

Recommended CI-equivalent frontend gate:

```bash
npm run check && npm run test:e2e:ci && npm run build
```

## Production Build and Runtime

Build optimized static assets from `frontend/`:

```bash
npm run build
```

Preview local production build:

```bash
npm run preview
```

Important: Vite variables are resolved at build time. If `VITE_API_ORIGIN` or `VITE_API_BASE_PATH` changes, rebuild before releasing.

For containerized production deployment, use repository-level compose commands from `../README.md`.

## Scripts

```bash
npm run dev            # start development server
npm run lint           # run ESLint
npm run typecheck      # run TypeScript checks
npm run test           # run unit/integration tests
npm run test:coverage  # run tests with coverage thresholds
npm run test:watch     # run tests in watch mode
npm run test:a11y      # run accessibility route baseline tests
npm run test:e2e       # run Playwright smoke suite
npm run test:e2e:ci    # CI-equivalent Playwright smoke suite
npm run check          # lint + typecheck + coverage + openapi drift + dependency audit
npm run build          # build production bundle + performance budget gate
npm run preview        # serve production bundle locally
```
