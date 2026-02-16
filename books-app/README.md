# books-app

Frontend for the books management app.

- Framework: Next.js 16 (App Router)
- UI: React 19
- Tests: Jest + Testing Library
- Styling: Tailwind CSS 4

## Requirements

- Node.js `>=20.9.0`
- npm `>=11`

## Setup

From `books-app/`:

```bash
npm install
```

Optional environment variables for API requests:

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

## Docker

This app is usually run from the repo root with Docker Compose:

```bash
docker compose up --build
```
