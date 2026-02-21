# Dependency Injection Guide (FastAPI Native)

## 1) Dependencies module

All providers are centralized in `app/dependencies.py`:

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
- Typed aliases for endpoint injection:
  - `BookServiceDependency`, `AuthorServiceDependency`, `AuthServiceDependency`
  - `CurrentUserDependency`, `CurrentActiveUserDependency`
  - `BookCreateAuthorizedUserDependency`, `BookUpdateAuthorizedUserDependency`, `BookDeleteAuthorizedUserDependency`

## 2) Endpoint examples

### `POST /books`

```python
@router.post("/")
async def add_book(
    book_data: AddBook,
    book_service: BookServiceDependency,
    _authorized_user: BookCreateAuthorizedUserDependency,
) -> Book:
    book = await book_service.add(book_data)
    return Book.model_validate(book)
```

### `PUT /books/{id}`

```python
@router.put("/{id}")
async def update_book(
    id: int,
    book_data: UpdateBook,
    book_service: BookServiceDependency,
    _authorized_user: BookUpdateAuthorizedUserDependency,
) -> Optional[Book]:
    book = await book_service.update(id, book_data)
    return Book.model_validate(book) if book else None
```

## 3) Quick tests guide with overrides/mocks

Use FastAPI native overrides through `app.dependency_overrides`.

### Override DB session

```python
from app.dependencies import get_db_session
from app.main import app

async def override_db_session():
    async with mock_database.Session() as session:
        yield session

app.dependency_overrides[get_db_session] = override_db_session
```

### Override service with a fake

```python
from app.dependencies import get_auth_service

class FakeAuthService:
    async def login(self, credentials):
        return Token(access_token="fake-token")

app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
```

### Cleanup

Always clear overrides at test teardown:

```python
app.dependency_overrides.clear()
```
