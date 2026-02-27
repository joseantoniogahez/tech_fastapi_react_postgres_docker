from typing import Annotated, Any, Optional

from fastapi import Body, Path, Query, status

from app.const.permission import PermissionId
from app.openapi.common import INTERNAL_ERROR_EXAMPLE, build_error_response
from app.repositories import DEFAULT_LIST_LIMIT, MAX_LIST_LIMIT
from app.repositories.book import BookSort
from app.schemas.book import AddBook, UpdateBook

BOOK_EXAMPLE: dict[str, Any] = {
    "id": 1,
    "title": "Foundation",
    "year": 1951,
    "status": "published",
    "author": {
        "id": 1,
        "name": "Isaac Asimov",
    },
}

ADD_BOOK_BODY_EXAMPLES: dict[str, Any] = {
    "with_existing_author": {
        "summary": "Using an existing author_id",
        "value": {
            "title": "I, Robot",
            "year": 1950,
            "status": "published",
            "author_id": 1,
            "author_name": "Isaac Asimov",
        },
    },
    "with_new_author_name": {
        "summary": "Creating or reusing by author name",
        "value": {
            "title": "Neuromancer",
            "year": 1984,
            "status": "published",
            "author_name": "William Gibson",
        },
    },
}

UPDATE_BOOK_BODY_EXAMPLES: dict[str, Any] = {
    "full_update": {
        "summary": "Update all mutable fields",
        "value": {
            "title": "Foundation",
            "year": 1951,
            "status": "published",
            "author_id": 1,
            "author_name": "Isaac Asimov",
        },
    }
}

AuthorIdQuery = Annotated[
    Optional[int],
    Query(
        ge=1,
        description="Filter the list by author ID.",
        examples=[1],
    ),
]

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

BookSortQuery = Annotated[
    BookSort,
    Query(
        description="Sort field. Use `-` prefix for descending order.",
        examples=["id", "-year"],
    ),
]

BookIdPath = Annotated[
    int,
    Path(
        ge=1,
        description="Book ID.",
        examples=[1],
    ),
]

AddBookPayload = Annotated[
    AddBook,
    Body(
        description="Payload to create a book.",
        examples=ADD_BOOK_BODY_EXAMPLES,
    ),
]

UpdateBookPayload = Annotated[
    UpdateBook,
    Body(
        description="Full payload used to update the book.",
        examples=UPDATE_BOOK_BODY_EXAMPLES,
    ),
]

GET_BOOKS_DOC: dict[str, Any] = {
    "summary": "List books",
    "description": (
        "Return the catalog of books. Supports `author_id` filter, pagination via `offset`/`limit`, "
        "and deterministic sorting via `sort`."
    ),
    "response_description": "List of books in the catalog.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Books fetched successfully.",
            "content": {"application/json": {"example": [BOOK_EXAMPLE]}},
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

GET_PUBLISHED_BOOKS_DOC: dict[str, Any] = {
    "summary": "List published books",
    "description": "Return only books with status `published`.",
    "response_description": "List of published books.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Published books fetched successfully.",
            "content": {"application/json": {"example": [BOOK_EXAMPLE]}},
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

GET_BOOK_DOC: dict[str, Any] = {
    "summary": "Get book by ID",
    "description": "Fetch a single book by its ID.",
    "response_description": "Book found.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Book fetched successfully.",
            "content": {"application/json": {"example": BOOK_EXAMPLE}},
        },
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid book ID.",
            example={
                "detail": "Request validation error",
                "status": 400,
                "code": "invalid_input",
                "meta": [{"loc": ["path", "id"], "msg": "Input should be greater than or equal to 1"}],
            },
        ),
        status.HTTP_404_NOT_FOUND: build_error_response(
            description="Book with the requested ID does not exist.",
            example={
                "detail": "Book 999 not found",
                "status": 404,
                "code": "not_found",
                "meta": {"id": 999},
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

ADD_BOOK_DOC: dict[str, Any] = {
    "status_code": status.HTTP_201_CREATED,
    "summary": "Create book",
    "description": (f"Create a new book. Requires authenticated user with `{PermissionId.BOOK_CREATE}` permission."),
    "response_description": "Book created successfully.",
    "responses": {
        status.HTTP_201_CREATED: {
            "description": "Book created.",
            "content": {"application/json": {"example": BOOK_EXAMPLE}},
        },
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid payload.",
            example={
                "detail": "Request validation error",
                "status": 400,
                "code": "invalid_input",
                "meta": [{"loc": ["body", "title"], "msg": "Field required"}],
            },
        ),
        status.HTTP_401_UNAUTHORIZED: build_error_response(
            description="Missing, expired, or invalid token.",
            example={
                "detail": "Could not validate credentials",
                "status": 401,
                "code": "unauthorized",
            },
            include_www_authenticate=True,
        ),
        status.HTTP_403_FORBIDDEN: build_error_response(
            description="User lacks permission to create books.",
            example={
                "detail": f"Missing required permission: {PermissionId.BOOK_CREATE}",
                "status": 403,
                "code": "forbidden",
                "meta": {"permission_id": PermissionId.BOOK_CREATE},
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

UPDATE_BOOK_DOC: dict[str, Any] = {
    "summary": "Update book",
    "description": (
        f"Update a book by ID. Requires `{PermissionId.BOOK_UPDATE}` permission. "
        "Returns `404` when the book does not exist."
    ),
    "response_description": "Updated book.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Book updated.",
            "content": {"application/json": {"example": BOOK_EXAMPLE}},
        },
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid ID or payload.",
            example={
                "detail": "Request validation error",
                "status": 400,
                "code": "invalid_input",
                "meta": [{"loc": ["path", "id"], "msg": "Input should be greater than or equal to 1"}],
            },
        ),
        status.HTTP_404_NOT_FOUND: build_error_response(
            description="Book with the requested ID does not exist.",
            example={
                "detail": "Book 999 not found",
                "status": 404,
                "code": "not_found",
                "meta": {"id": 999},
            },
        ),
        status.HTTP_401_UNAUTHORIZED: build_error_response(
            description="Missing, expired, or invalid token.",
            example={
                "detail": "Could not validate credentials",
                "status": 401,
                "code": "unauthorized",
            },
            include_www_authenticate=True,
        ),
        status.HTTP_403_FORBIDDEN: build_error_response(
            description="User lacks permission to update books.",
            example={
                "detail": f"Missing required permission: {PermissionId.BOOK_UPDATE}",
                "status": 403,
                "code": "forbidden",
                "meta": {"permission_id": PermissionId.BOOK_UPDATE},
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

DELETE_BOOK_DOC: dict[str, Any] = {
    "status_code": status.HTTP_204_NO_CONTENT,
    "summary": "Delete book",
    "description": (
        f"Delete a book by ID. Requires `{PermissionId.BOOK_DELETE}` permission. "
        "Deletion is idempotent: missing IDs are treated as no-op."
    ),
    "response_description": "Book deletion completed with no response body.",
    "responses": {
        status.HTTP_204_NO_CONTENT: {
            "description": "Book deleted (or no-op if it does not exist).",
        },
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid book ID.",
            example={
                "detail": "Request validation error",
                "status": 400,
                "code": "invalid_input",
                "meta": [{"loc": ["path", "id"], "msg": "Input should be greater than or equal to 1"}],
            },
        ),
        status.HTTP_401_UNAUTHORIZED: build_error_response(
            description="Missing, expired, or invalid token.",
            example={
                "detail": "Could not validate credentials",
                "status": 401,
                "code": "unauthorized",
            },
            include_www_authenticate=True,
        ),
        status.HTTP_403_FORBIDDEN: build_error_response(
            description="User lacks permission to delete books.",
            example={
                "detail": f"Missing required permission: {PermissionId.BOOK_DELETE}",
                "status": 403,
                "code": "forbidden",
                "meta": {"permission_id": PermissionId.BOOK_DELETE},
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}
