# Feature-Based Backend Architecture

## Goal

Use a strict feature-based layout with a small shared core.

Current top-level shape:

- `app/core`
- `app/features`
- `app/integrations`

## Ownership

`app/core` owns cross-feature concerns only:

- config
- database runtime and Unit of Work
- shared authorization primitives
- shared security helpers
- shared error types and handlers
- shared OpenAPI/error helpers
- app factory and router registration

`app/features/<feature>` owns vertical slices:

- router
- feature service
- feature repository
- feature schemas
- feature models
- feature-local OpenAPI metadata

Current features:

- `health`
- `auth`
- `rbac`
- `outbox`

## Dependency direction

Preferred direction:

`feature router -> feature service -> feature repository -> core db/runtime`

Allowed shared imports:

- features may import `app/core/*`
- a feature may import another feature only for explicitly shared records/models that already exist in production flow
- repositories must not depend on router or setup modules

## Practical rules

Routers:

- own HTTP concerns only
- do not build services directly
- do not contain business logic

Services:

- own use-case orchestration
- depend on ports/contracts where useful
- do not depend on FastAPI wiring

Repositories:

- own ORM access and query construction
- translate persistence failures before they cross upward

`__init__.py`:

- package markers and re-exports only
- no runtime logic

## Adding a new feature

When introducing a new vertical slice:

1. Create `app/features/<feature>/`.
1. Add `router.py`, `service.py`, `repository.py`, `schemas/api.py`, `schemas/app.py`.
1. Add `models.py` only if the feature owns persistence tables.
1. Register the router in `app/core/setup/routers.py`.
1. Add tests and docs for the new public surface.

## Anti-patterns

- rebuilding global cross-feature layers that bypass `app/features/<feature>` ownership
- moving feature-specific helpers into `app/core` too early
- putting business logic in dependency providers
- leaving public permissions undocumented
