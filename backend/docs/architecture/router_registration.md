# Modular Router Auto-Registration

## Central Router Catalog

Router module registration is centralized in `app/core/setup/routers.py`:

- `ROUTER_MODULES`: ordered tuple of fully qualified router module paths to load.
- `ROUTER_ATTRIBUTE`: required attribute name exposed by each module (`router`).
- `API_V1_PREFIX`: API namespace prefix applied to all routers.

`create_app` calls `configure_routers`, and `configure_routers` loads routers dynamically from that catalog.
At registration time, the backend applies the API namespace prefix `/v1` to every router.

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

1. Create a feature router module (for example `app.features.publisher.router`) exposing `router`.
1. Add `"app.features.publisher.router"` to `ROUTER_MODULES` in `app/core/setup/routers.py`.

No changes are needed in `create_app` or `app/core/setup/factory.py`.
The route is exposed as `/v1/publishers` because version prefixing is centralized in router setup.

## Related: OpenAPI docs split

This project keeps route documentation metadata in feature OpenAPI modules, not inside router modules.
See `openapi_documentation.md` for the full pattern.
