# frontend (Vite + React)

Frontend SPA for authentication entry flow.

For full-stack orchestration and shared environment setup, see `../README.md`.
For backend API behavior and authentication rules, see `../backend/README.md`.

## Tech Stack

- Vite 7
- React 19 + TypeScript
- React Router
- TanStack Query
- Tailwind CSS 4
- Vitest + Testing Library

## Prerequisites

- Node.js `>=20.9.0`
- npm `>=11`

## Setup

From `frontend/`:

```bash
npm install
```

## Run Locally

From `frontend/`:

```bash
npm run dev
```

Frontend URL: `http://localhost:3000`

## API Client Configuration

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

## Scripts

```bash
npm run dev        # start development server
npm run lint       # run ESLint
npm run typecheck  # run TypeScript checks
npm run test       # run unit/integration tests
npm run test:watch # run tests in watch mode
npm run check      # lint + typecheck + test
npm run build      # build production bundle
npm run preview    # run production bundle locally
```
