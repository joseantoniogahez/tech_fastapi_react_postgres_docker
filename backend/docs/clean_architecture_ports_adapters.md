# Clean Architecture: Ports, Adapters, and DIP

This guide explains how this backend applies:

- Dependency Inversion Principle (DIP) with `Protocol` ports
- Ports & Adapters style (services depend on contracts)
- Composition Root in dependency modules (object graph wiring outside services)
- Explicit layer contracts (`*RepositoryPort`, `*ServicePort`, `UnitOfWorkPort`)

## 1) Current Backend Map

### Ports (contracts)

- `app/services/__init__.py`
  - `UnitOfWorkPort`
- `app/services/author.py`
  - `AuthorRepositoryPort`
  - `AuthorServicePort`
- `app/services/book.py`
  - `BookRepositoryPort`
  - `BookServicePort`
- `app/services/auth.py`
  - `AuthRepositoryPort`
  - `AuthServicePort`

### Adapters (concrete implementations)

- `app/repositories/author.py` implements `AuthorRepositoryPort`
- `app/repositories/book.py` implements `BookRepositoryPort`
- `app/repositories/auth.py` implements `AuthRepositoryPort`
- `app/repositories/__init__.py` (`UnitOfWork`) implements `UnitOfWorkPort`

### Composition Root

- `app/dependencies/db.py`
  - Builds request-scoped `AsyncSession` and `UnitOfWork`
- `app/dependencies/repositories.py`
  - Wires concrete repository adapters
- `app/dependencies/services.py`
  - Wires service implementations through ports
- `app/dependencies/authentication.py`
  - Wires token and current-user dependencies
- `app/dependencies/authorization.py` + `authorization_books.py`
  - Wires generic and resource-specific authorization dependencies

## 2) How to Use It Day to Day

Operational rules:

1. In services, type dependencies as ports, not concrete classes.
1. Do not instantiate services inside other services.
1. Keep composition and wiring in dependency modules (`db.py`, `repositories.py`, `services.py`, etc.).
1. Keep transaction boundaries at use-case level with `async with unit_of_work`.

Real example:

- `BookService` depends on `BookRepositoryPort`, `AuthorServicePort`, and `UnitOfWorkPort`.
- `BookService` does not create `AuthorService`; `get_books_service` injects it.

## 3) How to Modify Safely

When changing an existing use case:

1. Update the port first (method signatures in `Protocol`).
1. Update concrete implementation(s) to satisfy the contract.
1. Wire the change in dependency composition modules (`app/dependencies/*.py`).
1. Update unit tests to mock the updated port methods.
1. Run service tests first, then router/integration tests.

Recommended order: contract -> adapter -> composition -> tests.

## 4) How to Extend with a New Module

Assume you add `Publisher`.

### Step A: Define ports

Create `app/services/publisher.py` with:

- `PublisherRepositoryPort`
- `PublisherServicePort`
- `PublisherService` (depending only on ports)

### Step B: Implement concrete adapter

Create `app/repositories/publisher.py` implementing `PublisherRepositoryPort`.

### Step C: Compose in dependency modules

In dependency composition modules add:

- `get_publisher_repository() -> PublisherRepositoryPort`
- `get_publishers_service() -> PublisherServicePort`
- `PublisherServiceDependency = Annotated[PublisherServicePort, Depends(...)]`

### Step D: Use from routers

Inject `PublisherServiceDependency` in endpoints without importing concrete classes.

## 5) Anti-patterns to Avoid

1. Importing concrete repositories in services just for typing.
1. Instantiating one service inside another (`SomeService()` in `OtherService`).
1. Moving business logic to providers (providers should only wire dependencies).
1. Skipping `UnitOfWork` for write use cases.

## 6) Recommended Testing Strategy

### Service unit tests

- Mock ports (`MagicMock` / `AsyncMock`)
- Assert behavior through contract methods
- Avoid coupling tests to SQLAlchemy details

### Integration tests

- Validate real composition in dependency modules (`db.py`, `repositories.py`, `services.py`, etc.)
- Validate transaction behavior and authorization flow in routers

## 7) PR Checklist

1. Services depend on ports (`Protocol`), not concrete adapters.
1. Concrete implementations stay outside the service layer.
1. Dependency modules compose the object graph.
1. No service instantiation inside services.
1. Unit tests are aligned with contract-level behavior.
