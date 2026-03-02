from typing import List

from fastapi import APIRouter

from app.common.pagination import DEFAULT_LIST_LIMIT
from app.dependencies.authorization import PublicReadAccessDependency
from app.dependencies.services import AuthorServiceDependency
from app.openapi.authors import GET_AUTHORS_DOC, AuthorSortQuery, LimitQuery, OffsetQuery
from app.schemas.api.author import Author

router = APIRouter(
    prefix="/authors",
    tags=["authors"],
)


@router.get("/", response_model=List[Author], **GET_AUTHORS_DOC)
async def get_authors(
    author_service: AuthorServiceDependency,
    _read_access: PublicReadAccessDependency,
    offset: OffsetQuery = 0,
    limit: LimitQuery = DEFAULT_LIST_LIMIT,
    sort: AuthorSortQuery = "name",
) -> List[Author]:
    authors = await author_service.get_all(offset=offset, limit=limit, sort=sort)
    return [Author.model_validate(author) for author in authors]
