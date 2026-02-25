from typing import Any

from fastapi import status

HEALTH_DOC: dict[str, Any] = {
    "summary": "Health check",
    "description": "Verify that the API is available and responding to requests.",
    "response_description": "Current service status.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Service is available.",
            "content": {"application/json": {"example": {"status": "ok"}}},
        }
    },
}
