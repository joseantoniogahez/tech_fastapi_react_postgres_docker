from fastapi import APIRouter

from app.openapi.health import HEALTH_DOC

router = APIRouter(tags=["health"])


@router.get("/health", **HEALTH_DOC)
async def health() -> dict[str, str]:
    return {"status": "ok"}
