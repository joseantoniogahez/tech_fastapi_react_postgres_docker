from typing import Annotated, Any

from fastapi import Query, status

from app.openapi.common import INTERNAL_ERROR_EXAMPLE, build_error_response
from app.repositories import DEFAULT_LIST_LIMIT, MAX_LIST_LIMIT
from app.repositories.author import AuthorSort

OffsetQuery = Annotated[
    int,
    Query(
        ge=0,
        description="Zero-based index of the first item to return.",
        examples=[0],
    ),
]

LimitQuery = Annotated[
    int,
    Query(
        ge=1,
        le=MAX_LIST_LIMIT,
        description=f"Maximum number of items to return. Must be between 1 and {MAX_LIST_LIMIT}.",
        examples=[DEFAULT_LIST_LIMIT],
    ),
]

AuthorSortQuery = Annotated[
    AuthorSort,
    Query(
        description=(
            "Sort field (`name`, `-name`, `id`, `-id`). Use `-` prefix for descending order. Default: `name`."
        ),
        examples=["name", "-name"],
    ),
]

GET_AUTHORS_DOC: dict[str, Any] = {
    "summary": "List authors",
    "description": (
        "Return authors in the catalog. Supports pagination via `offset`/`limit` "
        "and deterministic sorting via `sort` (default `name` ascending)."
    ),
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
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid query parameters.",
            example={
                "detail": "Request validation error",
                "status": 400,
                "code": "invalid_input",
                "meta": [{"loc": ["query", "limit"], "msg": f"Input should be less than or equal to {MAX_LIST_LIMIT}"}],
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}
