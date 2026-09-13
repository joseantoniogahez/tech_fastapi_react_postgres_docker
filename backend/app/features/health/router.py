from fastapi import APIRouter, Response, status

from app.core.authorization.dependencies import PublicReadAccessDependency
from app.core.setup.dependencies import ReadinessServiceDependency
from app.features.health.openapi import HEALTH_DOC, READINESS_DOC
from app.features.health.schemas import ReadinessResponse, ReadinessStatus

router = APIRouter(tags=["health"])


@router.get("/health", **HEALTH_DOC)
async def health(_read_access: PublicReadAccessDependency) -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readiness", response_model=ReadinessResponse, **READINESS_DOC)
async def readiness(
    response: Response,
    _read_access: PublicReadAccessDependency,
    readiness_service: ReadinessServiceDependency,
) -> ReadinessResponse:
    result = await readiness_service.evaluate()
    if result.status == ReadinessStatus.UNAVAILABLE:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
