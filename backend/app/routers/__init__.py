from typing import Final

ROUTER_MODULES: Final[tuple[str, ...]] = (
    "health",
    "auth",
    "book",
    "author",
)

ROUTER_ATTRIBUTE: Final[str] = "router"

__all__ = [
    "ROUTER_MODULES",
    "ROUTER_ATTRIBUTE",
]
