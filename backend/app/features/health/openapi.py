from typing import Any

from fastapi import status

from app.features.health.schemas import ReadinessResponse

HEALTH_DOC: dict[str, Any] = {
    "summary": "Liveness check",
    "description": "Verify that the API process is responding without checking dependencies.",
    "response_description": "Current service status.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Service is available.",
            "content": {"application/json": {"example": {"status": "ok"}}},
        }
    },
}

READINESS_DOC: dict[str, Any] = {
    "summary": "Readiness check",
    "description": "Verify that every registered dependency is available for traffic admission.",
    "response_description": "Neutral dependency readiness status.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "All registered dependencies are available.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "checks": [{"name": "database", "status": "ok"}],
                    }
                }
            },
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "One or more registered dependencies are unavailable.",
            "model": ReadinessResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "unavailable",
                        "checks": [{"name": "database", "status": "unavailable"}],
                    }
                }
            },
        },
    },
}
