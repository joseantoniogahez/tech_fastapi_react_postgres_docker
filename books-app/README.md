# books-app (Next.js Frontend)

Frontend for the Books App.

For full-stack orchestration and shared environment setup, see `../README.md`.
For backend-only setup and API details, see `../backend/README.md`.

## Tech Stack

- Next.js 16 (App Router)
- React 19
- Tailwind CSS 4
- Jest + Testing Library

## Requirements

- Node.js `>=20.9.0`
- npm `>=11`

## Setup

From `books-app/`:

```bash
npm install
```

## API Client Configuration

Environment variables consumed by frontend code:

- `NEXT_PUBLIC_API_ORIGIN` (example: `http://localhost:8000`)
- `NEXT_PUBLIC_API_BASE_PATH` (example: `/api` or `/`)

Defaults when variables are not set:

- `NEXT_PUBLIC_API_ORIGIN`: empty string
- `NEXT_PUBLIC_API_BASE_PATH`: `/api`

Examples:

```bash
# Windows PowerShell
$env:NEXT_PUBLIC_API_ORIGIN="http://localhost:8000"
$env:NEXT_PUBLIC_API_BASE_PATH="/api"

# macOS/Linux
export NEXT_PUBLIC_API_ORIGIN="http://localhost:8000"
export NEXT_PUBLIC_API_BASE_PATH="/api"
```

## Scripts

```bash
npm run dev        # development server
npm run test       # unit tests
npm run lint       # eslint
npm run typecheck  # TypeScript check
npm run check      # lint + typecheck + test
npm run build      # production build
npm run start      # run built app
```

## Notes

- If backend routes are exposed at root (`/books`, `/authors`), set `NEXT_PUBLIC_API_BASE_PATH=/`.
- If backend routes are exposed under a proxy prefix (`/api/...`), keep `NEXT_PUBLIC_API_BASE_PATH=/api`.
