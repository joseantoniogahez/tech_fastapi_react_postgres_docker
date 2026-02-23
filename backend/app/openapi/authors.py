from typing import Any

from fastapi import status

from app.openapi.common import INTERNAL_ERROR_EXAMPLE, build_error_response

GET_AUTHORS_DOC: dict[str, Any] = {
    "summary": "List authors",
    "description": "Return all authors in the catalog ordered by name.",
    "response_description": "List of available authors.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Authors fetched successfully.",
            "content": {
                "application/json": {
                    "example": [
                        {"id": 1, "name": "Isaac Asimov"},
                        {"id": 2, "name": "William Gibson"},
                    ]
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

__all__ = ["GET_AUTHORS_DOC"]
