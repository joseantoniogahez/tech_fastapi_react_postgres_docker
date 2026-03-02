from typing import Annotated, Any, Optional

from fastapi import Body, Path, Query

from app.common.pagination import DEFAULT_LIST_LIMIT, MAX_LIST_LIMIT
from app.repositories.book import BookSort
from app.schemas.api.book import AddBook, UpdateBook

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
