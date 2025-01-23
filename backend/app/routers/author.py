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
    return await author_service.get_all()
