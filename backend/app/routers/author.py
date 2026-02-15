from typing import List

from fastapi import APIRouter

from app.dependencies import AuthorServiceDependency
from app.schemas.author import Author

router = APIRouter(
    prefix="/authors",
    tags=["authors"],
)


@router.get("/")
async def get_authors(author_service: AuthorServiceDependency) -> List[Author]:
    authors = await author_service.get_all()
    return [Author.model_validate(author) for author in authors]
