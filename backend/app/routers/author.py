from typing import List

from fastapi import APIRouter

from app.dependencies import AuthorServiceDependency
from app.openapi.authors import GET_AUTHORS_DOC
from app.schemas.author import Author

router = APIRouter(
    prefix="/authors",
    tags=["authors"],
)


@router.get("/", response_model=List[Author], **GET_AUTHORS_DOC)
async def get_authors(author_service: AuthorServiceDependency) -> List[Author]:
    authors = await author_service.get_all()
    return [Author.model_validate(author) for author in authors]
