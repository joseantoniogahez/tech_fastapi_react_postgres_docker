# OpenAPI Documentation Pattern

## Goal

Keep routers readable while still providing rich Swagger UI docs at `http://localhost:8000/docs`.

## Current structure

- Common helpers: `app/openapi/common.py`
- Domain-specific docs:
  - `app/openapi/auth.py`
  - `app/openapi/books.py`
  - `app/openapi/authors.py`
  - `app/openapi/health.py`
- Routers consume those constants with `**DOC_CONSTANT`.

## Router pattern

Router modules should stay focused on behavior:

```python
@router.get("/", response_model=List[Book], **GET_BOOKS_DOC)
async def get_books(...):
    ...
```

Request parameter/body metadata is also defined in `app/openapi/*` via typed aliases:

```python
AuthorIdQuery = Annotated[
    Optional[int],
    Query(ge=1, description="Filter by author ID", examples=[1]),
]

AddBookPayload = Annotated[
    AddBook,
    Body(description="Payload to create a book.", examples=ADD_BOOK_BODY_EXAMPLES),
]
```

Router usage stays minimal:

```python
async def add_book(
    book_service: BookServiceDependency,
    _authorized_user: BookCreateAuthorizedUserDependency,
    book_data: AddBookPayload,
) -> Book:
    ...
```

## Naming conventions

- Endpoint metadata: `<ENDPOINT_NAME>_DOC`
  - Example: `GET_BOOK_DOC`, `UPDATE_CURRENT_USER_DOC`
- Request body examples: `<ENDPOINT_NAME>_BODY_EXAMPLES`
  - Example: `ADD_BOOK_BODY_EXAMPLES`
- Shared helpers:
  - `build_error_response`
  - `INTERNAL_ERROR_EXAMPLE`

## Recommended endpoint documentation checklist

1. `summary`
2. `description`
3. `response_description`
4. `responses` with realistic status codes
5. At least one success example
6. At least one representative error example for each expected status code
7. `WWW-Authenticate` header docs for `401` responses

## Error response consistency

Use `build_error_response(...)` from `app/openapi/common.py` to enforce:

- Stable payload schema
- Shared header docs for bearer challenges
- Consistent error examples across domains

## Adding docs for a new endpoint

1. Add documentation constants in the domain file under `app/openapi/`.
2. Export the constant(s) via `__all__`.
3. Import and apply them in the router decorator with `**CONSTANT`.
4. Add or update body/query/path examples as needed.
5. Run router tests to ensure behavior remains unchanged.

## Verification

After changes:

1. Open `http://localhost:8000/docs` and inspect rendered endpoint docs.
2. Run:

```bash
.\.venv\Scripts\python -m pytest backend/tests/routers -q -p no:cacheprovider
```
