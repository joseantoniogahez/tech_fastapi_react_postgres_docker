# Unit of Work (UoW) Implementation

## Why this project uses UoW

This backend applies Unit of Work to guarantee atomic writes across multiple repositories in one use case.

Without UoW, each repository method can commit independently and a multi-step operation may persist partial data.

With UoW, a use case either:

- commits once when all steps succeed, or
- rolls back all pending changes when any step fails.

## Where UoW is implemented

- Core class: `app/core/db/uow.py` (`UnitOfWork`)
- Port contract: `app/core/db/ports.py` (`UnitOfWorkPort`)
- DI provider: `app/core/setup/dependencies.py` (`get_unit_of_work`)
- Service usage:
  - `app/features/auth/service.py`
  - `app/features/rbac/service.py`
  - `app/features/outbox/service.py`

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

`BaseRepository` (`app/core/db/repository_base.py`) does not commit in `create`, `update`, or `delete`.

Repository write methods now do:

- `flush` to push SQL and get DB-generated values (for example IDs)
- `refresh` when needed to return updated entity state

Final transaction decision is always delegated to `UnitOfWork`.

## How services use UoW

Write use cases wrap business logic with `async with self.unit_of_work`.

Examples in current code:

- `AuthService.register`
- `AuthProfileUpdates.persist_user_changes` (called by `AuthService.update_current_user`)
- `RBACService` write methods (create/update/delete/assignment operations)
- `OutboxService.enqueue` and `OutboxService.mark_published`

## Rollback policy

- Primary rollback: handled by `UnitOfWork.__aexit__` on exceptions inside use-case scope.
- Defensive rollback: `get_db_session` also performs rollback if an exception escapes request handling.

## Dependency Injection wiring

`app/core/setup/dependencies.py` creates one request-scoped `AsyncSession` and `UnitOfWork`; repository and service modules reuse them:

- repositories
- `UnitOfWork`
- services that consume both

This guarantees repositories and UoW operate on the same SQLAlchemy session.

## Testing coverage

UoW behavior is verified in:

- `backend/tests/repositories/test_unit_of_work.py`:
  - commit on success
  - rollback on exception
  - nested scope behavior
- `backend/tests/services/*`:
  - write methods execute inside UoW context
- `backend/tests/routers/*`:
  - end-to-end write flows keep expected behavior
