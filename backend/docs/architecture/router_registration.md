# Modular Router Auto-Registration

## Central Router Catalog

Router module registration is centralized in `app/routers/__init__.py`:

- `ROUTER_MODULES`: ordered tuple of router module names to load.
- `ROUTER_ATTRIBUTE`: required attribute name exposed by each module (`router`).

`create_app` calls `configure_routers`, and `configure_routers` loads routers dynamically from that catalog.

## Auto-registrable Router Convention

A router module is auto-registrable when:

1. It is listed in `ROUTER_MODULES`.
1. It exposes a FastAPI `APIRouter` instance named `router`.

Minimal example:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/publishers", tags=["publishers"])
```

## Add a New Router

1. Create a module in `app/routers/` (example: `publisher.py`) exposing `router`.
1. Add `"publisher"` to `ROUTER_MODULES` in `app/routers/__init__.py`.

No changes are needed in `create_app` or `app/setup/routers.py`.

## Related: OpenAPI docs split

This project keeps route documentation metadata in `app/openapi/*`, not inside router modules.
See `openapi_documentation.md` for the full pattern.
