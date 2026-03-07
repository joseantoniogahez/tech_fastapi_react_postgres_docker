from fastapi import APIRouter

from app.core.authorization.dependencies import PublicReadAccessDependency
from app.features.health.openapi import HEALTH_DOC

router = APIRouter(tags=["health"])


@router.get("/health", **HEALTH_DOC)
async def health(_read_access: PublicReadAccessDependency) -> dict[str, str]:
    return {"status": "ok"}
