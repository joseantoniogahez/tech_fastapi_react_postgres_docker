# frontend (Vite + React)

Frontend SPA for landing, login, session validation, and RBAC admin flows.

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
- React Router 7
- TanStack Query 5
- Tailwind CSS 4
- Vitest + Testing Library
- Playwright (smoke e2e)

## Prerequisites

- Node.js `>=22.22.2 <23` (`22.23.1` is pinned in Docker/CI)
- npm `12.0.x` (`12.0.1` is pinned in Docker/CI)
- Python environment with backend dependencies installed when running `npm run check` (required by `openapi:check`).

The committed npm policy allows only the exact `esbuild@0.27.3` dependency install script and
fails installation if a new unreviewed install script appears.

OpenAPI sync uses the repository-root `.venv` by default. CI or another explicitly provisioned
environment without that directory can set `OPENAPI_PYTHON` to its governed Python executable.

## Environment Variables

Vite build inputs:

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

Vite embeds these values in the static assets during `npm run build`. The browser validates the
embedded configuration when the application starts. `VITE_API_ORIGIN` must be a canonical HTTP(S)
origin without credentials, an API path, a query string, or a fragment; put the API prefix in
`VITE_API_BASE_PATH`. Changing either value requires rebuilding and redeploying the bundle.

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

## Current Route Surface

See `docs/operations/route_inventory.md` for the canonical route and access-policy inventory.

## Testing and Quality Gates

Run from `frontend/`:

```bash
npm run lint
npm run typecheck
npm run test
npm run test:coverage
npm run test:a11y
npm run test:dependency-audit
npm run e2e:install
npm run test:e2e:ci
npm run check
```

Run `npm run e2e:install` once per machine before `npm run test:e2e` or `npm run test:e2e:ci`.

`npm run check` executes:

- lint
- typecheck
- coverage gate
- security-header generator and checker contract tests
- fail-closed dependency-audit contract tests
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

The production image also derives its `Content-Security-Policy` from the validated
`VITE_API_ORIGIN` during that build. Pinned `serve` sends the generated policy and the remaining
browser-security baseline as HTTP response headers. Container-start environment changes cannot
change the already-built bundle or CSP.

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
npm run test:dependency-audit # test fail-closed npm audit handling
npm run test:security-headers # test header generation and the HTTP checker
npm run e2e:install    # install Playwright Chromium locally
npm run test:e2e       # run Playwright smoke suite
npm run test:e2e:ci    # CI-equivalent Playwright smoke suite
npm run openapi:sync   # refresh frontend/contracts/openapi/backend_openapi.json
npm run openapi:check  # fail when backend OpenAPI artifact is stale
npm run deps:audit     # enforce dependency audit policy
npm run perf:check     # enforce bundle budget contract
npm run check          # lint + typecheck + coverage + openapi drift + dependency audit
npm run build          # build production bundle + performance budget gate
npm run preview        # serve production bundle locally
```

Inspect the real headers of an already-running production frontend, including its SPA fallback:

```bash
node scripts/security-headers-smoke.mjs http://127.0.0.1:3000 http://localhost:8000
```
