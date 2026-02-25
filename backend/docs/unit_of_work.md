# Unit of Work (UoW) Implementation

## Why this project uses UoW

This backend applies Unit of Work to guarantee atomic writes across multiple repositories in one use case.

Without UoW, each repository method can commit independently and a multi-step operation may persist partial data.

With UoW, a use case either:

- commits once when all steps succeed, or
- rolls back all pending changes when any step fails.

## Where UoW is implemented

- Core class: `app/repositories/__init__.py` (`UnitOfWork`)
- DI provider: `app/dependencies/db.py` (`get_unit_of_work`)
- Service usage:
  - `app/services/book.py`
  - `app/services/author.py`
  - `app/services/auth.py`

## Core behavior

`UnitOfWork` is an async context manager:

```python
async with unit_of_work:
    # one use case
```

Key rules:

- `__aenter__` increases scope depth.
- `__aexit__` rolls back when an exception is raised.
- Nested scopes are supported:
  - only the outermost scope decides final commit.
  - if any nested scope fails, `rollback_only` is set and final commit is skipped.

This prevents accidental commit after an inner failure that was caught by outer code.

## Repository contract after UoW refactor

`BaseRepository` no longer commits in `create`, `update`, or `delete`.

Repository write methods now do:

- `flush` to push SQL and get DB-generated values (for example IDs)
- `refresh` when needed to return updated entity state

Final transaction decision is always delegated to `UnitOfWork`.

## How services use UoW

Write use cases wrap business logic with `async with self.unit_of_work`.

Examples:

- `BookService.add`, `BookService.update`, `BookService.delete`
- `AuthService.register`, `AuthService.update_current_user`
- `AuthorService.get_or_add`

### Cross-service atomicity example

`BookService.add` may call `AuthorService.get_or_add`.

Both services receive the same `UnitOfWork` instance from DI, so both repository operations share the same transaction.

Result:

- author creation + book creation commit together, or
- both changes rollback together.

## Rollback policy

- Primary rollback: handled by `UnitOfWork.__aexit__` on exceptions inside use-case scope.
- Defensive rollback: `get_db_session` also performs rollback if an exception escapes request handling.

## Dependency Injection wiring

`db.py` creates one request-scoped `AsyncSession` and `UnitOfWork`; repository and service modules reuse them:

- repositories
- `UnitOfWork`
- services that consume both

This guarantees repositories and UoW operate on the same SQLAlchemy session.

## Testing coverage

UoW behavior is verified in:

- `tests/test_repositories.py`:
  - commit on success
  - rollback on exception
  - nested scope behavior
- `tests/services/*`:
  - write methods execute inside UoW context
- `tests/routers/*`:
  - end-to-end write flows keep expected behavior
