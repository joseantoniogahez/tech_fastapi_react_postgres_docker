# Dependency Injection Guide (FastAPI Native)

## 1) Dependency module layout

Dependency providers are split by concern under `app/dependencies/`:

- `db.py`
  - `get_db_session`
  - `get_unit_of_work`
- `repositories.py`
  - `get_book_repository`
  - `get_author_repository`
  - `get_auth_repository`
- `services.py`
  - `get_book_service`
  - `get_author_service`
  - `get_auth_service`
  - `get_auth_settings`
- `authentication.py`
  - `get_auth_credentials`
  - `get_current_user`
  - `get_current_active_user`
- `authorization.py`
  - generic policy builders (`require_permission`, `require_authorized_user`)
- `authorization_books.py`
  - book-specific authorization aliases

## 2) Typed aliases used in routers

- Service aliases:
  - `BookServiceDependency`
  - `AuthorServiceDependency`
  - `AuthServiceDependency`
- Transaction alias:
  - `UnitOfWorkDependency`
- User aliases:
  - `CurrentUserDependency`
  - `CurrentActiveUserDependency`
- Permission aliases:
  - `BookCreateAuth`
  - `BookUpdateAuth`
  - `BookDeleteAuth`

## 3) Endpoint examples

### `POST /books/`

```python
from app.schemas.application.book import BookMutationCommand

@router.post("/", response_model=BookResponse, **CREATE_BOOK_DOC)
async def create_book(
    book_service: BookServiceDependency,
    _authorized_user: BookCreateAuth,
    book_data: CreateBookRequest = Body(...),
) -> BookResponse:
    book = await book_service.create(
        BookMutationCommand(
            title=book_data.title,
            year=book_data.year,
            status=book_data.status,
            author_id=book_data.author_id,
            author_name=book_data.author_name,
        )
    )
    return BookResponse.model_validate(book)
```

### `PUT /books/{book_id}`

```python
from app.schemas.application.book import BookMutationCommand

@router.put("/{book_id}", response_model=BookResponse, **UPDATE_BOOK_DOC)
async def update_book(
    book_service: BookServiceDependency,
    _authorized_user: BookUpdateAuth,
    book_id: int = Path(..., ge=1),
    book_data: UpdateBookRequest = Body(...),
) -> BookResponse:
    book = await book_service.update(
        book_id,
        BookMutationCommand(
            title=book_data.title,
            year=book_data.year,
            status=book_data.status,
            author_id=book_data.author_id,
            author_name=book_data.author_name,
        ),
    )
    if book is None:
        raise NotFoundException(message=f"Book {book_id} not found", details={"book_id": book_id})
    return BookResponse.model_validate(book)
```

## 4) How DI enables one transaction per use case

`get_db_session` creates one `AsyncSession` per request. That same session is reused by:

- repository providers
- `get_unit_of_work`
- service providers

This guarantees repositories and Unit of Work share the same transaction context.

Practical effect:

- success path: one final commit at Unit of Work exit
- failure path: rollback for all pending writes in scope

See `unit_of_work.md` for detailed behavior.

## 5) Test overrides with `app.dependency_overrides`

### Override DB session

```python
from app.dependencies.db import get_db_session
from app.main import app

async def override_db_session():
    async with mock_database.Session() as session:
        yield session

app.dependency_overrides[get_db_session] = override_db_session
```

### Override a service provider

```python
from app.dependencies.services import get_auth_service
from app.schemas.application.auth import AccessTokenResult

class FakeAuthService:
    async def login(self, credentials):
        return AccessTokenResult(access_token="fake-token")

app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
```

### Cleanup

Always clear overrides during teardown:

```python
app.dependency_overrides.clear()
```
