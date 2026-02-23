# API Endpoints

Base path is root (`/`) unless a reverse proxy rewrites paths. `API_PATH` only affects FastAPI `root_path` metadata.

## Health

- `GET /health`

## Authentication and Users

- `POST /token`
  - Login using `application/x-www-form-urlencoded` (`username`, `password`)
  - Returns bearer token
- `POST /users/register`
  - Creates a new active user
- `GET /users/me`
  - Requires `Authorization: Bearer <access_token>`
- `PATCH /users/me`
  - Requires `Authorization: Bearer <access_token>`
  - Supports username and password changes

Authentication details and examples: `authentication.md`.

## Authors

- `GET /authors/`

## Books

- `GET /books/`
  - Optional query param: `author_id`
- `GET /books/published`
- `GET /books/{id}`
- `POST /books/` (requires permission `books:create`)
- `PUT /books/{id}` (requires permission `books:update`)
- `DELETE /books/{id}` (requires permission `books:delete`)

Book status values:

- `published`
- `draft`
