# Modular Router Auto-Registration

## Central Router Catalog

The central module list is defined in `app/routers/__init__.py`:

- `ROUTER_MODULES`: ordered list of router modules to auto-load.
- `ROUTER_ATTRIBUTE`: required attribute name (default: `router`).

`create_app` already calls `configure_routers`, and `configure_routers` now loads modules dynamically from that catalog.

## Minimal Convention for Auto-Registrable Router Modules

A module is auto-registrable when:

1. It is listed in `ROUTER_MODULES`.
2. It exposes an `APIRouter` instance named `router`.

Example:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/publishers", tags=["publishers"])
```

## Add a New Domain Router with Zero Friction

1. Create a module in `app/routers/` (e.g. `publisher.py`) exposing `router`.
2. Add `"publisher"` to `ROUTER_MODULES` in `app/routers/__init__.py`.

No changes are needed in `create_app` or `setup/routers.py`.
