# Dependency Injection Guide (FastAPI Native)

## 1) Dependency module layout

Dependency providers are centralized in `app/dependencies/providers.py`:

- `get_db_session`: creates and yields `AsyncSession`.
- Repository providers:
  - `get_book_repository`
  - `get_author_repository`
  - `get_auth_repository`
- Service providers:
  - `get_books_service`
  - `get_authors_service`
  - `get_auth_service`
- Auth providers:
  - `get_auth_credentials`
  - `get_current_user`
  - `get_current_active_user`

Authorization-specific providers are in `app/dependencies/authorization.py`.

## 2) Typed aliases used in routers

- Service aliases:
  - `BookServiceDependency`
  - `AuthorServiceDependency`
  - `AuthServiceDependency`
- User aliases:
  - `CurrentUserDependency`
  - `CurrentActiveUserDependency`
- Permission aliases:
  - `BookCreateAuthorizedUserDependency`
  - `BookUpdateAuthorizedUserDependency`
  - `BookDeleteAuthorizedUserDependency`

## 3) Endpoint examples

### `POST /books/`

```python
@router.post("/", response_model=Book, **ADD_BOOK_DOC)
async def add_book(
    book_service: BookServiceDependency,
    _authorized_user: BookCreateAuthorizedUserDependency,
    book_data: AddBook = Body(...),
) -> Book:
    book = await book_service.add(book_data)
    return Book.model_validate(book)
```

### `PUT /books/{id}`

```python
@router.put("/{id}", response_model=Optional[Book], **UPDATE_BOOK_DOC)
async def update_book(
    book_service: BookServiceDependency,
    _authorized_user: BookUpdateAuthorizedUserDependency,
    id: int = Path(..., ge=1),
    book_data: UpdateBook = Body(...),
) -> Optional[Book]:
    book = await book_service.update(id, book_data)
    return Book.model_validate(book) if book else None
```

## 4) Test overrides with `app.dependency_overrides`

### Override DB session

```python
from app.dependencies import get_db_session
from app.main import app

async def override_db_session():
    async with mock_database.Session() as session:
        yield session

app.dependency_overrides[get_db_session] = override_db_session
```

### Override a service provider

```python
from app.dependencies import get_auth_service

class FakeAuthService:
    async def login(self, credentials):
        return Token(access_token="fake-token")

app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
```

### Cleanup

Always clear overrides during teardown:

```python
app.dependency_overrides.clear()
```
