from typing import Final

ROUTER_MODULES: Final[tuple[str, ...]] = (
    "health",
    "auth",
    "book",
    "author",
    "rbac",
)

ROUTER_ATTRIBUTE: Final[str] = "router"
