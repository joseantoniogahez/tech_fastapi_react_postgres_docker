# Clean Architecture: Ports, Adapters, and Incremental Layered Target

This guide defines the backend target architecture for the next refactors.

The near-term target is still a layered backend, not a feature-based layout. The goal is to make the current structure stricter and more predictable before considering any `app/features/*` migration.

This backend already applies:

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

## 2) Incremental Target Architecture (Still Layered)

The package shape can stay close to the current one while boundaries become stricter:

- Delivery layer:
  - `app/routers/*`
  - `app/openapi/*`
- Composition layer:
  - `app/dependencies/*`
  - `app/setup/*`
  - `app/factory.py`
- Application layer:
  - `app/services/*`
  - service ports defined with `Protocol`
- Infrastructure / persistence layer:
  - `app/repositories/*`
  - `app/database.py` and related DB wiring until it is moved later
- Data definitions:
  - `app/models/*`
  - `app/schemas/*`
- Cross-cutting rules and errors:
  - `app/exceptions/*`
  - neutral shared modules outside `repositories` when cross-layer constants/helpers are extracted

Short-term architectural intent:

1. Preserve the layered layout that already exists.
1. Tighten import direction and ownership inside the existing folders.
1. Move shared cross-layer utilities out of persistence-specific modules.
1. Reduce `__init__.py` files to package surface and re-exports only.
1. Reevaluate a feature-based structure only after these boundaries are clean.

## 3) Import Direction Rules

Use these rules as the default dependency direction:

- `routers` may depend on:
  - `dependencies`
  - `schemas`
  - `openapi`
  - FastAPI/framework primitives
  - service contracts exposed through dependency aliases
- `routers` must not depend on:
  - concrete repositories
  - direct SQLAlchemy session handling
  - persistence-only constants exported from `repositories`
- `services` may depend on:
  - service/repository ports (`Protocol`)
  - domain/application exceptions
  - neutral shared modules (`const`, future common modules, validators, policy helpers)
- `services` must not depend on:
  - SQLAlchemy exception types
  - concrete repository implementations
  - request/response framework wiring
- `repositories` may depend on:
  - SQLAlchemy
  - models
  - repository/infrastructure exceptions
  - neutral shared modules
- `repositories` must not be used as a shared base module for unrelated layers.
- `__init__.py` files may depend on:
  - imports required for re-exports only
- `__init__.py` files must not contain:
  - core business logic
  - persistence logic
  - transaction behavior
  - shared constants that other layers import as primary source

Preferred direction:

`routers -> dependencies -> services (ports/contracts) -> repositories -> database`

Cross-cutting modules such as `exceptions`, neutral constants, or policy helpers may be imported inward by the layers that own them, but they should not invert the main flow by making `repositories` the default shared source for non-persistence concerns.

## 4) Ownership Rules by Layer

### Routers own HTTP concerns only

Routers are responsible for:

- request parsing
- dependency injection
- auth dependency composition
- response status codes
- mapping service results to API responses
- attaching OpenAPI metadata

Routers must stay thin.

Explicit rule: routers must not contain business logic. If a router needs branching beyond HTTP validation/response translation, move that behavior into a service or a dedicated policy/helper owned by the application layer.

### Services own use-case orchestration

Services are responsible for:

- use-case orchestration
- business rules
- validation that belongs to the application/domain layer
- transaction boundaries through `UnitOfWorkPort`
- translating repository outcomes into domain/application exceptions

Explicit rule: services must not depend on SQLAlchemy exceptions. Database-specific exceptions must be translated before they cross into the service layer, typically inside repositories or through repository-specific infrastructure exceptions.

### Repositories own persistence concerns

Repositories are responsible for:

- ORM access
- query construction
- DB writes/reads
- translating SQLAlchemy-specific failures into repository/infrastructure exceptions

Explicit rule: repositories must not export shared constants for the rest of the application as if they were a common module. If a constant is reused by routers, services, OpenAPI helpers, and repositories, it belongs in a neutral shared module, not in `app.repositories`.

### `__init__.py` owns package surface only

`__init__.py` files are responsible for:

- package markers
- narrow re-exports
- compatibility imports during a transition window

Explicit rule: `__init__.py` must not contain principal logic. Real implementations should live in dedicated modules with explicit names (`base.py`, `uow.py`, `models/base.py`, etc.), while `__init__.py` only exposes a stable package surface if needed.

## 5) Day-to-Day Use

Operational rules:

1. In services, type dependencies as ports, not concrete classes.
1. Do not instantiate services inside other services.
1. Keep composition and wiring in dependency modules (`db.py`, `repositories.py`, `services.py`, etc.).
1. Keep transaction boundaries at use-case level with `async with unit_of_work`.
1. When a concern is shared across layers, place it in a neutral module rather than in `repositories`.

Real example:

- `BookService` depends on `BookRepositoryPort`, `AuthorServicePort`, and `UnitOfWorkPort`.
- `BookService` does not create `AuthorService`; `get_books_service` injects it.

## 6) Safe Change Order

When changing an existing use case:

1. Update the port first (method signatures in `Protocol`).
1. Update concrete implementation(s) to satisfy the contract.
1. If infrastructure-specific errors are involved, translate them before the service boundary.
1. Wire the change in dependency composition modules (`app/dependencies/*.py`).
1. Update unit tests to mock the updated port methods.
1. Run service tests first, then router/integration tests.

Recommended order: contract -> adapter -> boundary translation -> composition -> tests.

## 7) How to Extend with a New Module

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

## 8) Anti-patterns to Avoid

1. Importing concrete repositories in services just for typing.
1. Instantiating one service inside another (`SomeService()` in `OtherService`).
1. Moving business logic to routers or providers.
1. Catching `IntegrityError` or other SQLAlchemy exceptions in services.
1. Using `app.repositories` as the source of shared constants for routers, services, or OpenAPI modules.
1. Keeping base classes, unit-of-work implementations, or shared runtime behavior inside `__init__.py`.
1. Skipping `UnitOfWork` for write use cases.

## 9) Recommended Testing Strategy

### Service unit tests

- Mock ports (`MagicMock` / `AsyncMock`)
- Assert behavior through contract methods
- Validate application-level exception translation, not SQLAlchemy internals

### Integration tests

- Validate real composition in dependency modules (`db.py`, `repositories.py`, `services.py`, etc.)
- Validate transaction behavior and authorization flow in routers
- Cover repository-side translation when infrastructure exceptions are expected

## 10) Refactor Checklist for the Next Steps

Use this checklist before considering a refactor complete:

1. Routers only handle HTTP concerns and contain no business logic.
1. Routers do not import concrete repositories or persistence-only constants.
1. Services depend on ports/contracts, not concrete adapters.
1. Services do not import or catch SQLAlchemy exception types.
1. Repositories own SQLAlchemy interaction and translate persistence failures before they reach services.
1. Repositories do not export shared cross-layer constants as a public common API.
1. Shared constants or validators used by multiple layers live in a neutral module.
1. `__init__.py` files are limited to package markers and re-exports.
1. `UnitOfWork`, base classes, and similar runtime behavior live in explicit modules, not in `__init__.py`.
1. Dependency modules remain the only place where concrete wiring is assembled.
1. The layered structure is preserved until these rules are consistently enforced.
