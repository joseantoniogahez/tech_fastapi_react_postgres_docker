# books-app (Next.js Frontend)

Frontend application for the Books App.

For full-stack orchestration and shared environment setup, see `../README.md`.
For backend setup and API behavior, see `../backend/README.md`.

## Tech Stack

- Next.js 16 (App Router)
- React 19
- Tailwind CSS 4
- Jest + Testing Library

## Prerequisites

- Node.js `>=20.9.0`
- npm `>=11`

## Setup

From `books-app/`:

```bash
npm install
```

## Run Locally

From `books-app/`:

```bash
npm run dev
```

Frontend URL: `http://localhost:3000`

## API Client Configuration

Frontend runtime variables:

- `NEXT_PUBLIC_API_ORIGIN` (example: `http://localhost:8000`)
- `NEXT_PUBLIC_API_BASE_PATH` (example: `/` or `/api`)

Defaults when unset:

- `NEXT_PUBLIC_API_ORIGIN`: empty string
- `NEXT_PUBLIC_API_BASE_PATH`: `/`

Behavior notes:

- `NEXT_PUBLIC_*` values are exposed to browser-side code.
- `NEXT_PUBLIC_API_BASE_PATH` is normalized (`/`, empty string, and `//` resolve to root calls with no prefix).
- In Docker builds, these values are embedded in the build output; rebuild frontend image after changing them.

Examples:

```bash
# Windows PowerShell
$env:NEXT_PUBLIC_API_ORIGIN="http://localhost:8000"
$env:NEXT_PUBLIC_API_BASE_PATH="/"

# macOS/Linux
export NEXT_PUBLIC_API_ORIGIN="http://localhost:8000"
export NEXT_PUBLIC_API_BASE_PATH="/"
```

## Scripts

```bash
npm run dev        # start development server
npm run test       # run unit tests
npm run test:watch # run unit tests in watch mode
npm run lint       # run ESLint
npm run typecheck  # run TypeScript checks
npm run check      # lint + typecheck + test
npm run build      # build production bundle
npm run start      # run built app
```

## Testing

From `books-app/`:

```bash
npm test
```

## Build and Run Production Bundle

From `books-app/`:

```bash
npm run build
npm run start
```

## API Path Notes

- Canonical local contract uses root routes (`/books`, `/authors`), so `NEXT_PUBLIC_API_BASE_PATH=/`.
- If a proxy exposes backend routes behind `/api/...`, override to `NEXT_PUBLIC_API_BASE_PATH=/api`.
