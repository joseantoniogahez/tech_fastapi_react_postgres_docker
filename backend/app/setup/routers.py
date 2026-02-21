from importlib import import_module

from fastapi import APIRouter, FastAPI

from app.routers import ROUTER_ATTRIBUTE, ROUTER_MODULES


def _resolve_router_module_path(module_name: str) -> str:
    if module_name.startswith("app."):
        return module_name
    return f"app.routers.{module_name}"


def _load_router(module_name: str) -> APIRouter:
    module_path = _resolve_router_module_path(module_name)
    module = import_module(module_path)
    router = getattr(module, ROUTER_ATTRIBUTE, None)
    if not isinstance(router, APIRouter):
        raise RuntimeError(f"Router module '{module_path}' must expose an APIRouter named '{ROUTER_ATTRIBUTE}'")
    return router


def get_registered_routers() -> list[APIRouter]:
    return [_load_router(module_name) for module_name in ROUTER_MODULES]


def configure_routers(app: FastAPI) -> None:
    for router in get_registered_routers():
        app.include_router(router)
