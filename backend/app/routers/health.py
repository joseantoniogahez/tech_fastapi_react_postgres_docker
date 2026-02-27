from fastapi import APIRouter

from app.dependencies.authorization import PublicReadAccessDependency
from app.openapi.health import HEALTH_DOC

router = APIRouter(tags=["health"])


@router.get("/health", **HEALTH_DOC)
async def health(_read_access: PublicReadAccessDependency) -> dict[str, str]:
    return {"status": "ok"}
